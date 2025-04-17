from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from config import config

# DB
from llm_api.Models.database import get_db
from llm_api.Services.get_db_host_instance_db_service import get_metrics_host_instance_db
from llm_api.Services.get_db_service_service import get_metrics_service, get_metrics_names_service
from llm_api.Services.get_redis_data_service import get_redis_metric_datas
from llm_api.Utils.data_utils import is_anomaly_metric

# Prompt
from llm_api.Prompts.model_prompt import gdn_explanation_prompt
from llm_api.Prompts.system_prompt import rule_prompt, pre_base_prompt, input_explanation_prompt
from llm_api.Prompts.metrics_prompt import metrics_definition_prompt
from llm_api.Prompts.output_format_prompt import os_output_format_prompt, was_output_format_prompt, \
    service_output_format_prompt
from llm_api.Prompts.make_input_data_prompt import generate_service_input_prompt, generate_os_was_input_prompt, \
    generate_metrics_definition_prompt
from llm_api.Prompts.fewshot_prompt import few_shot_prompt

# Logger
from llm_api.Utils.logger import llm_logger


class PromptLoaderService:
    class OSnWASJson(BaseModel):
        inst_type: str = Field(description="Type of instance")
        target_id: str = Field(description="Target ID")
        situation: str = Field(description="situation analysis")
        issue: str = Field(
            description="Use a bulleted description with a generic event name to list the events that might be causing the anomaly and a detailed description.")
        solution: str = Field(
            description="In the solution, use bullet points to list clear ways to resolve the anomaly.")
        etc: str = Field(description="Other views of the current situation")

    def __init__(self):
        self.parser = JsonOutputParser(pydantic_object=self.OSnWASJson)
        self._tmp_prompt = \
            pre_base_prompt + \
            rule_prompt + \
            input_explanation_prompt
        # gdn_explanation_prompt + \
        # input_explanation_prompt
        # service_input + \
        # os_was_input + \
        # few_shot_prompt
        self._qwen_model_prompt = """\n\n{format_instructions}\n\n※ Data delivered to you\n{input_data}\n{few_shot_learning}"""
        self._else_model_prompt = """\n\n※ Output Format\n{{'inst_type': 'your answer',"target_id": "your answer","situation": "your answer","issues": "your answer","solutions": "your answer"}}\n\n※ Data delivered to you\n{input_data}"""

    def load_base_prompt(self):
        try:
            llm_logger.info("기본 프롬프트 템플릿 로딩 시작")
            if config.model_name == "qwen2.5:14b-instruct-q8_0":
                llm_logger.info("Qwen 모델에 맞는 프롬프트 생성")
                return PromptTemplate(
                    template=self._tmp_prompt + self._qwen_model_prompt,
                    input_variables=["metrics_definition", "input_data"],
                    partial_variables={"format_instructions": self.parser.get_format_instructions()}
                )
            else:
                llm_logger.info("기타 모델용 프롬프트 생성")
                return PromptTemplate(
                    template=self._tmp_prompt + self._else_model_prompt,
                    input_variables=["metrics_definition", "input_data"]
                )
        except (ImportError, AttributeError) as e:
            llm_logger.exception("기본 프롬프트 로딩 중 오류 발생")
            return None

    @staticmethod
    def _make_os_was_db_prompt(request_data: dict):
        try:
            llm_logger.info("[OS/WAS/DB] 입력 데이터 프롬프트 생성 시작")
            # Input Data 정리
            # time = request_data["time"]
            time = request_data['summary']['time']
            # inst_type = request_data["tiers"][0]["type"]
            inst_type = request_data['summary']['tiers'][0]['type']
            # target_id = request_data["tiers"][0]["instances"][0]["target_id"]
            target_id = request_data['summary']['tiers'][0]['instances'][0]['target_id']

            ### DB에서 사용된 지표 가져오기
            with get_db() as session:
                all_metrics_values = get_metrics_host_instance_db(session, time, target_id, inst_type)

            ### Redis에서 해당 시점의 Average +- 2Sigma를 벗어난 값들만 가져오기 (일단 제외)
            ### Metrics Definition 가져오기
            anomaly_metrics = {}
            metrics_definition = {}
            for metric, real_value in all_metrics_values:
                lower, upper, avg, std = get_redis_metric_datas(time, metric, inst_type, target_id)
                # if is_anomaly_metric(avg, std, real_value):
                #     anomaly_metrics[metric] = [lower, upper, avg, real_value]
                #     metrics_definition[metric] = metrics_definition_prompt[metric]
                anomaly_metrics[metric] = [lower, upper, avg, real_value]
                metrics_definition[metric] = metrics_definition_prompt[metric]

            ### Prompt 생성
            input_data = generate_os_was_input_prompt(time, target_id, inst_type, anomaly_metrics)
            metrics_definition = generate_metrics_definition_prompt(metrics_definition)
            few_shot_learning = """

    ※ Please refer to the following when answering.
    First Example
    {
        "inst_type": "host",
        "target_id": "ebmciapos07",
        "situation": "rx_errors_delta 지표가 급격히 증가하고 있으며, tx_errors_delta 지표 또한 상승하고 있습니다. 반면, 네트워크 트래픽 자체는 일정한 수준을 유지하고 있습니다. 
        이러한 지표의 움직임으로 볼 때 현재 시스템의 네트워크 환경에서 패킷 오류가 증가하고 있으며, 데이터 손실이 발생할 가능성이 있습니다.",
        "issue": "네트워크 패킷 오류가 증가하면서 서비스 응답 지연이나 데이터 유실이 발생할 위험이 높아지고 있습니다.",
        "solution": "네트워크 인터페이스와 관련된 로그를 확인하고, 오류 발생 원인을 분석해야 합니다. 필요하다면 네트워크 장비 점검 및 설정 조정을 진행할 수 있습니다.",
        "group": "MCI",
        "etc": ""
    }

    Second Example
    {
        "inst_type": "host",
        "target_id": "ebeaiapos01",
        "situation": "rx_bytes_delta 지표가 급격히 증가하고 있으며, tx_bytes_delta 지표 또한 큰 폭으로 상승하고 있습니다. 반면, network 지표는 과거 대비 높은 수준에서 유지되고 있습니다. 
        이러한 지표의 움직임으로 볼 때 현재 시스템은 네트워크 부하가 증가하고 있으며, 과부하가 발생할 가능성이 있습니다.",
        "issue": "네트워크 트래픽이 증가하면서 향후 호스트의 네트워크 부하가 증가할 것으로 예상됩니다. 트래픽 폭주 시 패킷 손실이나 응답 지연이 발생할 수 있습니다.",
        "solution": "네트워크 트래픽이 급증한 원인을 분석하고 불필요한 데이터 송수신이 있는지 점검해야 합니다. 필요 시 QoS 정책을 적용하여 네트워크 부하를 분산하는 방안을 고려할 수 있습니다.",
        "group": "EAI",
        "etc": ""
    }

    Third Example
    {
        "inst_type": "host",
        "target_id": "ebfepapos06",
        "situation": "cpu_usage 지표가 지속적으로 상승하고 있으며, cpu_system 지표 또한 점진적으로 증가하는 양상을 보이고 있습니다. 반면, cpu_idle 지표는 점차 감소하고 있습니다. 이러한 지표의 움직임으로 볼 때 현재 시스템은 CPU 사용률이 점점 증가하면서 부하가 높아지고 있는 상태입니다. 현재 수준에서는 즉각적인 조치가 필요하지 않지만, 지속적인 증가가 감지될 경우 추가적인 모니터링이 요구됩니다.",
        "issue": "현재 CPU 사용량이 증가하고 있어, 향후 호스트의 CPU 부하가 증가할 가능성이 큽니다. 지속적인 부하가 발생하면 프로세스 처리 속도가 저하될 수 있습니다.",
        "solution": "과부하를 유발하는 프로세스를 점검하고, 필요하다면 불필요한 작업을 종료하여 CPU 부하를 완화해야 합니다. 장기적으로는 CPU 리소스를 확장하는 방안을 고려할 수 있습니다.",
        "group": "FEP",
        "etc": ""
    }
    """

            llm_logger.debug(f"[OS/WAS/DB] 생성된 input_data: {input_data}")
            return {"input_data": input_data,
                    "metrics_definition": metrics_definition}  # , "few_shot_learning": few_shot_learning}

        except Exception as e:
            llm_logger.exception("[OS/WAS/DB] 입력 프롬프트 생성 중 오류 발생 ")
            return {}

    @staticmethod
    def _make_service_prompt(request_data: dict):
        try:
            llm_logger.info("[Service] 입력 데이터 프롬프트 생성 시작")
            # Input Data 정리
            time = request_data["time"]
            inst_type = "service"
            tx_code = list(request_data["tx_codes"].keys())[0]
            tx_code_name = request_data["tx_codes"][tx_code]["name"]

            ### DB에서 사용된 지표 가져오기 -> DBSLNResultServicePerformance
            with get_db() as session:
                all_metrics_values = get_metrics_service(session, time, tx_code)

            ### Redis에서 해당 시점의 Average +- 2Sigma를 벗어난 값들만 가져오기 (일단 제외)
            ### Metrics Definition 가져오기
            anomaly_metrics = {}
            metrics_definition = {}
            for metric, real_value in all_metrics_values:
                lower, upper, avg, std = get_redis_metric_datas(time, metric, inst_type, tx_code)
                # if is_anomaly_metric(avg, std, real_value):
                #     anomaly_metrics[metric] = [lower, upper, avg, real_value]
                #     metrics_definition[metric] = metrics_definition_prompt[metric]
                anomaly_metrics[metric] = [lower, upper, avg, real_value]
                metrics_definition[metric] = metrics_definition_prompt[metric]

            ### 지표 이름을 desc로 매핑 -> XaiopsMetaMetric
            with get_db() as session:
                metric_name_mapping = get_metrics_names_service(session, list(anomaly_metrics.keys()))
            mapped_anomaly_metrics = {metric_name_mapping.get(k, k): v for k, v in anomaly_metrics.items()}
            mapped_metrics_definition = {metric_name_mapping.get(k, k): v for k, v in metrics_definition.items()}

            ### Prompt 생성
            input_prompt = generate_service_input_prompt(time, tx_code_name, inst_type, mapped_anomaly_metrics)
            metrics_definition = generate_metrics_definition_prompt(mapped_metrics_definition)
            llm_logger.debug(f"[Service] 생성된 input_data: {input_prompt}")

            return {"input_data": input_prompt, "metrics_definition": metrics_definition}

        except Exception as e:
            llm_logger.exception("[Service] 입력 프롬프트 생성 중 오류 발생 ")
            return {}

    @staticmethod
    def make_input_prompt(request_data: dict):
        category_inst_type = request_data["category_inst_type"]
        llm_logger.info(f"프롬프트 타입 판단 - 인스턴스 유형: {category_inst_type}")

        try:
            if category_inst_type == "host_instance_db":
                print("host_instance_db")
                return PromptLoaderService._make_os_was_db_prompt(request_data)
            elif category_inst_type == "service":
                print("was")
                return PromptLoaderService._make_service_prompt(request_data)
            else:
                llm_logger.warning(f"지원하지 않는 인스턴스 유형: {category_inst_type}")
                return None
        except Exception as e:
            llm_logger.exception("프롬프트 분기 처리 중 오류 발생")
            return None


if __name__ == "__main__":
    prompt_loader = PromptLoaderService()

    prompt = prompt_loader.load_base_prompt()
    import json

    prompt_loader._make_service_prompt(json.loads("""{
    "success": true,
    "message": null,
    "total": 0,
    "data": {
        "time": "2025-03-10 20:13:00",
        "anomaly": true,
        "tx_codes": {
            "8": {
                "name": "카드 생성(ME)",
                "performance": {
                    "lower": 0.0,
                    "upper": 79.41,
                    "elapse_avg": 12381.74,
                    "exec_count": 151.0
                },
                "anomaly": [
                    {
                        "name": "elapse_avg",
                        "target_id": "8",
                        "tx_code_name": "카드 생성(ME)",
                        "metric_desc": "E2E 전체 구간 수행 시간(평균)",
                        "value": 12381.74,
                        "lower": 0.0,
                        "upper": 79.41,
                        "failure": true,
                        "unit": "ms"
                    },
                    {
                        "name": "elapse08_avg",
                        "target_id": "8",
                        "tx_code_name": "카드 생성(ME)",
                        "metric_desc": "EAI 수행 시간(평균)",
                        "value": 176.46,
                        "lower": 0.0,
                        "upper": 8.54,
                        "failure": false,
                        "unit": "ms"
                    }
                ]
            }
        },
    "tiers": []
    }
}"""))
    print("test")

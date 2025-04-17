import asyncio
import time

from langchain_ollama import OllamaLLM
from config import config

from llm_api.Services.prompt_loader_service import PromptLoaderService

from llm_api.Utils.logger import llm_logger


class LLMModel:
    """
    LLM 모델을 싱글톤으로 관리하는 클래스
    """
    _instance = None

    def __new__(cls):
        """
        싱글톤 패턴 적용: 인스턴스가 없으면 생성, 있으면 기존 인스턴스 반환
        """
        if cls._instance is None:
            cls._instance = super(LLMModel, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """
        Ollama 기반의 LLM 모델 초기화
        """
        llm_logger.info("LLM 모델 초기화 시작...")
        # self.system_prompt = "마크다운으로 가시성 좋게 간략히 설명해주세요."
        self.llm = OllamaLLM(
            model=config.model_name,
            temperature=config.temperature,
            base_url=config.llm_base_url,
            format= "json"
        )
        prompt_loader = PromptLoaderService()
        self.prompt = prompt_loader.load_base_prompt()
        self.parser = prompt_loader.parser
        self._make_chain()
        llm_logger.info("LLM 모델 초기화 완료.")

    def _make_chain(self):
        self.chain = self.prompt | self.llm | self.parser

    def generate_response(self, input_prompts: dict):
        """
        주어진 입력을 기반으로 LLM 응답 생성
        """
        llm_logger.info("LLM 응답 생성 시작")
        llm_logger.debug(f"Input Prompt: {input_prompts}")

        start_time = time.time()
        response = None
        try:
            response = self.chain.invoke({
                "input_data": input_prompts.get("input_data", ""),
                "metrics_definition": input_prompts.get("metrics_definition", ""),
                "few_shot_learning": input_prompts.get("few_shot_learning", ""),
            })

            end_time = time.time()
            elapsed_time = end_time - start_time

            llm_logger.info(f"LLM 응답 생성 완료 - 소요 시간: {elapsed_time:.2f} seconds.")
            llm_logger.debug(f"LLM 응답 결과: {response}")
        except Exception as e:
            llm_logger.exception("LLM 응답 생성 중 오류 발생")

        return response


# 싱글톤 인스턴스 생성
llm_model = LLMModel()

# 테스트 실행
if __name__ == "__main__":
    async def main():
        user_input = """1. Time of anomaly: 2024-12-06 14:30
2. Target Name: dev_ai-server
3. Instance type of anomaly: os
4. Anomalous metrics:
 4.1. cpu_usage_max: The percentage contributing to the anomaly is 9.2, and the actual value is 1.0. 
 4.2. cpu_user: The percentage contributing to the anomaly is 9.1, and the actual value is 0.0.
 4.3. swap_used: The percentage contributing to the anomaly is 8.8, and the actual value is 179.4218.
 4.4. cpu_usage: The percentage contributing to the anomaly is 8.4, and the actual value is 0.75.
 4.5. cpu_system: The percentage contributing to the anomaly is 8.2, and the actual value is 0.75."""
        response = llm_model.generate_response(user_input)
        print(response)

    asyncio.run(main())

import redis
import json
import time

from config import config

from llm_api.Services.model_loader_service import llm_model
from llm_api.Services.prompt_loader_service import PromptLoaderService

from llm_api.Utils.logger import consumer_logger

# Redis 설정
redis_client = redis.Redis(host=config.SAVE_REDIS_HOST, port=config.SAVE_REDIS_PORT, decode_responses=True)

# LLM Worker 실행
def llm_worker():
    consumer_logger.info("Consumer Start")
    while True:
        # 큐에서 데이터 가져오기 (FIFO 방식)
        request = redis_client.blpop(config.QUEUE_KEY, timeout=5)
        if request is None:
            print("⏳ 큐가 비어 있습니다. 다음 루프를 실행합니다.")
            continue

        _, request_json = request
        consumer_logger.info("요청 데이터 수신")

        try:
            request_data = json.loads(request_json)
            consumer_logger.info(f"요청 데이터: {request_data}")
        except Exception as e:
            consumer_logger.exception(f"요청 데이터 파싱 오류 발생: {e}")
            continue

        # (OS, WAS), (SERVICE) 에 따른 redis key값 생성
        try:
            if request_data['category_inst_type'] == "host_instance_db":
                redis_key = f"{request_data['summary']['time']}_tiers_{request_data['summary']['tiers'][0]['type']}_{request_data['summary']['tiers'][0]['instances'][0]['target_id']}"
            elif request_data['category_inst_type'] == "service":
                tmp_tx_code = list(request_data["tx_codes"].keys())[0]
                redis_key = f"{request_data['time']}_tx_codes_{tmp_tx_code}"
            else:
                redis_key = None
                raise ValueError("지원되지 않는 형식의 데이터가 들어왔습니다.")
            consumer_logger.info(f"{request_data['category_inst_type']}의 Redis Key 생성 완료: {redis_key}")
        except Exception as e:
            consumer_logger.exception(f"Redis Key 생성 실패: {e}")
            continue

        try:
            # LLM 프롬프트 생성
            prompt_start_time = time.time()
            input_prompt = PromptLoaderService.make_input_prompt(request_data)
            prompt_end_time = time.time()
            consumer_logger.info(f"Prompt 생성 완료, 생성 소요 시간: {prompt_end_time - prompt_start_time:.2f} seconds.")
            consumer_logger.debug(f"Prompt 내용: {input_prompt}")

            # Ollama 호출
            response_start_time = time.time()
            response = llm_model.generate_response(input_prompt)
            response_end_time = time.time()
            consumer_logger.info(f"※ LLM 응답 생성 완료, 생성 소요 시간 ※ : {response_end_time - response_start_time:.2f} seconds."
                                 f"\n {response}")

            # Instance_name, Group, request 정보 추가하기
            if request_data["category_inst_type"] == "host_instance_db":
                response["instance_name"] = request_data["summary"]["tiers"][0]["instances"][0]["instance_name"]
                response["group"] = request_data["summary"]["tiers"][0]["name"]
                response["obj"] = request_data["summary"]["tiers"][0]
            elif request_data["category_inst_type"] == "service":
                response["instance_name"] = None
                response["group"] = None
                response["obj"] = request_data["tx_codes"][tmp_tx_code]
            else:
                response = None

            # Redis에 결과 저장 (성공)
            redis_client.hset(redis_key, mapping={"status": "success", "response": json.dumps(response)})
            consumer_logger.info(f"LLM 응답을 Redis에 저장 완료: {redis_key}")
        except Exception as e:
            consumer_logger.exception(f"LLM 답변 생성 중 예외 발생: {e}")
            redis_client.hset(redis_key, mapping={"status": "failed", "response": str(e)})

        time.sleep(1)  # 부하 방지를 위해 1초 대기
    consumer_logger.info("Consumer End")


if __name__ == "__main__":
    llm_worker()

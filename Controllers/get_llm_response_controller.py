import asyncio
import json
import redis.asyncio as redis

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Union

from config import config
from llm_api.Utils.logger import init_logger

# DTO
from llm_api.Dto.host_instance_db_request_dto import HostInstanceDBRequestDTO
from llm_api.Dto.service_request_dto import ServiceDataDTO

# Logger
from llm_api.Utils.logger import api_logger

llm_router = APIRouter()
redis_client = redis.Redis(host=config.SAVE_REDIS_HOST, port=config.SAVE_REDIS_PORT, decode_responses=True)
############################################

@llm_router.get('/answer/{timestamp}', tags=['test'], summary="해당 API는 테스트 목적으로 작성되었습니다.")
async def get_llm_response(request_data: Dict) -> List[Dict[str, str]]:
    response_data = []

    # 요청 데이터에서 필요한 부분 추출
    data = request_data.get("data", {})

    # 1️⃣ 트랜잭션 코드(tx_codes) 기반 이상 탐지 분석
    tx_codes = data.get("tx_codes", {})
    for tx_code, details in tx_codes.items():
        tx_name = details.get("name", None)
        anomalies = details.get("anomaly", [])

        for anomaly in anomalies:
            anomaly_name = anomaly.get("name", None)
            metric_desc = anomaly.get("metric_desc", None)
            value = anomaly.get("value", 0)
            lower = anomaly.get("lower", 0)
            upper = anomaly.get("upper", 0)
            failure = anomaly.get("failure", False)
            target_id = anomaly.get("target_id", None)

            # LLM 분석 응답 생성 (테스트용 메시지 포함)
            llm_answer = f"""
    -----------TEST-----------
    트랜잭션 코드: {tx_name}, 대상 ID: {target_id}, 메트릭 설명: {metric_desc}
    값: {value}ms (정상 범위 {lower} ~ {upper}ms) → {'이상 감지' if failure else '경계값 근접'}

    요약 (Java 기반 WAS에서 CPU 상승, 메모리 정상 원인)
    1. GC(Garbage Collection) 과다 발생 → Full GC 반복으로 CPU 점유율 상승하지만 메모리는 유지됨.
    2. CPU 바운드 작업 증가 → 무한 루프, 동기화 문제, 과도한 스레드 실행으로 CPU 사용률 급증.
    3. JIT 컴파일러 과부하 → Java의 동적 컴파일 최적화 과정에서 CPU 사용 증가.
    4. 과도한 System Call 또는 I/O 작업 → DB, 네트워크 요청 과부하로 CPU 점유율만 증가.

    문제 원인을 분석하려면 GC 로그, top -H, jstack, iostat, strace 등을 확인하면 됨."""

            if anomaly_name == "elapse_avg":
                response_data.append({
                    "llm_answer": llm_answer,
                    "inst_type": "Service"
                })

    # 2️⃣ 계층(tiers) 기반 이상 탐지 분석
    tiers = data.get("tiers", [])
    for tier in tiers:
        type_name = tier.get("type", None)
        tier_name = tier.get("name", None)
        instances = tier.get("instances", [])

        for instance in instances:
            metric = instance.get("metric", None)
            status = instance.get("status", None)
            target_id = instance.get("target_id", None)
            instance_name = instance.get("instance_name", None)

            # LLM 분석 응답 생성
            llm_answer = f"""
    -----------TEST-----------
    계층 이름: {tier_name}, 인스턴스: {instance_name}, 대상 ID: {target_id}
    메트릭: {metric}, 상태: {status}

    요약 (Java 기반 WAS에서 CPU 상승, 메모리 정상 원인)
    1. GC(Garbage Collection) 과다 발생 → Full GC 반복으로 CPU 점유율 상승하지만 메모리는 유지됨.
    2. CPU 바운드 작업 증가 → 무한 루프, 동기화 문제, 과도한 스레드 실행으로 CPU 사용률 급증.
    3. JIT 컴파일러 과부하 → Java의 동적 컴파일 최적화 과정에서 CPU 사용 증가.
    4. 과도한 System Call 또는 I/O 작업 → DB, 네트워크 요청 과부하로 CPU 점유율만 증가.

    문제 원인을 분석하려면 GC 로그, top -H, jstack, iostat, strace 등을 확인하면 됨."""
            type_category = ""
            if type_name == "os":
                type_category = "Host"
            elif type_name == "was":
                type_category = "Instance"

            response_data.append({
                "llm_answer": llm_answer,
                "inst_type": type_category
            })

    return response_data

QUEUE_KEY = "llm_request_queue"

# 상태 확인 간격 및 타임아웃
CHECK_INTERVAL = 1  # 1초 간격
TIMEOUT = 60  # 10초 초과 시 실패 처리

# 요청 데이터 모델
class Instance(BaseModel):
    target_id: str = Field(..., title="Target ID")
    status: str
    metric: str
    instance_name: str
    blocking_session: str | None = None

class Tier(BaseModel):
    name: str = Field(..., title="Tiers Name")
    type: str = Field(..., title="Tiers Type")
    instances: list[Instance] = Field(..., title="Instances List")

class RequestData(BaseModel):
    time: str = Field(..., title="Request Time")
    anomaly: bool
    tx_codes: dict
    tiers: list[Tier]  # 단일 Tier만 포함

class RequestModel(BaseModel):
    success: bool
    message: str | None
    total: int
    data: RequestData

@llm_router.post("/process")
async def process_request(request: RequestModel):
    redis_key = f"{request.data.time}tiers{request.data.tiers[0].name}_{request.data.tiers[0].type}"

    # Redis에서 결과 확인
    result = await redis_client.hget(redis_key, "status")
    if result == "true":
        response_data = await redis_client.hget(redis_key, "response")
        return json.loads(response_data)  # 결과 반환

    # Redis에 상태 초기화 (처리 중 상태)
    await redis_client.hset(redis_key, mapping={"status": "running", "response": "null"})

    # 큐에 요청 추가
    await redis_client.rpush(QUEUE_KEY, json.dumps(request.dict()))

    # 상태 확인 대기
    result = await wait_for_result(redis_key)
    return result


########################################################################################################
# Inwoo Test Code
@llm_router.post("/process_test")
async def process_request(request: Dict):
    data = request
    api_logger.debug(f"요청 수신: {data}")

    # (OS, WAS, DB), (Service) 요청 구분
    try:
        if data.get("tx_codes") and not data.get("tiers"):
            # Service
            request_obj = ServiceDataDTO(**request)
            request_obj.category_inst_type = "service"
            tmp_tx_code = list(request_obj.tx_codes.keys())[0]
            # redis_key = f"{request_obj.data.time}_tx_codes_{tmp_tx_code}_{request_obj.data.tx_codes[tmp_tx_code].name}"
            redis_key = f"{request_obj.time}_tx_codes_{tmp_tx_code}"
            api_logger.info(f"[Service] Redis Key 생성: {redis_key}")
        # elif data.get("tiers") and not data.get("tx_codes"):
        elif data.get("summary") and not data.get("tx_codes"):
            # OS, Instance, DB
            request_obj = HostInstanceDBRequestDTO(**request)
            request_obj.category_inst_type = "host_instance_db"
            # redis_key = f"{request_obj.data.time}_tiers_{request_obj.data.tiers[0].name}_{request_obj.data.tiers[0].type}_{request_obj.data.tiers[0].instances[0].target_id}"
            # redis_key = f"{request_obj.time}_tiers_{request_obj.tiers[0].type}_{request_obj.tiers[0].instances[0].target_id}"
            redis_key = f"{request_obj.summary.time}_tiers_{request_obj.summary.tiers[0].type}_{request_obj.summary.tiers[0].instances[0].target_id}"
            api_logger.info(f"[Host/Instance/DB] Redis Key 생성: {redis_key}")
        else:
            api_logger.error("유효하지 않은 요청 구조입니다.\n요청 데이터를 확인해주세요.")
            request_obj = None
            redis_key = None
    except Exception as e:
        api_logger.exception(f"요청 데이터 파싱 중 예외 발생: {e}")
        return {"message": "유효하지 않은 요청입니다."}

    # Redis에서 결과 확인
    result = await redis_client.hget(redis_key, "status")
    if result == "success":
        api_logger.info(f"Redis Key 조회 결과 SUCCESS: {redis_key}")
        response_data = await redis_client.hget(redis_key, "response")
        return json.loads(response_data)  # 결과 반환
    api_logger.info(f"Redis Key 조회 결과 None: {redis_key}")

    # Redis에 상태 초기화 (처리 중 상태)
    api_logger.info(f"요청 처리 시작 -> Redis 상태 초기화: {redis_key}")
    await redis_client.hset(redis_key, mapping={"status": "running", "response": "null"})

    # 큐에 요청 추가
    await redis_client.rpush(config.QUEUE_KEY, json.dumps(request_obj.dict()))
    api_logger.info(f"요청 처리 Queue 추가 -> Queue: {config.QUEUE_KEY}")

    # 상태 확인 대기
    result = await wait_for_result(redis_key)
    return result

########################################################################################################

async def wait_for_result(redis_key: str):
    """Redis에서 상태를 10초 동안 확인"""
    api_logger.info(f"요청 후 Redis Key 상태 조회 진행: {redis_key}")

    for _ in range(config.TIMEOUT):
        status = await redis_client.hget(redis_key, "status")

        if status == "success":
            api_logger.info(f"※ 요청 처리 완료 success: {redis_key}")
            response_data = await redis_client.hget(redis_key, "response")
            return json.loads(response_data)

        elif status == "failed":
            api_logger.error(f"※ 요청 처리 실패 failed: {redis_key}", exc_info=True)
            return {"message": "잠시 후에 다시 시도해주세요"}

        await asyncio.sleep(CHECK_INTERVAL)

    api_logger.warning(f"※ 요청 처리 시간 초과: {redis_key}")
    return {"message": "잠시 후에 다시 시도해주세요"}



if __name__ == "__main__":
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_name = "gpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    print("test")
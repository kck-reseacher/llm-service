from redis.commands.json.path import Path

from datetime import datetime

from llm_api.Models.database import rj
from llm_api.Utils.logger import db_logger


def _cal_day(date_str: str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.weekday()


def _cal_minute(date_str: str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.hour * 60 + dt.minute


def get_redis_metric_datas(time: str, metric: str, inst_type: str, target_or_txcode: str):
    day_num = _cal_day(time)
    minute = _cal_minute(time)

    if inst_type == "service":
        if 0 <= day_num <= 4:
            day_num = 0
        elif 5 <= day_num <= 6:
            day_num = 5

    key_name = f"exem_aiops_anls_service/{inst_type}/all/dbsln/dbsln_{inst_type}_all_{target_or_txcode}_{metric}_day{day_num}"

    db_logger.info(
        f"[Redis] 데이터 조회 시작 - key: {key_name}, 시간: {time} (분: {minute}), "
        f"지표: {metric}, 인스턴스 유형: {inst_type}, 대상: {target_or_txcode}"
    )

    try:
        result = rj.json().get(key_name, Path(f".{minute}"))
        db_logger.debug(f"[Redis] 조회 결과: {result}")
        return result

    except Exception:
        db_logger.exception(f"[Redis] 메트릭 기준선 조회 중 오류 발생 - key: {key_name}")
        return None

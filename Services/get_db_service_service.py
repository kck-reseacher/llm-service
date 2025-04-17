from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from llm_api.Models.dbsln_result_service_performance_model import DBSLNResultServicePerformance
from llm_api.Models.xaiops_meta_metric_model import XaiopsMetaMetric

from llm_api.Utils.logger import db_logger


def get_metrics_service(db:Session, time: str, target_id: str):
    """
    이상이 발생한 시점에서의 지표들과 실제값을 가져온다.
    :param db:
    :param time: 이상 발생 시점
    :param target_id: 타겟 이름
    :return:
    """
    db_logger.info(f"[Service] 성능 지표 조회 시작 - 시간: {time}, 대상 ID: {target_id}")
    try:
        result = db.query(
            DBSLNResultServicePerformance.metric,
            DBSLNResultServicePerformance.real_value
        ).filter(
            DBSLNResultServicePerformance.time == time,
            DBSLNResultServicePerformance.target_id == target_id
        ).all()

        db_logger.debug(f"[Service] 성능 지표 조회 결과: {result}")
        return result

    except SQLAlchemyError:
        db_logger.exception("[Service] 성능 지표 조회 중 오류 발생")
        return []


def get_metrics_names_service(db:Session, metrics: list):
    """
    Service의 경우 elapse_avg, sql_elapse07 와 같이 되어 있어서 metric의 desc을 가져와 사용한다.
    :param db:
    :param metrics: 이상 지표
    :return:
    """
    db_logger.info(f"[Service] 메트릭 설명 조회 시작 - 메트릭 목록: {metrics}")
    try:
        results = (
            db.query(XaiopsMetaMetric.metric_id, XaiopsMetaMetric.metric_desc)
            .filter(XaiopsMetaMetric.metric_id.in_(metrics))
            .all()
        )

        result_dict = {metric_id: metric_desc for metric_id, metric_desc in results}
        db_logger.debug(f"[Service] 메트릭 설명 조회 결과: {result_dict}")
        return result_dict

    except SQLAlchemyError:
        db_logger.exception("[Service] 메트릭 설명 조회 중 오류 발생")
        return {}
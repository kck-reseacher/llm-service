from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from llm_api.Models.ai_result_gdn_performance_model import AiResultGdnPerformance
from llm_api.Models.dbsln_result_performance_model import DbslnResultPerformanceModel

from llm_api.Utils.logger import db_logger


def get_metrics_host_instance_db2(db:Session, time: str, target_id: str, inst_type: str):
    return db.query(AiResultGdnPerformance.metric,
                    AiResultGdnPerformance.real_value).filter(
        AiResultGdnPerformance.time == time,
        AiResultGdnPerformance.target_id == target_id,
        AiResultGdnPerformance.inst_type == inst_type
    ).all()

def get_metrics_host_instance_db(db: Session, time: str, target_id: str, inst_type: str):
    db_logger.info(f"[Host, Instance, DB] GDN 성능 지표 조회 시작 - 시간: {time}, 대상 ID: {target_id}, 인스턴스 유형: {inst_type}")
    try:
        result = db.query(
            AiResultGdnPerformance.metric,
            AiResultGdnPerformance.real_value
        ).filter(
            AiResultGdnPerformance.time == time,
            AiResultGdnPerformance.target_id == target_id,
            AiResultGdnPerformance.inst_type == inst_type
        ).all()

        db_logger.debug(f"[Host, Instance, DB] GDN 성능 지표 조회 결과: {result}")
        return result

    except SQLAlchemyError:
        db_logger.exception("[Host, Instance, DB] GDN 성능 지표 조회 중 오류 발생")
        return []
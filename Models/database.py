from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# from rejson import Client
import redis

from config import config
from llm_api.Utils.logger import db_logger


# PostgreSQL 엔진 설정
engine = create_engine(config.database_url, echo=True)

# 세션 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 모델 생성
Base = declarative_base()

####################### Postgres DB Session 생성 #######################
def get_db():
    db_logger.info("[PostgreSQL] DB 세션 생성 시도")
    db = SessionLocal()
    try:
        return db
    except Exception:
        db_logger.exception("[PostgreSQL] DB 세션 생성 중 오류 발생")
        db.rollback()
        raise
    finally:
        db.close()
        db_logger.info("[PostgreSQL] DB 세션 종료")

####################### Redis Client 생성 함수 #######################
try:
    db_logger.info("[Redis] Redis 클라이언트 연결 시도")
    rj = redis.Redis(host=config.DATA_REDIS_HOST, port=config.DATA_REDIS_PORT, decode_responses=True)
    db_logger.info("[Redis] Redis 클라이언트 연결 성공")
except Exception as e:
    db_logger.exception("[Redis] Redis 클라이언트 연결 실패")
    raise


if __name__ == '__main__':
    db1 = get_db()
    from llm_api.Services.get_db_host_instance_db_service import get_metrics
    result = get_metrics(db1, "2024-12-17 00:00:00.000", "tp01", "tp")
    print("test")
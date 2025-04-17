import os

from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):

    # LLM Model Config
    model_name: str = "qwen2.5:14b-instruct-q8_0"
    llm_base_url: str = "10.10.34.20:11434"
    temperature: float = 0
    max_length: int = 512

    # DataBase URL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # Redis
    DATA_REDIS_HOST: str
    DATA_REDIS_PORT: int
    SAVE_REDIS_HOST: str
    SAVE_REDIS_PORT: int
    QUEUE_KEY: str = "llm_request_queue"
    # Redis 상태 확인 간격 및 타임아웃
    CHECK_INTERVAL: int = 1  # 1초 간격
    TIMEOUT: int = 120  # 10초 초과 시 실패 처리

    # Logger Name
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_BASE_DIR: str = os.path.join(BASE_DIR, "logs")

    LOGGER_API_NAME: str = "api"
    LOGGER_API_PATH: str = os.path.join(LOG_BASE_DIR, "api")
    LOGGER_CONSUMER_NAME: str = "consumer"
    LOGGER_CONSUMER_PATH: str = os.path.join(LOG_BASE_DIR, "consumer")
    LOGGER_LLM_NAME: str = "llm"
    LOGGER_LLM_PATH: str = os.path.join(LOG_BASE_DIR, "llm")
    LOGGER_DB_NAME: str = "db"
    LOGGER_DB_PATH: str = os.path.join(LOG_BASE_DIR, "db")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = '.env'


class DevelopmentConfig(BaseConfig):

    class Config:
        env_file = '.env.dev'


class ProductionConfig(BaseConfig):

    class Config:
        env_file = '.env.prod'

# 환경변수 조회
env = os.getenv('ENV', 'dev')

# Config 객체 생성
config: BaseConfig = DevelopmentConfig() if env == 'dev' else ProductionConfig()
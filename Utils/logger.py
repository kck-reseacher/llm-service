import os
import logging

from logging.handlers import TimedRotatingFileHandler

from config import config


def check_log_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def init_logger(name: str, log_folder: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

    if not logger.handlers:
        # 로그 저장 디렉터리 생성
        check_log_dir(log_folder)

        # 날짜별 롤링 파일 핸들러
        log_file_path = os.path.join(log_folder, f"{name}.log")  # 실제 파일 이름 패턴은 핸들러가 관리
        rotating_handler = TimedRotatingFileHandler(
            log_file_path, when="midnight", interval=1, encoding='utf-8', backupCount=30, utc=False
        )
        rotating_handler.suffix = "%Y-%m-%d"  # 파일 이름에 날짜 붙게 설정
        rotating_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(rotating_handler)
        logger.addHandler(console_handler)

        logger.propagate = False

    return logger

api_logger = init_logger(config.LOGGER_API_NAME, config.LOGGER_API_PATH)
consumer_logger = init_logger(config.LOGGER_CONSUMER_NAME, config.LOGGER_CONSUMER_PATH)
llm_logger = init_logger(config.LOGGER_LLM_NAME, config.LOGGER_LLM_PATH)
db_logger = init_logger(config.LOGGER_DB_NAME, config.LOGGER_DB_PATH)
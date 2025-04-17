from fastapi import FastAPI

from llm_api.Controllers.get_llm_response_controller import llm_router


def create_app():
    app = FastAPI(
        title="API Server Of LLM For Test",
        description="해당 API Server는 XAIOps 내부 LLM 테스트를 위해 제작되었습니다.",
        version="0.1.0"
    )

    app.include_router(llm_router, prefix="/llm")
    return app

# @staticmethod
# def get_environment_variable():
#     # AIMODULE_HOME
#     home = os.environ.get(sc.AIMODULE_HOME)
#     if home is None:
#         print("plz export AIMODULE_HOME")
#         home = os.path.dirname(os.path.abspath(__file__))
#
#     # MLOPS_LOG_PATH
#     log_path = os.environ.get(sc.MLOPS_LOG_PATH)
#     if log_path is None:
#         print("plz export MLOPS_LOG_PATH")
#         log_path = os.path.dirname(os.path.abspath(__file__))
#
#     # AIMODULE_PATH
#     py_path = os.environ.get("AIMODULE_CHATBOT_PATH")
#     if py_path is None:
#         print("plz export AIMODULE_CHATBOT_PATH")
#         py_path = os.path.dirname(os.path.abspath(__file__))
#
#     # AIMODULE_PATH
#     server_env = os.environ.get(sc.AIMODULE_SERVER_ENV)
#     if server_env is None:
#         print("plz export AIMODULE_SERVER_ENV")
#         py_path = os.path.dirname(os.path.abspath(__file__))
#
#     return home, log_path, py_path, server_env
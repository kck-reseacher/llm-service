import uvicorn

from fastapi.middleware.cors import CORSMiddleware
from llm_api.Utils.app_utils import create_app


app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return "Hello, FastAPI!"

@app.get("/ping")
def ping():
    return "Pong!"

@app.get("/hello/{name}")
def hello(name: str):
    return f"Hello, {name}"

@app.get("/status")
def status():
    return "server is running smoothly."


if __name__ == "__main__":

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8893,
        reload=True
    )
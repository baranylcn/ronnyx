from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.routers import router as chat_router

load_dotenv()

app = FastAPI(
    title="Ronnyx",
    version="0.1.0",
)

app.include_router(chat_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}

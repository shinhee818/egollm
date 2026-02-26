from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.api.chat_router import router as chat_router
from app.api.quiz_router import router as quiz_router
from app.api.quiz_generator_router import router as quiz_generator_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: 나중에 DB 붙일 것
    yield

app = FastAPI(
    title="Egoeng Quiz API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(quiz_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(quiz_generator_router)


@app.get("/health")
def health():
    return {"status": "ok"}

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure repo root is importable (backend.app + model)
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config.settings import CORS_ORIGINS
from backend.app.routes.audit import router as audit_router
from backend.app.routes.datasets import router as datasets_router
from backend.app.routes.metrics import router as metrics_router
from backend.app.routes.pipeline import router as pipeline_router
from backend.app.routes.predict import router as predict_router
from backend.app.services.inference import init_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_model(device="cpu")
    yield


app = FastAPI(
    title="ABSA Inference API",
    description="Vietnamese Aspect-Based Sentiment Analysis — local demo",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(metrics_router)
app.include_router(audit_router)
app.include_router(datasets_router)
app.include_router(pipeline_router)


if __name__ == "__main__":
    import uvicorn

    from backend.app.config.settings import API_HOST, API_PORT

    uvicorn.run(
        "backend.app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
    )

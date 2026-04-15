from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Sentiment Inference API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictRequest) -> dict:
    # TODO: Load the actual ViDeBERTa model and tokenizer here.
    return {
        "success": True,
        "data": {
            "text": payload.text,
            "overall_sentiment": "Tích cực",
            "aspects": [
                {
                    "aspect": "Dịch vụ",
                    "sentiment": "Tích cực",
                    "confidence": 0.98,
                }
            ],
        },
    }

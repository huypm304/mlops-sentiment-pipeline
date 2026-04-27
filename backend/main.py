import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from model.inference import model_fn, predict_fn
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev thì để *
    allow_credentials=True,
    allow_methods=["*"],  # cho phép OPTIONS
    allow_headers=["*"],
)

MODEL_DIR = "model" 
model_dict = model_fn(MODEL_DIR)

class FeedbackRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(request: FeedbackRequest):
    try:
        result = predict_fn(request.text, model_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/eda")
def get_eda():
    import json
    with open("/frontend/public/eda.py", encoding="utf-8") as f:
        return json.load(f)
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
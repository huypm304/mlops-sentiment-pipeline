import boto3
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = boto3.client("sagemaker-runtime", region_name="ap-southeast-1")

class SentimentRequest(BaseModel):
    text: str

def get_prediction(text):
    response = client.invoke_endpoint(
        EndpointName="absa-mlops-huy-endpoint-v2", 
        ContentType="application/json",
        Body=json.dumps({"inputs": text})
    )
    result = json.loads(response["Body"].read().decode())
    return result

@app.post("/predict")
async def predict(request: SentimentRequest):
    try:
        prediction = get_prediction(request.text)
        return {"status": "success", "data": prediction}
    except Exception as e:
        return {"status": "error", "message": str(e)}
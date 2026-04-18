import boto3
import json
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SentimentRequest(BaseModel):
    text: str

@app.post("/predict")
async def predict(request: SentimentRequest):
    try:
        # Gọi hàm get_prediction của Huy
        prediction = get_prediction(request.text)
        return {"status": "success", "data": prediction}
    except Exception as e:
        return {"status": "error", "message": str(e)}
client = boto3.client("sagemaker-runtime", region_name="ap-southeast-1")

def get_prediction(text):
    response = client.invoke_endpoint(
        EndpointName="absa-mlops-huy-endpoint", # Thay đúng tên vào đây
        ContentType="application/json",
        Body=json.dumps({"inputs": text})
    )
    result = json.loads(response["Body"].read().decode())
    return result
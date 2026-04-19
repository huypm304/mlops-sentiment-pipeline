import boto3
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from botocore.config import Config

# 1. Cấu hình timeout để không bị xoay mãi mãi
my_config = Config(
    region_name = 'ap-southeast-1',
    connect_timeout = 5,
    read_timeout = 60,  # Tăng lên 60s vì model PhoBERT load lần đầu hơi lâu
    retries = {'max_attempts': 2}
)

# 2. KHỞI TẠO CLIENT DUY NHẤT MỘT LẦN
client = boto3.client("sagemaker-runtime", config=my_config)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SentimentRequest(BaseModel):
    text: str

def get_prediction(text):
    # Log để check xem hàm có chạy vào đây không
    print(f"--- Sending to SageMaker: {text} ---")
    response = client.invoke_endpoint(
        EndpointName="absa-mlops-huy-endpoint-v2", 
        ContentType="application/json",
        Body=json.dumps({"inputs": text})
    )
    result = json.loads(response["Body"].read().decode())
    return result

@app.post("/analyze") 
async def predict(request: SentimentRequest):
    try:
        raw_result = get_prediction(request.text)
        print(f"DEBUG FROM SAGEMAKER: {raw_result}")

        # Nắn lại dữ liệu trả về cho Frontend
        return {
            "global_sentiment": "Positive" if any(x.get('sentiment') == 'Positive' for x in raw_result) else "Negative",
            "aspects": raw_result  
        }
    except Exception as e:
        print(f"Lỗi kết nối SageMaker: {str(e)}")
        # Trả về lỗi chi tiết để Huy nhìn trên web là biết sai đâu luôn
        return {"global_sentiment": "Error", "aspects": [{"aspect": "SYSTEM", "sentiment": "Error", "target": str(e)}]}
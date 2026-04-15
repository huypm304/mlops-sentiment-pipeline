# MLOps Project Blueprint: ABSA with ViDeBERTa (Local MVP)

## 1. Project Overview
This project is an Enterprise-grade Aspect-Based Sentiment Analysis (ABSA) system.
Currently, we are building the **Local MVP (Minimum Viable Product)** for the Inference layer before deploying to AWS.

**Tech Stack:**
- Model: ViDeBERTa (PyTorch/Transformers)
- Backend API: FastAPI (Python)
- Frontend UI: React.js (Vite)

---

## 2. Folder Structure
Agent, please enforce the following strict minimalist directory structure. Do NOT create global requirements files.

```text
├── /data                # Contains existing data crawling and training scripts. (Do not modify)
├── /model               # Contains weights and training logic. (Do not modify)
├── /backend             # The FastAPI Inference Server
│   ├── main.py
│   └── requirements.txt
└── /frontend            # The React UI (Vite)
    ├── package.json
    └── src/
        └── App.jsx
Task 1: Setup Backend API
Create /backend/requirements.txt with exactly these contents (Strictly NO other libraries):

Plaintext
fastapi==0.110.0
uvicorn==0.29.0
pydantic==2.6.4
torch==2.10.0
transformers==5.3.0
pandas==2.3.3
huggingface_hub==1.6.0
python-dotenv==1.2.2
Create /backend/main.py using FastAPI.

Configure CORSMiddleware allowing all origins (*).

Create a POST /predict endpoint that accepts { "text": "string" }.

Implement mock inference logic that returns JSON in this format:
{ "success": true, "data": { "text": "...", "overall_sentiment": "Tích cực", "aspects": [{"aspect": "Dịch vụ", "sentiment": "Tích cực", "confidence": 0.98}] } }.

(Leave a comment placeholder for loading the actual ViDeBERTa model).

Task 2: Setup Frontend UI
Initialize a React project using Vite inside the /frontend directory.

Install axios.

Overwrite /frontend/src/App.jsx to create a simple form:

A <textarea> for customer feedback input.

A submit <button>.

On submit, use axios to POST data to http://localhost:8000/predict.

CRITICAL UI RULE: Only render the overall_sentiment and text on the screen. The aspects and confidence scores MUST be hidden from the UI but logged to console.log() for developer debugging.

Task 3: Output Instructions
After creating the files, print out the exact terminal commands the user needs to run to start both the Backend (uvicorn) and Frontend (npm run dev) simultaneously in two different terminal tabs.
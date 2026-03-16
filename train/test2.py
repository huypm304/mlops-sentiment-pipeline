import torch
import pickle
import numpy as np
from transformers import AutoTokenizer, AutoModel
from underthesea import word_tokenize

# 1. Load PhoBERT (Chỉ để encode 1 câu duy nhất nhập vào)
device = torch.device("cpu")
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base").to(device)
model.eval()

# 2. Load "Bộ não" đã học xong (Logistic Regression)
with open(r'data\processed\logistic_model.pkl', 'rb') as f:
    clf = pickle.load(f)

def quick_predict(comment):
    # Tách từ và lấy embedding cho DUY NHẤT câu này
    comment_seg = word_tokenize(comment, format="text")
    inputs = tokenizer(comment_seg, return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
    
    # Dự đoán
    pred = clf.predict(embedding)[0]
    prob = clf.predict_proba(embedding)[0]
    
    status = "TÍCH CỰC ✅" if pred == 1 else "TIÊU CỰC ❌"
    print(f"\n💬: {comment}\n🤖: {status} ({prob[pred]*100:.2f}%)")

if __name__ == "__main__":
    while True:
        text = input("\nNhập câu bình luận (hoặc 'q' để thoát): ")
        if text.lower() == 'q': break
        quick_predict(text)
import pandas as pd
import torch
import numpy as np
import pickle
import os
from transformers import AutoTokenizer, AutoModel
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm

# ==============================
# 1. CẤU HÌNH & LOAD DATA
# ==============================
MODEL_PATH = r'.\data\processed\logistic_model.pkl'
os.makedirs(r'.\data\processed', exist_ok=True)

train_df = pd.read_csv(r".\data\processed\train_dataset.csv")
label_map = {"negative": 0, "positive": 1}
train_df["label"] = train_df["sentiment"].map(label_map)

# ==============================
# 2. KHỞI TẠO PHOBERT
# ==============================
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base")
device = torch.device("cpu") # Laptop chạy CPU là ổn
model.to(device)
model.eval()

def encode_texts(texts, batch_size=32):
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
            cls_embedding = outputs.last_hidden_state[:, 0, :]
        embeddings.append(cls_embedding.cpu().numpy())
    return np.vstack(embeddings)

# ==============================
# 3. TRAIN & SAVE
# ==============================
print("Đang trích xuất đặc trưng (Encoding)...")
texts = train_df["review_segmented"].fillna("").astype(str).tolist()
X_train = encode_texts(texts)
y_train = train_df["label"].values

print("Đang huấn luyện bộ phân loại Logistic Regression...")
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

# ĐÂY LÀ BƯỚC LƯU MODEL
print(f"Đang lưu model vào {MODEL_PATH}...")
with open(MODEL_PATH, 'wb') as f:
    pickle.dump(clf, f)

print("ĐÃ XONG! Giờ Huy có thể dùng file test mà không cần train lại.")
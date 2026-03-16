import pandas as pd
import torch
import numpy as np

from transformers import AutoTokenizer, AutoModel
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from tqdm import tqdm

# ==============================
# LOAD DATA
# ==============================

train_df = pd.read_csv(r".\data\processed\train_dataset.csv")
test_df = pd.read_csv(r".\data\processed\test_dataset.csv")

label_map = {"negative":0,"positive":1}

train_df["label"] = train_df["sentiment"].map(label_map)
test_df["label"] = test_df["sentiment"].map(label_map)

# ==============================
# LOAD PHOBERT
# ==============================

tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModel.from_pretrained("vinai/phobert-base")

model.eval()

device = torch.device("cpu")
model.to(device)

# ==============================
# EMBEDDING FUNCTION (BATCH)
# ==============================

def encode_texts(texts, batch_size=32):

    embeddings = []

    for i in tqdm(range(0, len(texts), batch_size)):

        batch = texts[i:i+batch_size]

        inputs = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )

        inputs = {k:v.to(device) for k,v in inputs.items()}

        with torch.no_grad():

            outputs = model(**inputs)

            cls_embedding = outputs.last_hidden_state[:,0,:]

        embeddings.append(cls_embedding.cpu().numpy())

    return np.vstack(embeddings)

# ==============================
# ENCODE DATA
# ==============================

print("Encoding train data...")

texts = train_df["review_segmented"].fillna("").astype(str).tolist()
X_train = encode_texts(texts)

y_train = train_df["label"].values

print("Encoding test data...")

X_test = encode_texts(test_df["review_segmented"].tolist())

y_test = test_df["label"].values

# ==============================
# TRAIN CLASSIFIER
# ==============================

clf = LogisticRegression(max_iter=1000)

clf.fit(X_train, y_train)

pred = clf.predict(X_test)

print("\nClassification Report:\n")

print(classification_report(y_test, pred))
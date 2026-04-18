# Tóm tắt Script Train ABSA v3 — `model/train.py`

## 1. Mục tiêu

Train mô hình **Aspect-Based Sentiment Analysis (ABSA)** v3 giải quyết 3 nhiệm vụ cùng lúc trên mỗi câu:

| Nhiệm vụ | Mô tả |
|---|---|
| **BIO Tagging** | Nhận diện các span (token-level) thuộc 1 aspect cụ thể (Product, Service, Ship, Price, App) |
| **Aspect Sentiment** | Phân loại sentiment cho từng aspect span được phát hiện (Neg/Pos/Neu) |
| **Global Sentiment** | Phân loại sentiment tổng thể của cả câu (Neg/Pos/Neu) |

---

## 2. Kiến trúc Model — `ABSAv3`

```
Input Text
    │
    ▼
┌──────────────────────────────────────────┐
│  Backbone: Fsoft-AIC/videberta-base      │  (hidden=768)
└──────────────────────────────────────────┘
    │
    ├── CLS token ──► Dropout ──► Global Head (Linear 768→3)
    │                                    └──> global_sentiment logits
    │
    └── Sequence Output (last_hidden_state)
            │
            ├── Dropout ──► BIO Head (Linear 768→11)
            │                        └──> bio_emissions ──► CRF (11 tags)
            │
            ├── AttentionPooling
            │         (dùng span_mask để tập trung vào span context)
            └──► Sent Head (Linear 768→3)
                      └──> span_sentiment logits
```

### Các thành phần chính

- **Backbone**: `Fsoft-AIC/videberta-base` (Frozen/finetune được)
- **BIO Head**: Linear layer → emissions → **CRF layer** (Sequence labeling)
- **Global Head**: Linear trên CLS token → phân loại sentiment toàn câu
- **Attention Pooling**: Weighted sum theo `span_mask` → repr cho từng aspect span
- **Sent Head**: Phân loại sentiment cho từng span đã detect

### Số lượng nhãn

| Head | Số nhãn |
|---|---|
| BIO | 11 (`O`, `B-Product`, `I-Product`, `B-Service`, ..., `I-App`) |
| Sentiment (span) | 3 (Neg=0, Pos=1, Neu=2) |
| Global | 3 (Neg=0, Pos=1, Neu=2) |

---

## 3. Cấu hình Hyperparameter

| Tham số | Giá trị | Ghi chú |
|---|---|---|
| `MODEL_NAME` | `Fsoft-AIC/videberta-base` | Pretrained backbone |
| `MAX_LEN` | 320 | Max token length |
| `BATCH_SIZE` | 8 | |
| `ACCUM_STEPS` | 4 | Effective batch = 32 |
| `EPOCHS` | 12 | |
| `LR_BACKBONE` | 1.5e-5 | Learning rate cho backbone |
| `LR_HEADS` | 3e-5 | Learning rate cho các head |
| `WARMUP_RATIO` | 0.1 | Warmup ratio |
| `DROPOUT` | 0.15 | |
| `PATIENCE` | 4 | Early stopping |
| `SEED` | 42 | |
| `weight_decay` | 0.01 | |

### Trọng số Loss

| Loss | Lambda | Giá trị |
|---|---|---|
| BIO CRF Loss | `LAMBDA_BIO` | 1.0 |
| Sentiment Loss | `LAMBDA_SENT` | 1.5 |
| Global Loss | `LAMBDA_GLOBAL` | 0.3 |

### Focal Loss Alpha Weights

```
alpha_sent   = [1.2, 1.0, 1.8]   # [Neg, Pos, Neu]
alpha_global = [1.0, 1.0, 1.2]   # [Neg, Pos, Neu]
gamma        = 2.0               # focal loss gamma
```

---

## 4. Dữ liệu (Data Format)

File đầu vào: **JSONL** (mỗi dòng 1 JSON object)

```json
{
  "text": "Sản phẩm tốt nhưng giao hàng chậm",
  "global_sentiment": 1,
  "opinions": [
    {
      "aspect": "Product",
      "sentiment": 1,
      "start": 0,
      "end": 12
    },
    {
      "aspect": "Ship",
      "sentiment": 0,
      "start": 23,
      "end": 36
    }
  ]
}
```

### Đường dẫn data (Colab)

| File | Path |
|---|---|
| Train | `/content/train_data_v3.jsonl` |
| Validation | `/content/val_data.jsonl` |
| Test | `/content/test_data.jsonl` |

### Token Alignment

- Dùng `offset_mapping` để align **character-level spans** → **token-level indices**
- Bỏ qua các token đặc biệt (CLS, SEP, PAD, etc.)
- Mỗi opinion span lấy thêm `CONTEXT_TOKENS=2` token xung quanh làm context

---

## 5. Hàm Loss Tổng

```
total_loss = (λ_BIO * CRF_loss + λ_SENT * Sent_loss + λ_GLOBAL * Global_loss) / ACCUM_STEPS
```

Trong đó **Sent_loss** và **Global_loss** dùng **Focal Loss** để xử lý class imbalance.

---

## 6. Quá trình Train

```
1 epoch = n_batch // ACCUM_STEPS optimizer steps
```

1. **Forward** qua model → thu logits
2. **Tính 3 losses** (BIO/CRF, Sentiment-Focal, Global-Focal)
3. **Backward** (gradient accumulation mỗi `ACCUM_STEPS` steps)
4. **Gradient clipping** `max_norm=1.0`
5. **Optimizer step** + **Scheduler step**

### Metrics đánh giá mỗi epoch (trên validation)

| Metric | Công thức |
|---|---|
| **Span F1** | P/R/F1 từ tập BIO spans (aspect-level) |
| **Sent F1** | Macro-F1 trên sentiment predictions |
| **Global F1** | Macro-F1 trên global sentiment |
| **Composite Score** | `0.4 * sent_f1 + 0.4 * span_f1 + 0.2 * global_f1` |

**Early stopping** dựa trên `composite_score` với `patience=4`.

---

## 7. Output

| File | Mô tả |
|---|---|
| `best_absa_v3.pt` | Checkpoint chứa `model_state_dict` + config |
| `training_log_v3.csv` | Log train_loss, val_loss, score mỗi epoch |

Checkpoint format:
```python
{
    "epoch": int,
    "model_state": OrderedDict,   # model.state_dict()
    "config": {
        "model_name": "Fsoft-AIC/videberta-base",
        "max_len": 320
    }
}
```

---

## 8. Các hàm tiện ích chính

| Hàm | Mô tả |
|---|---|
| `build_bio_labels()` | Build danh sách 11 nhãn BIO |
| `find_token_indices()` | Map character span → token indices |
| `extract_bio_spans()` | Decode BIO sequence → set of (start, end, aspect) |
| `span_prf()` | Tính P/R/F1 cho span-level extraction |
| `focal_loss()` | Focal loss với class weights |
| `composite_score()` | Weighted combination: `0.4*sent + 0.4*span + 0.2*global` |
| `run_eval()` | Full evaluation trên 1 dataloader |
| `set_seed()` | Reproducibility |

---

## 9. Đặc điểm nổi bật

- ✅ **CRF layer** cho BIO tagging — capture transition constraints
- ✅ **Focal Loss** — handle class imbalance (đặc biệt Neutral)
- ✅ **Gradient Accumulation** — effective batch = 32 trên GPU memory hạn chế
- ✅ **Attention Pooling** — học được representation cho từng aspect span riêng biệt
- ✅ **Composite Score** — cân bằng cả 3 nhiệm vụ trong early stopping
- ✅ **Early Stopping** — ngăn overfitting
- ✅ **Auto-download** — tự động tải checkpoint + log về máy local sau train

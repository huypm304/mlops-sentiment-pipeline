"""
reference_test.py
─────────────────
Reference script để test model best_absa_v3.pt

Fixes vs version cũ:
  - predict_one: 1 lần encode backbone, tái dùng seq_out cho cả BIO + Sentiment
  - Bỏ rule-based aspect correction (override kết quả model)
  - evaluate: truyền span_masks từ dataset (không rebuild trong inference)

Chạy:
  python reference_test.py                        # Demo
  python reference_test.py --eval                 # Eval trên test set
  python reference_test.py --text "câu cần test"  # Single prediction
"""

import argparse
import json
import os
import unicodedata

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import f1_score, classification_report
from tqdm import tqdm
from torchcrf import CRF


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

MODEL_NAME     = "Fsoft-AIC/videberta-base"
MODEL_PATH     = "model/best_absa_v3.pt"
MAX_LEN        = 320
BATCH_SIZE     = 8
MAX_OPS        = 8
CONTEXT_TOKENS = 2

ASPECTS    = ["Product", "Service", "Ship", "Price", "App"]
SENTIMENTS = [0, 1, 2]
SENT_NAME  = {0: "Neg 🔴", 1: "Pos 🟢", 2: "Neu 🟡"}
SENT_SHORT = {0: "Neg",    1: "Pos",    2: "Neu"}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Label maps ────────────────────────────────────────────────────────────────

def build_bio_labels():
    labels = ["O"]
    for asp in ASPECTS:
        labels.append(f"B-{asp}")
        labels.append(f"I-{asp}")
    l2i = {l: i for i, l in enumerate(labels)}
    i2l = {i: l for i, l in enumerate(labels)}
    return labels, l2i, i2l

BIO_LABELS, BIO_LABEL2ID, BIO_ID2LABEL = build_bio_labels()
N_BIO    = len(BIO_LABELS)   # 11
N_SENT   = 3
N_GLOBAL = 3


# ══════════════════════════════════════════════════════════════════════════════
# MODEL (phải khớp hoàn toàn với train_absa_v3.py)
# ══════════════════════════════════════════════════════════════════════════════

class AttentionPooling(nn.Module):
    def __init__(self, hidden: int):
        super().__init__()
        self.scorer = nn.Linear(hidden, 1)

    def forward(self, x, mask):
        scores  = self.scorer(x).squeeze(-1)
        scores  = scores.masked_fill(mask == 0, -1e9)
        weights = torch.softmax(scores, dim=-1)
        return (x * weights.unsqueeze(-1)).sum(dim=2)


class ABSAv3(nn.Module):
    def __init__(self, model_name: str, dropout: float = 0.15):
        super().__init__()
        self.backbone    = AutoModel.from_pretrained(model_name)
        hidden           = self.backbone.config.hidden_size
        self.dropout     = nn.Dropout(dropout)
        self.bio_head    = nn.Linear(hidden, N_BIO)
        self.crf         = CRF(N_BIO, batch_first=True)
        self.span_attn   = AttentionPooling(hidden)
        self.sent_head   = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden, N_SENT))
        self.global_head = nn.Linear(hidden, N_GLOBAL)

    def forward(self, input_ids, attention_mask,
                span_masks=None, bio_labels=None):
        out       = self.backbone(input_ids=input_ids,
                                  attention_mask=attention_mask)
        seq_out   = self.dropout(out.last_hidden_state)
        cls_out   = self.dropout(seq_out[:, 0, :])
        mask_bool = attention_mask.bool()

        bio_emissions = self.bio_head(seq_out)

        if bio_labels is not None:
            crf_loss  = -self.crf(bio_emissions, bio_labels,
                                  mask=mask_bool, reduction="mean")
            bio_preds = None
        else:
            crf_loss  = None
            bio_preds = self.crf.decode(bio_emissions, mask=mask_bool)

        global_logits = self.global_head(cls_out)

        span_logits = None
        if span_masks is not None:
            B, L, H = seq_out.shape
            M       = span_masks.shape[1]
            seq_exp     = seq_out.unsqueeze(1).expand(B, M, L, H)
            span_repr   = self.span_attn(seq_exp, span_masks)
            span_logits = self.sent_head(span_repr)

        return bio_emissions, crf_loss, bio_preds, span_logits, global_logits


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text) if text else ""


def find_token_indices(offsets, special_mask, char_s: int, char_e: int):
    indices = []
    for i, (tok_s, tok_e) in enumerate(offsets):
        if special_mask[i] or (tok_s == 0 and tok_e == 0):
            continue
        if max(tok_s, char_s) < min(tok_e, char_e):
            indices.append(i)
    return indices


def extract_bio_spans(label_seq):
    spans, start, cur = set(), None, None
    for i, lid in enumerate(label_seq):
        s = BIO_ID2LABEL.get(lid, "O")
        if s.startswith("B-"):
            if start is not None:
                spans.add((start, i - 1, cur))
            start, cur = i, s[2:]
        elif s.startswith("I-") and cur and s[2:] == cur:
            pass
        else:
            if start is not None:
                spans.add((start, i - 1, cur))
            start = cur = None
    if start is not None:
        spans.add((start, len(label_seq) - 1, cur))
    return spans


def span_prf(pred_list, gold_list, aspect_filter=None):
    tp = fp = fn = 0
    for ps, gs in zip(pred_list, gold_list):
        if aspect_filter:
            ps = {s for s in ps if s[2] == aspect_filter}
            gs = {s for s in gs if s[2] == aspect_filter}
        tp += len(ps & gs)
        fp += len(ps - gs)
        fn += len(gs - ps)
    p = tp / (tp + fp + 1e-9)
    r = tp / (tp + fn + 1e-9)
    f = 2 * p * r / (p + r + 1e-9)
    return p, r, f


def load_model(model_path: str) -> ABSAv3:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Không tìm thấy model: {model_path}")
    checkpoint   = torch.load(model_path, map_location=DEVICE)
    inferred     = checkpoint.get("config", {}).get("model_name", MODEL_NAME)
    model        = ABSAv3(inferred).to(DEVICE).float()
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    print(f"  ✅ Loaded epoch={checkpoint.get('epoch', '?')}  model={inferred}")
    return model


# ══════════════════════════════════════════════════════════════════════════════
# DATASET (dùng cho eval)
# ══════════════════════════════════════════════════════════════════════════════

class ABSADataset(Dataset):
    def __init__(self, file_path: str, tokenizer, max_len: int):
        self.tokenizer = tokenizer
        self.max_len   = max_len
        self.items     = self._load(file_path)

    def _load(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"⚠️ Không tìm thấy: {file_path}")

        items, skipped, align_miss = [], 0, 0
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                text        = nfc(rec.get("text", "").strip())
                global_sent = rec.get("global_sentiment", -1)
                opinions    = rec.get("opinions", [])

                if len(text) < 2 or global_sent not in [0, 1, 2]:
                    skipped += 1
                    continue

                enc = self.tokenizer(
                    text,
                    max_length=self.max_len,
                    padding="max_length",
                    truncation=True,
                    return_offsets_mapping=True,
                    return_special_tokens_mask=True,
                )

                offsets      = enc.pop("offset_mapping")
                special_mask = enc.pop("special_tokens_mask")
                seq_len      = len(enc["input_ids"])

                bio_labels = [BIO_LABEL2ID["O"]] * seq_len
                span_masks = torch.zeros(MAX_OPS, seq_len)
                span_sents = torch.full((MAX_OPS,), -100, dtype=torch.long)

                op_idx = 0
                for op in opinions:
                    if op_idx >= MAX_OPS:
                        break
                    asp      = op.get("aspect", "")
                    sent_int = op.get("sentiment", -1)
                    char_s   = op.get("start", -1)
                    char_e   = op.get("end", -1)

                    if asp not in ASPECTS or sent_int not in SENTIMENTS:
                        continue
                    if char_s < 0 or char_e <= char_s:
                        continue

                    token_indices = find_token_indices(
                        offsets, special_mask, char_s, char_e
                    )
                    if not token_indices:
                        align_miss += 1
                        continue

                    for idx, i in enumerate(token_indices):
                        prefix    = "B" if idx == 0 else "I"
                        label_str = f"{prefix}-{asp}"
                        if label_str in BIO_LABEL2ID:
                            bio_labels[i] = BIO_LABEL2ID[label_str]

                    lo = max(0, token_indices[0]  - CONTEXT_TOKENS)
                    hi = min(seq_len - 1, token_indices[-1] + CONTEXT_TOKENS)
                    for i in range(lo, hi + 1):
                        if not special_mask[i] and not (
                            offsets[i][0] == 0 and offsets[i][1] == 0
                        ):
                            span_masks[op_idx, i] = 1.0

                    span_sents[op_idx] = sent_int
                    op_idx += 1

                items.append({
                    "input_ids"     : torch.tensor(enc["input_ids"],      dtype=torch.long),
                    "attention_mask": torch.tensor(enc["attention_mask"],  dtype=torch.long),
                    "bio_labels"    : torch.tensor(bio_labels,             dtype=torch.long),
                    "span_masks"    : span_masks,
                    "span_sents"    : span_sents,
                    "global_label"  : torch.tensor(global_sent,            dtype=torch.long),
                })

        print(f"  📂 {os.path.basename(file_path)}: "
              f"{len(items):,} items  "
              f"(skipped={skipped}, align_miss={align_miss})")
        return items

    def __len__(self):        return len(self.items)
    def __getitem__(self, i): return self.items[i]


# ══════════════════════════════════════════════════════════════════════════════
# INFERENCE ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ABSAEngine:
    def __init__(self, model_path: str = MODEL_PATH):
        self.device    = DEVICE
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model     = load_model(model_path)

    @torch.no_grad()
    def predict_one(self, text: str):
        """
        1 lần encode backbone, tái dùng seq_out cho cả BIO và Sentiment.
        Không forward 2 lần, không rule-based override.
        """
        text = nfc(text.strip())
        if not text:
            return {"global_sentiment": SENT_NAME[2], "aspects": []}

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=MAX_LEN,
            return_offsets_mapping=True,
            return_special_tokens_mask=True,
        )

        input_ids      = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        offsets        = inputs.pop("offset_mapping")[0].cpu().numpy()
        special_mask   = inputs.pop("special_tokens_mask")[0].cpu().numpy()
        seq_len        = input_ids.shape[1]
        mask_bool      = attention_mask.bool()

        # ── Step 1: Encode backbone 1 lần duy nhất ───────────
        out     = self.model.backbone(input_ids=input_ids,
                                      attention_mask=attention_mask)
        seq_out = self.model.dropout(out.last_hidden_state)  # (1, L, H)
        cls_out = self.model.dropout(seq_out[:, 0, :])       # (1, H)

        # ── Step 2: BIO decode ────────────────────────────────
        bio_em    = self.model.bio_head(seq_out)
        bio_preds = self.model.crf.decode(bio_em, mask=mask_bool)
        spans     = extract_bio_spans(bio_preds[0])

        # ── Step 3: Global sentiment ──────────────────────────
        global_logits = self.model.global_head(cls_out)
        global_pred   = int(torch.argmax(global_logits, dim=-1).item())
        global_conf   = round(
            torch.softmax(global_logits, dim=-1)[0].max().item(), 4
        )

        if not spans:
            return {
                "global_sentiment" : SENT_NAME[global_pred],
                "global_confidence": global_conf,
                "aspects"          : [],
            }

        # ── Step 4: Build span_masks từ BIO spans ─────────────
        span_masks  = torch.zeros(1, MAX_OPS, seq_len, device=self.device)
        sorted_spans = sorted(list(spans))

        for idx, (s_idx, e_idx, _) in enumerate(sorted_spans):
            if idx >= MAX_OPS:
                break
            lo = max(0, s_idx - CONTEXT_TOKENS)
            hi = min(seq_len - 1, e_idx + CONTEXT_TOKENS)
            for i in range(lo, hi + 1):
                if not special_mask[i] and not (
                    offsets[i][0] == 0 and offsets[i][1] == 0
                ):
                    span_masks[0, idx, i] = 1.0

        # ── Step 5: Span sentiment — tái dùng seq_out ─────────
        B, L, H = seq_out.shape
        M       = span_masks.shape[1]
        seq_exp     = seq_out.unsqueeze(1).expand(B, M, L, H)
        span_repr   = self.model.span_attn(seq_exp, span_masks)
        span_logits = self.model.sent_head(span_repr)          # (1, M, 3)

        # ── Step 6: Assemble results ──────────────────────────
        results = []
        for idx, (s_idx, e_idx, asp) in enumerate(sorted_spans):
            if idx >= MAX_OPS:
                break

            # Lấy target text từ char offsets
            char_s = int(offsets[s_idx][0])
            char_e = int(offsets[e_idx][1])
            target = text[char_s:char_e].strip()

            span_prob = torch.softmax(span_logits[0, idx], dim=-1)
            span_pred = int(torch.argmax(span_logits[0, idx]).item())

            results.append({
                "aspect"    : asp,
                "target"    : target,
                "sentiment" : SENT_NAME[span_pred],
                "sent_id"   : span_pred,
                "confidence": round(span_prob[span_pred].item(), 4),
            })

        return {
            "global_sentiment" : SENT_NAME[global_pred],
            "global_confidence": global_conf,
            "aspects"          : results,
        }

    @torch.no_grad()
    def predict_raw(self, text: str):
        """Trả về raw logits để debug."""
        result = self.predict_one(text)
        return result


# ══════════════════════════════════════════════════════════════════════════════
# EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

def evaluate(model, test_file: str):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    test_ds   = ABSADataset(test_file, tokenizer, MAX_LEN)
    test_dl   = DataLoader(test_ds, batch_size=BATCH_SIZE,
                            shuffle=False, num_workers=2, pin_memory=True)

    print(f"\n{'='*60}")
    print("  🧪 EVALUATION ON TEST SET")
    print(f"{'='*60}")
    print(f"  File   : {test_file}")
    print(f"  Samples: {len(test_ds):,}  |  Device: {DEVICE}")

    model.eval()
    pred_spans, gold_spans         = [], []
    all_sent_preds, all_sent_golds = [], []
    all_g_preds,    all_g_labels   = [], []

    with torch.no_grad():
        for b in tqdm(test_dl, desc="Evaluating"):
            ids        = b["input_ids"].to(DEVICE)
            mask       = b["attention_mask"].to(DEVICE)
            bio_lbl    = b["bio_labels"].to(DEVICE)
            span_masks = b["span_masks"].to(DEVICE)
            span_sents = b["span_sents"].to(DEVICE)
            g_lbl      = b["global_label"].to(DEVICE)

            # Eval: không truyền bio_labels → model decode CRF
            bio_em, _, bio_preds, span_log, g_log = model(
                ids, mask, span_masks, bio_labels=None
            )

            bio_golds = bio_lbl.cpu().tolist()
            mask_list = mask.cpu().tolist()
            for i, (p_seq, g_seq) in enumerate(zip(bio_preds, bio_golds)):
                vl = int(sum(mask_list[i]))
                pred_spans.append(extract_bio_spans(p_seq[:vl]))
                gold_spans.append(extract_bio_spans(g_seq[:vl]))

            if span_log is not None:
                for sp, sg in zip(
                    span_log.argmax(-1).cpu().view(-1).tolist(),
                    span_sents.cpu().view(-1).tolist(),
                ):
                    if sg != -100:
                        all_sent_preds.append(sp)
                        all_sent_golds.append(sg)

            all_g_preds.extend(g_log.argmax(-1).cpu().tolist())
            all_g_labels.extend(g_lbl.cpu().tolist())

    # ── Metrics ───────────────────────────────────────────────
    p, r, span_f1 = span_prf(pred_spans, gold_spans)
    sent_f1       = f1_score(all_sent_golds, all_sent_preds,
                              average="macro", zero_division=0)
    global_f1     = f1_score(all_g_labels, all_g_preds,
                              average="macro", zero_division=0)
    composite     = 0.4 * sent_f1 + 0.4 * span_f1 + 0.2 * global_f1

    print(f"\n{'─'*60}")
    print("  📊 RESULTS")
    print(f"{'─'*60}")

    print(f"\n  🏷️  Span F1  : {span_f1:.4f}  (P={p:.4f}  R={r:.4f})")
    print(f"\n  📌 Per-aspect Span F1:")
    print(f"     {'Aspect':<10} {'P':>7} {'R':>7} {'F1':>7}")
    for asp in ASPECTS:
        ap, ar, af = span_prf(pred_spans, gold_spans, aspect_filter=asp)
        bar = "█" * int(af * 20)
        print(f"     {asp:<10} {ap:>7.4f} {ar:>7.4f} {af:>7.4f}  {bar}")

    print(f"\n  😊 Sent F1  : {sent_f1:.4f}")
    for sid, sname in SENT_SHORT.items():
        pb = [1 if x == sid else 0 for x in all_sent_preds]
        gb = [1 if x == sid else 0 for x in all_sent_golds]
        f1 = f1_score(gb, pb, zero_division=0)
        bar = "█" * int(f1 * 20)
        print(f"     {sname:<10} F1={f1:.4f}  {bar}")

    print(f"\n  🌍 Global F1: {global_f1:.4f}")
    print("     " + classification_report(
        all_g_labels, all_g_preds,
        target_names=["Neg", "Pos", "Neu"],
        zero_division=0,
    ).replace("\n", "\n     "))

    print(f"  🔥 Composite: {composite:.4f}")
    print(f"     (0.4×sent + 0.4×span + 0.2×global)")
    print(f"{'─'*60}\n")

    return {"span_f1": span_f1, "sent_f1": sent_f1,
            "global_f1": global_f1, "composite": composite}


# ══════════════════════════════════════════════════════════════════════════════
# DEMO
# ══════════════════════════════════════════════════════════════════════════════

DEMO_CASES = [
    "áo rất xấu luôn thế mà giá còn hơi mắc nhưng nhân viên phục vụ rất tốt.",
    "App dùng hơi lag nhưng giá rẻ nên vẫn cho 5 sao, ship hơi lâu.",
    "Cái đồng hồ này đẹp tuyệt vời, nhân viên giao hàng rất nhanh.",
    "Giao hàng chậm, đóng gói bị rách, sản phẩm bình thường, không hài lòng.",
    "Shop phục vụ niềm nở, tư vấn nhiệt tình, chắc chắn sẽ ủng hộ lần sau.",
    "Ứng dụng bị lag nhiều quá, mỗi lần mở là đơ, không thể nào sử dụng được.",
    "Giá cả hợp lý, chất lượng sản phẩm tốt, ship nhanh, app mượt — rất hài lòng!",
]


def run_demo(engine: ABSAEngine, cases=None):
    if cases is None:
        cases = DEMO_CASES

    print(f"\n{'='*65}")
    print("  🎯 ABSA V3 — DEMO")
    print(f"{'='*65}")

    for i, text in enumerate(cases):
        result = engine.predict_one(text)

        print(f"\n  [{i+1}] {text}")
        print(f"  🌍 Global : {result['global_sentiment']}"
              f"  (conf={result['global_confidence']})")

        if not result["aspects"]:
            print(f"  ❌ Không detect được aspect nào.")
        else:
            for asp in result["aspects"]:
                conf = asp["confidence"]
                bar  = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
                print(f"  📌 [{asp['aspect']:<8}] {asp['sentiment']:<12}"
                      f"'{asp['target']}'  [{bar}] {conf:.2f}")

    print(f"\n{'='*65}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval",      action="store_true")
    parser.add_argument("--text",      type=str, default=None)
    parser.add_argument("--model",     type=str, default=MODEL_PATH)
    parser.add_argument("--test-file", type=str,
                        default="data/processed/test_data.jsonl")
    parser.add_argument("--no-demo",   action="store_true")
    args = parser.parse_args()

    print(f"\n🔧 Device : {DEVICE}")
    print(f"📦 Model  : {args.model}")

    engine = ABSAEngine(model_path=args.model)

    if args.text:
        result = engine.predict_one(args.text)
        print(f"\n{'='*60}")
        print(f"  Input  : {args.text}")
        print(f"  Global : {result['global_sentiment']}"
              f"  (conf={result['global_confidence']})")
        for asp in result["aspects"]:
            print(f"  📌 [{asp['aspect']:<8}] {asp['sentiment']:<12}"
                  f"'{asp['target']}'  conf={asp['confidence']:.4f}")
        print(f"{'='*60}\n")
        return

    if args.eval:
        evaluate(engine.model, args.test_file)

    if not args.no_demo:
        run_demo(engine)


if __name__ == "__main__":
    main()
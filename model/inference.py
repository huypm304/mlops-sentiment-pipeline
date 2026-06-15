"""
DEPRECATED: This module is kept for backward compatibility with backend/.

New code should use src.absa.inference instead:
    from src.absa.inference import load_model, predict_one

Key differences:
- src.absa.inference uses strict=True (required)
- src.absa.inference follows train/train.py forward logic exactly
- model_version = 'absa-v2b' in the new module
"""

import argparse
import json
import time
import unicodedata
from pathlib import Path
from contextlib import nullcontext

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
from torchcrf import CRF


ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENT_ID2LABEL = {
    0: "NEG",
    1: "POS",
    2: "NEU",
}
N_SENT = 3
MAX_OPS = 6


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def build_bio_labels():
    labels = ["O"]
    for aspect in ASPECTS:
        labels.extend([f"B-{aspect}", f"I-{aspect}"])
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}


BIO_LABELS, BIO_L2I, BIO_I2L = build_bio_labels()
N_BIO = len(BIO_LABELS)


def autocast_context(device):
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.float16)
    return nullcontext()


def extract_spans(seq):
    spans, start, cur = set(), None, None

    for idx, label_id in enumerate(seq):
        tag = BIO_I2L.get(int(label_id), "O")

        if tag.startswith("B-"):
            if start is not None:
                spans.add((start, idx - 1, cur))
            start, cur = idx, tag[2:]

        elif not (tag.startswith("I-") and cur == tag[2:]):
            if start is not None:
                spans.add((start, idx - 1, cur))
            start, cur = None, None

    if start is not None:
        spans.add((start, len(seq) - 1, cur))

    return spans


def compute_clause_aware_window(
    tmin,
    tmax,
    op_idx,
    span_token_lists,
    offsets,
    text,
    seq_len,
    max_context_window,
):
    low = max(tmin - max_context_window, 1)
    high = min(tmax + max_context_window, seq_len - 1)

    stop_tokens = {",", ".", "!", "?", ";", ":", "-", "~", "/"}
    boundary_tokens = {
        "nhưng", "tuy", "dù", "mà", "song", "còn",
        "tuy_nhiên", "thế_mà", "thế_nhưng"
    }

    if op_idx > 0:
        low = max(low, max(span_token_lists[op_idx - 1]) + 1)

    if op_idx < len(span_token_lists) - 1:
        high = min(high, min(span_token_lists[op_idx + 1]) - 1)

    text_l = text.lower()

    for cursor in range(tmin - 1, low - 1, -1):
        if 0 < cursor < seq_len:
            cs, ce = int(offsets[cursor][0]), int(offsets[cursor][1])
            token = text_l[cs:ce].strip()
            if token in stop_tokens | boundary_tokens:
                low = cursor + 1
                break

    for cursor in range(tmax + 1, high + 1):
        if 0 < cursor < seq_len:
            cs, ce = int(offsets[cursor][0]), int(offsets[cursor][1])
            token = text_l[cs:ce].strip()
            if token in stop_tokens | boundary_tokens:
                high = cursor - 1
                break

    return low, high


def compute_clause_position(span_start, span_end, offsets_row, text, seq_len):
    contrast_words = {
        "nhưng", "tuy", "dù", "mà", "song", "còn",
        "tuy_nhiên", "thế_nhưng"
    }

    text_l = text.lower()
    contrast_pos = None

    for idx in range(seq_len):
        cs = int(offsets_row[idx][0])
        ce = int(offsets_row[idx][1])
        token = text_l[cs:ce].strip()

        if token in contrast_words:
            contrast_pos = idx
            break

    if contrast_pos is None:
        return 0

    center = 0.5 * (span_start + span_end)
    return 1 if center < contrast_pos else 2


def build_predicted_span_inputs(
    decoded_seq,
    offsets_row,
    spec_mask_row,
    text,
    seq_len,
    max_ops,
    max_context_window,
    device,
):
    predicted_spans = sorted(extract_spans(decoded_seq[:seq_len]))

    total_len = int(offsets_row.shape[0])
    pred_span_mask = torch.zeros(max_ops, total_len, device=device)
    pred_span_aspect = torch.full(
        (max_ops,),
        len(ASPECTS),
        dtype=torch.long,
        device=device,
    )
    pred_clause_pos = torch.zeros(max_ops, dtype=torch.long, device=device)

    span_token_lists = [
        list(range(start, end + 1))
        for start, end, _ in predicted_spans[:max_ops]
    ]

    for span_idx, (start, end, aspect) in enumerate(predicted_spans[:max_ops]):
        if aspect in ASPECTS:
            pred_span_aspect[span_idx] = ASPECTS.index(aspect)

        pred_clause_pos[span_idx] = compute_clause_position(
            start,
            end,
            offsets_row,
            text,
            seq_len,
        )

        lo, hi = compute_clause_aware_window(
            start,
            end,
            span_idx,
            span_token_lists,
            offsets_row,
            text,
            seq_len,
            max_context_window,
        )

        for token_id in range(lo, hi + 1):
            if not bool(spec_mask_row[token_id]):
                pred_span_mask[span_idx, token_id] = 1.0

    return predicted_spans, pred_span_mask, pred_span_aspect, pred_clause_pos


CONTRAST_WORDS = {"nhưng", "tuy", "dù", "mà", "song", "còn"}


def extract_contrast_feature(sequence, offsets_batch, text_batch, mask):
    B, L, H = sequence.shape
    per_batch = []

    for b in range(B):
        text = text_batch[b].lower()
        offsets = offsets_batch[b]
        found = []

        for i in range(L):
            if bool(mask[b, i]):
                continue

            cs = int(offsets[i, 0])
            ce = int(offsets[i, 1])
            tok = text[cs:ce].strip()

            if tok in CONTRAST_WORDS:
                found.append(sequence[b, i])

        if found:
            summed = torch.stack(found, dim=0).sum(0)
            per_batch.append(F.normalize(summed, dim=0))
        else:
            per_batch.append(sequence.new_zeros(H))

    return torch.stack(per_batch, dim=0)


class ABSAModel(nn.Module):
    def __init__(self, model_name, max_ops):
        super().__init__()

        self.max_ops = max_ops
        self.backbone = AutoModel.from_pretrained(model_name)

        h = self.backbone.config.hidden_size

        self.dropout = nn.Dropout(0.3)

        self.bio_lstm = nn.LSTM(
            h,
            h // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.bio_head = nn.Linear(h, N_BIO)
        self.crf = CRF(N_BIO, batch_first=True)

        self.fc_pool = nn.Linear(h, 1)
        self.span_proj = nn.Linear(h * 4, h)

        self.cross_attn = nn.MultiheadAttention(
            h,
            num_heads=8,
            dropout=0.1,
            batch_first=True,
        )
        self.cross_attn_scale = nn.Parameter(torch.tensor(0.5))
        self.cross_attn_norm = nn.LayerNorm(h)

        self.span_self_attn = nn.MultiheadAttention(
            h,
            num_heads=4,
            dropout=0.1,
            batch_first=True,
        )

        self.aspect_embed = nn.Embedding(
            len(ASPECTS) + 1,
            h,
            padding_idx=len(ASPECTS),
        )
        self.aspect_scale = nn.Parameter(torch.tensor(0.8))

        self.clause_pos_embed = nn.Embedding(3, h)
        self.clause_pos_scale = nn.Parameter(torch.tensor(0.5))

        self.sent_head = nn.Sequential(
            nn.Linear(h, h),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(h // 2, N_SENT),
        )

        self.global_polarity_fusion = nn.Linear(h * 4, h)
        self.global_head = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(h, N_SENT),
        )

    def forward(
        self,
        ids,
        mask,
        span_mask=None,
        bio=None,
        cached_seq=None,
        span_aspect=None,
        span_clause_pos=None,
        offsets=None,
        texts=None,
    ):
        if cached_seq is None:
            seq = self.backbone(ids, attention_mask=mask).last_hidden_state
            seq = self.dropout(seq).float() 
        else:
            seq = cached_seq.float() 

        B = seq.shape[0]

        bio_feat, _ = self.bio_lstm(seq.float())
        emiss = self.bio_head(bio_feat)

        crf_loss = None
        if bio is not None:
            crf_loss = -self.crf(
                emiss.float(),
                bio,
                mask=mask.bool(),
                reduction="mean",
            )

        sent_logits = None
        span_features = None

        if span_mask is not None:
            B2, L, H = seq.shape
            M = span_mask.shape[1]

            exp_seq = seq.unsqueeze(1).expand(B2, M, L, H)

            scores = self.fc_pool(exp_seq).squeeze(-1)
            scores = scores.masked_fill(span_mask == 0, -1e4)

            attn = torch.softmax(scores, dim=-1).unsqueeze(-1)
            pooled = (exp_seq * attn).sum(dim=2)

            if offsets is not None and texts is not None:
                c_vec = extract_contrast_feature(
                    seq,
                    offsets,
                    texts,
                    ~mask.bool(),
                )
                pooled = pooled + 0.3 * c_vec.unsqueeze(1)

            # Final architecture: full CLS residual
            pooled = pooled + seq[:, 0].unsqueeze(1)

            if span_aspect is not None:
                pooled = pooled + self.aspect_scale * self.aspect_embed(span_aspect)

            if span_clause_pos is not None:
                pooled = pooled + self.clause_pos_scale * self.clause_pos_embed(span_clause_pos)

            span_active = span_mask > 0
            valid_span_slots = span_active.any(dim=-1, keepdim=True).float()
            span_padding_mask = ~span_active.any(dim=-1)

            pos_ids = torch.arange(L, device=seq.device).view(1, 1, L).expand(B2, M, L)

            start_pos = pos_ids.masked_fill(~span_active, L).min(dim=-1).values
            end_pos = pos_ids.masked_fill(~span_active, -1).max(dim=-1).values

            empty_spans = span_padding_mask
            start_pos = start_pos.masked_fill(empty_spans, 0).long()
            end_pos = end_pos.masked_fill(empty_spans, 0).long()

            batch_ids = torch.arange(B2, device=seq.device).view(B2, 1).expand(B2, M)

            start_repr = seq[batch_ids, start_pos] * valid_span_slots
            end_repr = seq[batch_ids, end_pos] * valid_span_slots

            boundary_feat = torch.cat(
                [pooled, start_repr, end_repr, start_repr * end_repr],
                dim=-1,
            )

            pooled = self.span_proj(boundary_feat)
            pooled = pooled * valid_span_slots

            cross_out, _ = self.cross_attn(
                pooled,
                seq,
                seq,
                key_padding_mask=~mask.bool(),
                need_weights=False,
            )

            pooled = self.cross_attn_norm(
                pooled + self.cross_attn_scale * cross_out * valid_span_slots
            )
            pooled = pooled * valid_span_slots

            # Safe self-attention for samples with no predicted span
            span_padding_mask_safe = span_padding_mask.clone()
            all_empty = span_padding_mask_safe.all(dim=1)
            if all_empty.any():
                span_padding_mask_safe[all_empty, 0] = False

            span_interact, _ = self.span_self_attn(
                pooled,
                pooled,
                pooled,
                key_padding_mask=span_padding_mask_safe,
                need_weights=False,
            )

            pooled = pooled + span_interact * valid_span_slots
            pooled = pooled * valid_span_slots

            span_features = pooled
            sent_logits = self.sent_head(pooled)

        cls_repr = seq[:, 0]
        h_dim = seq.shape[-1]

        if sent_logits is not None and span_features is not None:
            valid_spans = (span_mask.sum(dim=-1) > 0).float()

            # Same as final training: detach sentiment probs for global pooling
            span_probs = sent_logits.detach().softmax(-1)

            neg_w = span_probs[:, :, 0] * valid_spans
            pos_w = span_probs[:, :, 1] * valid_spans

            neg_pool = (
                span_features * neg_w.unsqueeze(-1)
            ).sum(1) / neg_w.sum(1, keepdim=True).clamp(min=1e-4)

            pos_pool = (
                span_features * pos_w.unsqueeze(-1)
            ).sum(1) / pos_w.sum(1, keepdim=True).clamp(min=1e-4)

            contra_vec = neg_pool - pos_pool

        else:
            neg_pool = pos_pool = contra_vec = seq.new_zeros(B, h_dim)

        fused = F.gelu(
            self.global_polarity_fusion(
                torch.cat([cls_repr, neg_pool, pos_pool, contra_vec], dim=-1)
            )
        )

        global_logits = self.global_head(fused)

        return crf_loss, emiss, sent_logits, global_logits, seq, span_features


def load_state_dict_safely(model, model_path, device):
    state = torch.load(model_path, map_location=device)

    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    # Handle DataParallel-style keys if needed
    new_state = {}
    for k, v in state.items():
        if k.startswith("module."):
            k = k[len("module."):]
        new_state[k] = v

    missing, unexpected = model.load_state_dict(new_state, strict=False)

    if missing:
        print("⚠️ Missing keys:", missing[:10], "..." if len(missing) > 10 else "")
    if unexpected:
        print("⚠️ Unexpected keys:", unexpected[:10], "..." if len(unexpected) > 10 else "")

    return model


@torch.inference_mode()
def infer_one(
    text,
    model,
    tokenizer,
    device,
    max_len=192,
    max_ops=6,
    max_context_window=25,
    span_conf_threshold=0.0,
):
    text = nfc(text)

    enc = tokenizer(
        text,
        max_length=max_len,
        padding="max_length",
        truncation=True,
        return_offsets_mapping=True,
        return_special_tokens_mask=True,
        return_tensors="pt",
    )

    ids = enc["input_ids"].to(device)
    mask = enc["attention_mask"].to(device)

    offsets = enc["offset_mapping"][0].to(device)
    spec_mask = enc["special_tokens_mask"][0].bool().to(device)

    with autocast_context(device):
        _, emiss, _, _, cached, _ = model(ids, mask)

    bio_pred = model.crf.decode(emiss.float(), mask=mask.bool())[0]
    seq_len = int(mask[0].sum().item())

    pred_spans, pred_span_mask, pred_span_aspect, pred_clause_pos = build_predicted_span_inputs(
        decoded_seq=bio_pred,
        offsets_row=offsets,
        spec_mask_row=spec_mask,
        text=text,
        seq_len=seq_len,
        max_ops=max_ops,
        max_context_window=max_context_window,
        device=device,
    )

    pred_span_mask_b = pred_span_mask.unsqueeze(0)
    pred_span_aspect_b = pred_span_aspect.unsqueeze(0)
    pred_clause_pos_b = pred_clause_pos.unsqueeze(0)
    offsets_b = offsets.unsqueeze(0)

    with autocast_context(device):
        _, _, sent_logits, global_logits, _, _ = model(
            ids,
            mask,
            span_mask=pred_span_mask_b,
            cached_seq=cached,
            span_aspect=pred_span_aspect_b,
            span_clause_pos=pred_clause_pos_b,
            offsets=offsets_b,
            texts=[text],
        )

    global_probs = torch.softmax(global_logits[0], dim=-1).detach().cpu()
    global_id = int(global_probs.argmax().item())

    results = []

    sorted_spans = sorted(pred_spans)[:max_ops]

    for slot_idx, (tok_s, tok_e, aspect) in enumerate(sorted_spans):
        sent_probs = torch.softmax(sent_logits[0, slot_idx], dim=-1).detach().cpu()
        sent_id = int(sent_probs.argmax().item())
        sent_conf = float(sent_probs[sent_id].item())

        if sent_conf < span_conf_threshold:
            continue

        char_s = int(offsets[tok_s][0].item())
        char_e = int(offsets[tok_e][1].item())
        raw_target = text[char_s:char_e]
        leading = len(raw_target) - len(raw_target.lstrip())
        target_text = raw_target.strip()

        char_s = char_s + leading
        char_e = char_s + len(target_text)

        results.append({
            "target": target_text,
            "aspect": aspect,
            "sentiment": SENT_ID2LABEL[sent_id],
            "sentiment_id": sent_id,
            "confidence": round(sent_conf, 4),
            "start": char_s,
            "end": char_e,
            "probs": {
                "NEG": round(float(sent_probs[0].item()), 4),
                "POS": round(float(sent_probs[1].item()), 4),
                "NEU": round(float(sent_probs[2].item()), 4),
            },
        })

    output = {
        "text": text,
        "opinions": results,
        "global_sentiment": SENT_ID2LABEL[global_id],
        "global_sentiment_id": global_id,
        "global_probs": {
            "NEG": round(float(global_probs[0].item()), 4),
            "POS": round(float(global_probs[1].item()), 4),
            "NEU": round(float(global_probs[2].item()), 4),
        },
    }

    return output


SENT_API_MAP = {
    "NEG": "negative",
    "POS": "positive",
    "NEU": "neutral",
    "Negative": "negative",
    "Positive": "positive",
    "Neutral": "neutral",
}


def _load_run_config(model_dir: Path) -> dict:
    for name in ("config.json", "run_config.json"):
        path = model_dir / name
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_model(model_dir: Path, device: str | None = None) -> dict:
    """Load checkpoint bundle for API inference."""
    from model.postprocess import PostprocessConfig

    model_dir = Path(model_dir)
    config = _load_run_config(model_dir)
    model_name = config.get("model_name", "Fsoft-AIC/videberta-base")
    max_len = int(config.get("max_len", 192))
    max_ops = int(config.get("max_ops", MAX_OPS))
    max_context_window = int(config.get("max_context_window", 25))

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = ABSAModel(model_name, max_ops).to(dev)
    checkpoint = model_dir / "best_model.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")
    model = load_state_dict_safely(model, checkpoint, dev)
    model.eval()

    pp_cfg = PostprocessConfig()
    pp_path = model_dir / "postprocess_config.json"
    if pp_path.is_file():
        pp_cfg = PostprocessConfig.from_dict(json.loads(pp_path.read_text(encoding="utf-8")))

    return {
        "model": model,
        "tokenizer": tokenizer,
        "device": dev,
        "max_len": max_len,
        "max_ops": max_ops,
        "max_context_window": max_context_window,
        "postprocess_config": pp_cfg,
        "model_version": "absa-v1",
    }


def predict_text(text: str, bundle: dict) -> dict:
    """Run inference and return API-friendly payload."""
    from model.postprocess import postprocess_predictions

    started = time.perf_counter()
    raw = infer_one(
        text,
        bundle["model"],
        bundle["tokenizer"],
        bundle["device"],
        max_len=bundle["max_len"],
        max_ops=bundle["max_ops"],
        max_context_window=bundle["max_context_window"],
    )

    opinions_for_pp = []
    for opinion in raw["opinions"]:
        probs = opinion.get("probs") or {}
        vec = [
            float(probs.get("NEG", 0.0)),
            float(probs.get("POS", 0.0)),
            float(probs.get("NEU", 0.0)),
        ]
        sent_key = str(opinion.get("sentiment", "NEU"))
        sent_id = {"NEG": 0, "POS": 1, "NEU": 2}.get(sent_key, 2)
        opinions_for_pp.append({
            **opinion,
            "raw_confidence": float(opinion.get("confidence", 0.0)),
            "_probs": vec,
            "_sent_id": sent_id,
        })

    glob_probs = torch.tensor([
        float(raw["global_probs"]["NEG"]),
        float(raw["global_probs"]["POS"]),
        float(raw["global_probs"]["NEU"]),
    ])
    refined, glob_id, glob_conf = postprocess_predictions(
        opinions_for_pp,
        glob_probs,
        bundle.get("postprocess_config"),
    )

    api_opinions = []
    for opinion in refined:
        sentiment = SENT_API_MAP.get(str(opinion.get("sentiment", "NEU")), "neutral")
        calibrated = float(opinion.get("confidence", 0.0))
        raw_conf = float(opinion.get("raw_confidence", calibrated))
        api_opinions.append({
            "target": opinion["target"],
            "aspect": opinion["aspect"],
            "sentiment": sentiment,
            "confidence": calibrated,
            "raw_confidence": raw_conf,
            "calibrated_confidence": calibrated,
            "start": opinion.get("start"),
            "end": opinion.get("end"),
        })

    latency_ms = int((time.perf_counter() - started) * 1000)
    global_sentiment = SENT_API_MAP.get(SENT_ID2LABEL.get(glob_id, "NEU"), "neutral")
    raw_global_conf = float(max(raw["global_probs"].values()))

    return {
        "opinions": api_opinions,
        "global_sentiment": global_sentiment,
        "global_confidence": round(float(glob_conf), 4),
        "global_raw_confidence": round(raw_global_conf, 4),
        "latency_ms": latency_ms,
        "model_version": bundle.get("model_version", "absa-v1"),
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-path",
        type=Path,
        required=True,
        help="Path to best_model.pt",
    )
    parser.add_argument(
        "--model-name",
        default="Fsoft-AIC/videberta-base",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Single input text",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Optional .txt file, one review per line",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional output jsonl path",
    )
    parser.add_argument("--max-len", type=int, default=192)
    parser.add_argument("--max-ops", type=int, default=6)
    parser.add_argument("--max-context-window", type=int, default=25)

    args = parser.parse_args()

    if args.text is None and args.input_file is None:
        raise ValueError("Please provide either --text or --input-file")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = ABSAModel(args.model_name, args.max_ops).to(device)
    model = load_state_dict_safely(model, args.model_path, device)
    model.eval()

    if args.text is not None:
        output = infer_one(
            text=args.text,
            model=model,
            tokenizer=tokenizer,
            device=device,
            max_len=args.max_len,
            max_ops=args.max_ops,
            max_context_window=args.max_context_window,
        )
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    outputs = []

    with open(args.input_file, encoding="utf-8") as f:
        texts = [line.strip() for line in f if line.strip()]

    for text in texts:
        output = infer_one(
            text=text,
            model=model,
            tokenizer=tokenizer,
            device=device,
            max_len=args.max_len,
            max_ops=args.max_ops,
            max_context_window=args.max_context_window,
        )
        outputs.append(output)

    if args.output_file is not None:
        with open(args.output_file, "w", encoding="utf-8") as f:
            for item in outputs:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Saved to {args.output_file}")
    else:
        print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
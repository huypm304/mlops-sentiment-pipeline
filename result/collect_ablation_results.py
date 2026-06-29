"""
Chạy cell này sau khi tất cả ablation xong để in bảng kết quả.
Copy cell này vào Kaggle notebook.
"""
import csv
import json
import os

CONFIGS = [
    ("A0 Full model",        "ablation_a0_full",              "a0_full"),
    ("A1 −BiLSTM",           "ablation_a1_no_bilstm",         "a1_no_bilstm"),
    ("A2 −CRF (softmax)",    "ablation_a2_no_crf",            "a2_no_crf"),
    ("A3 −CrossAttention",   "ablation_a3_no_cross_attn",     "a3_no_cross_attn"),
    ("A4 −ContraVec",        "ablation_a4_no_contra_vec",     "a4_no_contra_vec"),
    ("A5 −ContrastLoss",     "ablation_a5_no_contrast_loss",  "a5_no_contrast_loss"),
]

METRICS = [
    "tas_strict_f1", "tas_relaxed_f1", "span_f1",
    "sent_matched_f1", "global_f1",
    "span_f1_Electronics",
]

WORKING = "/kaggle/working"


def find_artifact(folder, new_name, old_name=None):
    candidates = [new_name]
    if old_name:
        candidates.append(old_name)
    for name in candidates:
        path = os.path.join(WORKING, folder, name)
        if os.path.exists(path):
            return path
    return None


HEADER = f"{'Config':<26} | " + " | ".join(f"{m:<20}" for m in METRICS)
print(HEADER)
print("-" * len(HEADER))

baseline_vals = {}
all_summaries = {}

for label, folder, slug in CONFIGS:
    log_path = find_artifact(folder, f"{slug}_train_log.csv", "train_log.csv")
    summary_path = find_artifact(folder, f"{slug}_summary.json")

    if summary_path:
        with open(summary_path, encoding="utf-8") as f:
            all_summaries[slug] = json.load(f)

    if not log_path:
        print(f"{label:<26} | NOT FOUND")
        continue

    rows = list(csv.DictReader(open(log_path, encoding="utf-8")))
    best = max(rows, key=lambda r: float(r["tas_relaxed_f1"]))
    vals = {m: float(best[m]) for m in METRICS}

    if label.startswith("A0"):
        baseline_vals = vals

    parts = []
    for m in METRICS:
        v = vals[m]
        base = baseline_vals.get(m, v)
        delta = v - base
        delta_str = f"({delta:+.4f})" if delta != 0 else "         "
        parts.append(f"{v:.4f} {delta_str:<12}")

    print(f"{label:<26} | " + " | ".join(parts))
    print(f"  -> best epoch {int(float(best['epoch']))}, "
          f"TAS-Relaxed={vals['tas_relaxed_f1']:.4f}, log={os.path.basename(log_path)}")

print()
print("Note: Δ = config − A0 Full. Negative = ablated component helped.")
print("Logs: {slug}_train_log.csv | Models: {slug}_best_model.pt | Summary: {slug}_summary.json")

if all_summaries:
    out = os.path.join(WORKING, "ablation_results_all.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"ablation_results": all_summaries}, f, ensure_ascii=False, indent=2)
    print(f"\nMerged summary → {out}")

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


SENTIMENT_MAP = {
    0: "Neg",
    1: "Pos",
    2: "Neu",
    "0": "Neg",
    "1": "Pos",
    "2": "Neu",
    "neg": "Neg",
    "negative": "Neg",
    "pos": "Pos",
    "positive": "Pos",
    "neu": "Neu",
    "neutral": "Neu",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze manual ABSA test outputs and explain likely failure reasons."
    )
    parser.add_argument("--train-file", required=True)
    parser.add_argument("--gold-file", required=True)
    parser.add_argument("--pred-file", required=True)
    parser.add_argument("--summary-out", default="model/manual_eval_summary.md")
    parser.add_argument("--details-out", default="model/manual_eval_details.jsonl")
    return parser.parse_args()


def normalize_text(value):
    value = unicodedata.normalize("NFC", str(value or "")).lower().strip()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_sentiment(value):
    return SENTIMENT_MAP.get(value, SENTIMENT_MAP.get(str(value).lower(), str(value)))


def normalize_opinion(opinion):
    return {
        "aspect": str(opinion.get("aspect", "")).strip(),
        "target": str(opinion.get("target", "")).strip(),
        "target_norm": normalize_text(opinion.get("target", "")),
        "sentiment": normalize_sentiment(opinion.get("sentiment", "")),
    }


def check_target_surface(text, target):
    raw_text = str(text or "")
    raw_target = str(target or "").strip()
    if not raw_target:
        return None

    norm_text = normalize_text(raw_text)
    norm_target = normalize_text(raw_target)
    raw_in_text = raw_target in raw_text
    norm_in_text = norm_target in norm_text if norm_target else False

    if raw_in_text:
        return None
    if norm_in_text:
        return {
            "type": "surface_form_mismatch",
            "target": raw_target,
            "why": "target khop sau khi normalize, nhung khong khop exact raw text; can dung normalized eval va khong highlight bang target string",
        }
    return {
        "type": "raw_text_mismatch",
        "target": raw_target,
        "why": "target khong xuat hien trong raw text ngay ca sau khi normalize; can kiem tra lai offset/annotation",
    }


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            record.setdefault("line_no", line_no)
            rows.append(record)
    return rows


def iter_opinions(record):
    opinions = record.get("opinions")
    if opinions is None:
        opinions = record.get("aspects", [])
    return [normalize_opinion(op) for op in opinions]


def build_train_stats(train_file):
    target_counter = Counter()
    aspect_target_counter = Counter()
    token_counter = Counter()

    for record in load_jsonl(train_file):
        for opinion in record.get("opinions", []):
            norm_target = normalize_text(opinion.get("target", ""))
            aspect = str(opinion.get("aspect", "")).strip()
            if not norm_target:
                continue
            target_counter[norm_target] += 1
            aspect_target_counter[(aspect, norm_target)] += 1
            for token in norm_target.split():
                token_counter[token] += 1

    return {
        "targets": target_counter,
        "aspect_targets": aspect_target_counter,
        "tokens": token_counter,
    }


def target_similarity(left, right):
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    if left in right or right in left:
        return 0.8

    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return overlap / union if union else 0.0


def align_predictions(gold_ops, pred_ops):
    unmatched_pred = set(range(len(pred_ops)))
    aligned = []

    for gold in gold_ops:
        best_idx = None
        best_score = -1.0
        for pred_idx in list(unmatched_pred):
            pred = pred_ops[pred_idx]
            aspect_bonus = 1.0 if pred["aspect"] == gold["aspect"] else 0.0
            score = (2.0 * aspect_bonus) + target_similarity(gold["target_norm"], pred["target_norm"])
            if score > best_score:
                best_score = score
                best_idx = pred_idx

        if best_idx is None:
            aligned.append((gold, None))
            continue

        pred = pred_ops[best_idx]
        same_aspect = pred["aspect"] == gold["aspect"]
        same_target = target_similarity(gold["target_norm"], pred["target_norm"]) >= 0.6
        if same_aspect or same_target:
            aligned.append((gold, pred))
            unmatched_pred.discard(best_idx)
        else:
            aligned.append((gold, None))

    extras = [pred_ops[idx] for idx in sorted(unmatched_pred)]
    return aligned, extras


def explain_unseen_target(gold, train_stats):
    target_norm = gold["target_norm"]
    if not target_norm:
        return None

    if target_norm not in train_stats["targets"]:
        aspect_key = (gold["aspect"], target_norm)
        if aspect_key not in train_stats["aspect_targets"]:
            missing_tokens = [token for token in target_norm.split() if token not in train_stats["tokens"]]
            if missing_tokens:
                return f"target ngoai train, token moi: {', '.join(missing_tokens)}"
            return "target ngoai train"
    return None


def analyze_record(record_id, text, gold_ops, pred_ops, train_stats):
    aligned, extras = align_predictions(gold_ops, pred_ops)
    issues = []

    gold_sentiments = {op["sentiment"] for op in gold_ops if op["sentiment"] in {"Neg", "Pos", "Neu"}}
    pred_sentiments = {op["sentiment"] for op in pred_ops if op["sentiment"] in {"Neg", "Pos", "Neu"}}

    for gold in gold_ops:
        surface_issue = check_target_surface(text, gold["target"])
        if surface_issue is not None:
            issues.append(surface_issue)

    for gold, pred in aligned:
        unseen_reason = explain_unseen_target(gold, train_stats)
        if pred is None:
            detail = {
                "type": "missing_aspect",
                "aspect": gold["aspect"],
                "target": gold["target"],
                "sentiment": gold["sentiment"],
                "why": unseen_reason or "model khong bat duoc aspect/target nay",
            }
            issues.append(detail)
            continue

        if pred["aspect"] != gold["aspect"]:
            issues.append({
                "type": "wrong_aspect",
                "gold_aspect": gold["aspect"],
                "pred_aspect": pred["aspect"],
                "target": gold["target"],
                "why": unseen_reason or "target co ve da bat duoc nhung gan nham aspect",
            })
            continue

        sim = target_similarity(gold["target_norm"], pred["target_norm"])
        if sim < 0.6:
            issues.append({
                "type": "wrong_target",
                "aspect": gold["aspect"],
                "gold_target": gold["target"],
                "pred_target": pred["target"],
                "why": unseen_reason or "model bat dung aspect nhung lech target span",
            })
            continue

        if pred["sentiment"] != gold["sentiment"]:
            issues.append({
                "type": "wrong_sentiment",
                "aspect": gold["aspect"],
                "target": gold["target"],
                "gold_sentiment": gold["sentiment"],
                "pred_sentiment": pred["sentiment"],
                "why": unseen_reason or "aspect dung nhung sentiment cua aspect bi sai",
            })

    for extra in extras:
        issues.append({
            "type": "extra_prediction",
            "aspect": extra["aspect"],
            "target": extra["target"],
            "sentiment": extra["sentiment"],
            "why": "he thong du doan them aspect/target khong co trong gold",
        })

    if len(gold_ops) >= 2 and len(gold_sentiments) >= 2:
        if len(pred_sentiments) <= 1:
            issues.append({
                "type": "contrast_collapse",
                "why": "cau nhieu aspect doi lap nhung du doan bi gom ve cung mot sentiment",
                "gold_sentiments": sorted(gold_sentiments),
                "pred_sentiments": sorted(pred_sentiments),
            })

    return {
        "id": record_id,
        "text": text,
        "gold": gold_ops,
        "pred": pred_ops,
        "issues": issues,
    }


def build_summary(results, train_stats, summary_path):
    total = len(results)
    with_issues = [result for result in results if result["issues"]]
    issue_counter = Counter(issue["type"] for result in with_issues for issue in result["issues"])
    unseen_counter = Counter()

    for result in with_issues:
        for issue in result["issues"]:
            why = issue.get("why", "")
            if "ngoai train" in why:
                target = issue.get("target") or issue.get("gold_target")
                if target:
                    unseen_counter[target] += 1

    lines = [
        "# Manual Error Analysis",
        f"- Total cases: {total}",
        f"- Cases with issues: {len(with_issues)}",
        "",
        "## Comparison Policy",
        "- Target matching uses normalized text: lowercase, collapse spaces, and convert `_` to space.",
        "- This avoids losing F1 unfairly in cases like `nhan_vien` vs `nhan vien`.",
        "- `surface_form_mismatch` means the target is semantically matchable after normalization but unsafe for exact-string frontend highlight.",
        "- `raw_text_mismatch` means the target still does not align with raw text after normalization and should be reviewed as potential offset/annotation error.",
        "",
        "## Issue Counts",
        "| Type | Count |",
        "|---|---:|",
    ]

    for issue_type, count in sorted(issue_counter.items()):
        lines.append(f"| {issue_type} | {count} |")

    lines.extend([
        "",
        "## Unseen Targets Suspected",
    ])

    if unseen_counter:
        for target, count in unseen_counter.most_common(20):
            lines.append(f"- {target}: {count}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Sample Failures",
    ])

    for result in with_issues[:10]:
        issue_bits = "; ".join(
            f"{issue['type']}: {issue.get('why', '')}" for issue in result["issues"][:3]
        )
        lines.append(f"- id={result['id']} | text=\"{result['text']}\" | {issue_bits}")

    Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    train_stats = build_train_stats(args.train_file)
    gold_records = load_jsonl(args.gold_file)
    pred_records = load_jsonl(args.pred_file)

    pred_by_id = {}
    pred_by_text = {}
    for record in pred_records:
        if "id" in record:
            pred_by_id[str(record["id"])] = record
        pred_by_text[normalize_text(record.get("text", ""))] = record

    results = []
    for gold in gold_records:
        record_id = str(gold.get("id", gold.get("line_no")))
        text = gold.get("text", "")
        pred = pred_by_id.get(record_id) or pred_by_text.get(normalize_text(text), {})
        result = analyze_record(
            record_id=record_id,
            text=text,
            gold_ops=iter_opinions(gold),
            pred_ops=iter_opinions(pred),
            train_stats=train_stats,
        )
        results.append(result)

    build_summary(results, train_stats, args.summary_out)

    with open(args.details_out, "w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"Wrote summary: {args.summary_out}")
    print(f"Wrote details: {args.details_out}")


if __name__ == "__main__":
    main()
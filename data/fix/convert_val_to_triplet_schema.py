#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

VAL_FILE = Path("data/processed/val_data.jsonl")
BACKUP_FILE = Path("data/processed/val_data.legacy_opinions.backup.jsonl")

NEG_CUES = {
    "tệ", "xấu", "kém", "lỗi", "lag", "đơ", "giật", "chậm", "lâu", "trễ", "đắt", "mắc", "rách", "bẩn", "hôi",
    "không", "chưa", "thiếu", "sai", "dơ", "chát", "tồi", "dở", "nhỏ", "chật", "rộng", "mỏng",
}
POS_CUES = {
    "tốt", "đẹp", "ổn", "ok", "xịn", "ưng", "ngon", "rẻ", "tuyệt", "nhanh", "hài_lòng", "chuẩn", "mượt", "chắc",
}
NEU_CUES = {
    "bình_thường", "tạm", "được", "tạm_ổn", "ổn_định", "vừa", "tương_đối",
}
STOPWORDS = {
    "và", "hay", "hoặc", "thì", "mà", "là", "có", "được", "của", "cho", "với", "như", "vì", "nên", "đã", "rồi",
}


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\n", " ")).strip()


def norm_key(s: str) -> str:
    return normalize(s).lower().replace("_", " ")


def find_target_span(text: str, target: str, start: int, end: int) -> tuple[int, int, str]:
    text_len = len(text)
    start = max(0, min(start, text_len))
    end = max(start, min(end, text_len))
    target_clean = target.strip()

    if start < end and text[start:end] == target_clean:
        return start, end, target_clean

    # Try normalized exact search.
    positions = [m.start() for m in re.finditer(re.escape(target_clean), text)]
    if positions:
        best = min(positions, key=lambda p: abs(p - start))
        return best, best + len(target_clean), target_clean

    # As fallback use existing span text.
    fallback = text[start:end].strip()
    if fallback:
        return start, end, fallback

    # Last fallback: locate first token-looking chunk.
    m = re.search(r"\S+", text)
    if m:
        return m.start(), m.end(), text[m.start():m.end()]

    return 0, 0, ""


def iter_tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\S+", text)]


def choose_opinion(text: str, sentiment: int, target_span: tuple[int, int]) -> tuple[str, int, int]:
    t_start, t_end = target_span
    tokens = iter_tokens(text)
    if not tokens:
        return "", -1, -1

    if sentiment == 0:
        lexicon = NEG_CUES
    elif sentiment == 1:
        lexicon = POS_CUES
    else:
        lexicon = NEU_CUES

    candidates = []
    for tok, s, e in tokens:
        if not (e <= t_start or s >= t_end):
            continue
        key = norm_key(tok)
        if key in lexicon:
            candidates.append((tok, s, e))

    # Prefer sentiment cue nearest to target.
    if candidates:
        target_mid = (t_start + t_end) / 2.0
        tok, s, e = min(candidates, key=lambda item: abs(((item[1] + item[2]) / 2.0) - target_mid))
        return tok, s, e

    # Fallback: nearest non-stopword token around target span.
    non_stop = []
    for tok, s, e in tokens:
        if not (e <= t_start or s >= t_end):
            continue
        key = norm_key(tok)
        if len(key) < 2 or key in STOPWORDS:
            continue
        non_stop.append((tok, s, e))

    if non_stop:
        target_mid = (t_start + t_end) / 2.0
        tok, s, e = min(non_stop, key=lambda item: abs(((item[1] + item[2]) / 2.0) - target_mid))
        return tok, s, e

    return "", -1, -1


def convert_record(record: dict) -> dict:
    text = record.get("text", "")
    triplets = []

    for op in record.get("opinions", []):
        target = str(op.get("target", ""))
        start = int(op.get("start", -1))
        end = int(op.get("end", -1))
        aspect = op.get("aspect")
        sentiment = op.get("sentiment")

        t_start, t_end, target_fixed = find_target_span(text, target, start, end)
        opinion, o_start, o_end = choose_opinion(text, sentiment, (t_start, t_end))

        # If we still cannot detect a separate opinion, fallback to target for schema completeness.
        if not opinion:
            opinion = target_fixed
            o_start, o_end = t_start, t_end

        triplets.append(
            {
                "aspect": aspect,
                "target": target_fixed,
                "target_span": [t_start, t_end],
                "opinion": opinion,
                "opinion_span": [o_start, o_end],
                "aspect_opinion_pair": f"{target_fixed} {opinion}".strip(),
                "sentiment": sentiment,
            }
        )

    return {"text": text, "triplets": triplets}


def main() -> None:
    if not VAL_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {VAL_FILE}")

    if not BACKUP_FILE.exists():
        shutil.copy2(VAL_FILE, BACKUP_FILE)

    converted = []
    total = 0
    with VAL_FILE.open(encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            converted.append(convert_record(json.loads(raw)))

    with VAL_FILE.open("w", encoding="utf-8") as handle:
        for row in converted:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "records_converted": total,
                "output": str(VAL_FILE),
                "backup": str(BACKUP_FILE),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

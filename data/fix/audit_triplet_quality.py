import json
import re
from collections import defaultdict

# Configuration
INPUT_FILE = "/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/train_final_v9_aste_selective_merged.jsonl"
OUTPUT_ERRORS = "/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/audit_errors.jsonl"
OUTPUT_CLEAN = "/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/triplet_data_clean.jsonl"

# Validation rules
VALID_ASPECTS = {"Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"}
VALID_SENTIMENTS = {0, 1, 2}

# Heuristic signals
NEG_SIGNALS = {"xấu", "tệ", "lag", "chậm", "mắc", "đắt", "lỗi", "kém", "hỏng", "yếu", "mệt", 
               "thất_vọng", "tệ_hại", "dở", "hỏng", "rách", "bẩn", "hôi"}
POS_SIGNALS = {"tốt", "đẹp", "nhanh", "ổn", "ok", "xịn", "ưng", "ngon", "rẻ", "tuyệt", 
               "vừa", "thích", "hài_lòng", "tốc_độ", "mịn", "mượt", "chắc", "chuẩn"}
NEU_SIGNALS = {"bình_thường", "tạm", "được", "trung_bình", "ổn_định"}

GENERIC_TARGETS = {"shop", "hàng", "sản_phẩm", "đồ", "cái", "thứ", "này"}
STOP_WORDS = {"và", "hay", "hoặc", "rồi", "thì", "mà", "là", "có", "được"}

NEG_NEGATORS = {"không", "chưa", "chẳng", "k", "ko"}

def normalize(text):
    """Normalize text for comparison: lowercase, replace _ with space"""
    return text.lower().replace("_", " ").strip()

def extract_text_span(text, start, end):
    """Extract and normalize text span"""
    return normalize(text[start:end])

def check_offset_match(text, span, target_str):
    """Check if span matches target after normalization"""
    if span[0] < 0 or span[1] > len(text) or span[0] > span[1]:
        return False
    extracted = extract_text_span(text, span[0], span[1])
    target_norm = normalize(target_str)
    return extracted == target_norm

def check_overlap(span1, span2):
    """Check if two spans overlap"""
    return not (span1[1] <= span2[0] or span2[1] <= span1[0])

def check_sentiment_opinion_mismatch(opinion, sentiment):
    """Check if opinion word contradicts sentiment (W1)"""
    opinion_norm = normalize(opinion)
    
    # Check for negators in context
    has_negator = any(neg in opinion_norm for neg in NEG_NEGATORS)
    
    # Split opinion into words
    words = opinion_norm.split()
    opinion_words = set(words)
    
    # Check signals
    has_neg_signal = bool(opinion_words & NEG_SIGNALS)
    has_pos_signal = bool(opinion_words & POS_SIGNALS)
    has_neu_signal = bool(opinion_words & NEU_SIGNALS)
    
    # Logic:
    # - If has negator, don't flag (negation flips sentiment)
    # - If Pos signal but sentiment=0 (Neg) → flag
    # - If Neg signal but sentiment=1 (Pos) → flag
    # - If Neu signal but sentiment=1 (Pos) → flag
    
    if has_negator:
        return False
    
    if has_pos_signal and sentiment == 0:
        return True
    if has_neg_signal and sentiment == 1:
        return True
    if has_neu_signal and sentiment == 1:
        return True
    
    return False

def check_strong_opinion_vs_neu(opinion, sentiment):
    """Check if Neu sentiment but strong opinion signal (W4)"""
    if sentiment != 2:  # Not Neu
        return False
    
    opinion_norm = normalize(opinion)
    words = set(opinion_norm.split())
    
    has_neg_signal = bool(words & NEG_SIGNALS)
    has_pos_signal = bool(words & POS_SIGNALS)
    
    # Flag if has strong signal but marked as Neu
    # Exception: "tạm", "bình_thường", "ổn" are valid Neu
    valid_neu = {"tạm", "bình_thường", "ổn", "tạm_được", "ổn_định", "được"}
    if opinion_norm in valid_neu or all(w in valid_neu for w in words):
        return False
    
    return has_neg_signal or has_pos_signal

def check_aspect_opinion_pair(target, opinion, aspect_opinion_pair):
    """Check if aspect_opinion_pair matches target + " " + opinion (W5)"""
    expected = normalize(target) + " " + normalize(opinion)
    actual = normalize(aspect_opinion_pair)
    return expected != actual

def check_opinion_quality(opinion):
    """Check if opinion is too short or stop word (W6)"""
    opinion_clean = normalize(opinion)
    if len(opinion_clean) < 2:
        return True
    if opinion_clean in STOP_WORDS:
        return True
    return False

def audit_record(record, line_no):
    """Audit a single record, return errors list and is_clean flag"""
    errors = []
    text = record.get("text", "")
    triplets = record.get("triplets", [])
    
    # Check for hard errors (C1-C6)
    has_hard_error = False
    
    if not isinstance(triplets, list):
        return [{"code": "C_FORMAT", "detail": "triplets is not a list"}], True
    
    # Track for C6 (duplicates)
    seen_triplets = set()
    
    for triplet_idx, triplet in enumerate(triplets):
        triplet_errors = []
        
        # C1: Offset mismatch target
        if "target_span" in triplet and "target" in triplet:
            if not check_offset_match(text, triplet["target_span"], triplet["target"]):
                triplet_errors.append(("C1", f"target_span mismatch: expected '{triplet['target']}'"))
                has_hard_error = True
        
        # C2: Offset mismatch opinion
        if "opinion_span" in triplet and "opinion" in triplet:
            if not check_offset_match(text, triplet["opinion_span"], triplet["opinion"]):
                triplet_errors.append(("C2", f"opinion_span mismatch: expected '{triplet['opinion']}'"))
                has_hard_error = True
        
        # C3: Invalid aspect
        if "aspect" in triplet:
            if triplet["aspect"] not in VALID_ASPECTS:
                triplet_errors.append(("C3", f"invalid aspect '{triplet['aspect']}'"))
                has_hard_error = True
        
        # C4: Invalid sentiment
        if "sentiment" in triplet:
            if triplet["sentiment"] not in VALID_SENTIMENTS:
                triplet_errors.append(("C4", f"invalid sentiment {triplet['sentiment']}"))
                has_hard_error = True
        
        # C5: Target-opinion overlap
        if "target_span" in triplet and "opinion_span" in triplet:
            if check_overlap(triplet["target_span"], triplet["opinion_span"]):
                triplet_errors.append(("C5", "target and opinion spans overlap"))
                has_hard_error = True
        
        # C6: Duplicate triplet (check later after collecting all)
        triplet_key = (
            triplet.get("aspect"), 
            tuple(triplet.get("target_span", [])),
            tuple(triplet.get("opinion_span", []))
        )
        if triplet_key in seen_triplets:
            triplet_errors.append(("C6", "duplicate triplet"))
            has_hard_error = True
        seen_triplets.add(triplet_key)
        
        # Add triplet errors to main errors list
        for error_code, detail in triplet_errors:
            errors.append({
                "code": error_code,
                "triplet_idx": triplet_idx,
                "detail": detail
            })
        
        # Soft warnings (W1-W6)
        # W1: Sentiment vs opinion mismatch
        if "opinion" in triplet and "sentiment" in triplet:
            if check_sentiment_opinion_mismatch(triplet["opinion"], triplet["sentiment"]):
                errors.append({
                    "code": "W1",
                    "triplet_idx": triplet_idx,
                    "detail": f"opinion '{triplet['opinion']}' contradicts sentiment {triplet['sentiment']}"
                })
        
        # W2: Opinion fuzzy mismatch (similar to C2 but softer)
        # Skip - covered by C2
        
        # W4: Neu but strong opinion
        if "opinion" in triplet and "sentiment" in triplet:
            if check_strong_opinion_vs_neu(triplet["opinion"], triplet["sentiment"]):
                errors.append({
                    "code": "W4",
                    "triplet_idx": triplet_idx,
                    "detail": f"sentiment is Neu but opinion '{triplet['opinion']}' has strong signal"
                })
        
        # W5: Aspect-opinion pair mismatch
        if all(k in triplet for k in ["target", "opinion", "aspect_opinion_pair"]):
            if check_aspect_opinion_pair(triplet["target"], triplet["opinion"], triplet["aspect_opinion_pair"]):
                errors.append({
                    "code": "W5",
                    "triplet_idx": triplet_idx,
                    "detail": f"aspect_opinion_pair mismatch"
                })
        
        # W6: Opinion too short or stop word
        if "opinion" in triplet:
            if check_opinion_quality(triplet["opinion"]):
                errors.append({
                    "code": "W6",
                    "triplet_idx": triplet_idx,
                    "detail": f"opinion '{triplet['opinion']}' is too short or stop word"
                })
    
    # W3: Generic target with only 1 triplet
    if len(triplets) == 1 and triplets:
        target = triplets[0].get("target", "")
        if normalize(target) in GENERIC_TARGETS:
            errors.append({
                "code": "W3",
                "triplet_idx": 0,
                "detail": f"generic target '{target}' with only 1 triplet"
            })
    
    is_clean = not has_hard_error
    return errors, is_clean

def main():
    print("🔍 Starting audit of train_final_v9_aste_selective_merged.jsonl...")
    
    error_counts = defaultdict(int)
    hard_errors_by_code = defaultdict(int)
    all_errors = []
    clean_records = []
    records_with_errors = []
    
    total_records = 0
    total_triplets = 0
    total_hard_errors = 0
    total_soft_warnings = 0
    clean_record_count = 0
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    total_records += 1
                    total_triplets += len(record.get("triplets", []))
                    
                    errors, is_clean = audit_record(record, line_no)
                    
                    if is_clean:
                        clean_record_count += 1
                        clean_records.append(record)
                    else:
                        records_with_errors.append(record)
                    
                    # Categorize errors
                    hard_error_found = False
                    for error in errors:
                        code = error["code"]
                        error_counts[code] += 1
                        
                        if code.startswith("C"):
                            hard_errors_by_code[code] += 1
                            total_hard_errors += 1
                            hard_error_found = True
                        else:  # W codes
                            total_soft_warnings += 1
                        
                        error_record = {
                            "line": line_no,
                            "text_preview": record.get("text", "")[:50],
                            "triplet_idx": error.get("triplet_idx", -1),
                            "error_code": code,
                            "detail": error.get("detail", "")
                        }
                        all_errors.append(error_record)
                    
                    if line_no % 1000 == 0:
                        print(f"  ✓ Processed {line_no} records...")
                
                except json.JSONDecodeError as e:
                    print(f"  ⚠ Line {line_no}: JSON parse error - {e}")
                    total_records + 1
        
        print(f"\n✅ Audit complete! Processed {total_records} records with {total_triplets} triplets\n")
        
    except FileNotFoundError:
        print(f"❌ File not found: {INPUT_FILE}")
        return
    
    # Write errors to file
    with open(OUTPUT_ERRORS, 'w', encoding='utf-8') as f:
        for error in all_errors:
            f.write(json.dumps(error, ensure_ascii=False) + '\n')
    
    # Write clean records
    with open(OUTPUT_CLEAN, 'w', encoding='utf-8') as f:
        for record in clean_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # Print report
    print("=" * 70)
    print("AUDIT REPORT".center(70))
    print("=" * 70)
    print(f"Total records: {total_records}")
    print(f"Total triplets: {total_triplets}")
    print(f"Clean records: {clean_record_count} ({100*clean_record_count/max(total_records,1):.1f}%)")
    print()
    
    print("HARD ERRORS (record removed):")
    print("-" * 70)
    hard_error_total = 0
    for code in sorted(hard_errors_by_code.keys()):
        count = hard_errors_by_code[code]
        hard_error_total += count
        desc = {
            "C1": "Offset mismatch target",
            "C2": "Offset mismatch opinion",
            "C3": "Invalid aspect",
            "C4": "Invalid sentiment",
            "C5": "Target-opinion overlap",
            "C6": "Duplicate triplet"
        }.get(code, code)
        print(f"  {code:3s} ({desc:30s}): {count:4d} occurrence(s)")
    
    records_removed = total_records - clean_record_count
    print(f"\n  Total records with hard errors: {records_removed} ({100*records_removed/max(total_records,1):.1f}%)")
    print()
    
    print("SOFT WARNINGS (record kept for review):")
    print("-" * 70)
    for code in sorted(error_counts.keys()):
        if not code.startswith("C"):
            count = error_counts[code]
            desc = {
                "W1": "Sentiment-opinion mismatch",
                "W2": "Opinion fuzzy mismatch",
                "W3": "Generic target",
                "W4": "Neu but strong opinion",
                "W5": "Aspect-opinion pair mismatch",
                "W6": "Opinion too short/stop-word"
            }.get(code, code)
            print(f"  {code:3s} ({desc:35s}): {count:4d} occurrence(s)")
    print()
    
    print("=" * 70)
    print(f"Status: {'✅ EXCELLENT QUALITY' if clean_record_count == total_records else '⚠ NEEDS REVIEW'}")
    print("=" * 70)
    print()
    print(f"📁 Errors logged to: {OUTPUT_ERRORS}")
    print(f"📁 Clean records saved to: {OUTPUT_CLEAN}")
    print()

if __name__ == "__main__":
    main()

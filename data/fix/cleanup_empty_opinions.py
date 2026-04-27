import json
from collections import defaultdict

INPUT_FILE = "/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/train_final_v9_aste_selective_merged.jsonl"
OUTPUT_FILE = "/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/train_final_v9_CLEANED.jsonl"
REPORT_FILE = "/home/uph3hc/project/mlops-sentiment-pipeline/data/processed/CLEANUP_REPORT.md"

print("🧹 Cleaning dataset by removing triplets with empty opinions...\n")

total_records = 0
records_cleaned = 0
records_removed = 0
triplets_removed = 0
triplets_kept = 0

with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
     open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
    
    for line_no, line in enumerate(fin, 1):
        line = line.strip()
        if not line:
            continue
        
        record = json.loads(line)
        total_records += 1
        
        # Filter triplets: keep only those with non-empty opinion
        original_triplet_count = len(record.get('triplets', []))
        cleaned_triplets = [
            t for t in record.get('triplets', [])
            if t.get('opinion', '').strip() and t.get('opinion_span') != [-1, -1]
        ]
        
        triplets_removed += original_triplet_count - len(cleaned_triplets)
        triplets_kept += len(cleaned_triplets)
        
        # Only keep record if it has at least 1 valid triplet
        if len(cleaned_triplets) > 0:
            record['triplets'] = cleaned_triplets
            fout.write(json.dumps(record, ensure_ascii=False) + '\n')
            records_cleaned += 1
        else:
            records_removed += 1
        
        if line_no % 1000 == 0:
            print(f"  ✓ Processed {line_no} records...")

print(f"\n✅ Cleanup complete!\n")

# Calculate statistics
valid_opinion_triplets = triplets_kept
total_original_triplets = triplets_kept + triplets_removed

print(f"📊 Cleanup Statistics:")
print(f"  Original records: {total_records}")
print(f"  Records kept: {records_cleaned} ({100*records_cleaned/total_records:.1f}%)")
print(f"  Records removed: {records_removed} ({100*records_removed/total_records:.1f}%)")
print()
print(f"  Original triplets: {total_original_triplets}")
print(f"  Triplets kept: {triplets_kept} ({100*triplets_kept/total_original_triplets:.1f}%)")
print(f"  Triplets removed: {triplets_removed} ({100*triplets_removed/total_original_triplets:.1f}%)")
print()

# Verify output file
with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
    output_records = sum(1 for _ in f)
    f.seek(0)
    output_triplets = sum(len(json.loads(line).get('triplets', [])) for line in f)

print(f"✅ Output verification:")
print(f"  Output file: {OUTPUT_FILE}")
print(f"  Records: {output_records}")
print(f"  Triplets: {output_triplets}")

# Write report
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write("# Data Cleanup Report\n\n")
    f.write(f"**Processing Date**: {__import__('datetime').datetime.now().isoformat()}\n\n")
    f.write("## Summary\n\n")
    f.write(f"- **Input File**: `train_final_v9_aste_selective_merged.jsonl`\n")
    f.write(f"- **Output File**: `train_final_v9_CLEANED.jsonl`\n\n")
    f.write("## Issue Found\n\n")
    f.write(f"**1,981 triplets had empty opinions** with `opinion_span: [-1, -1]`\n\n")
    f.write("These triplets were created during the merge process but lack valid opinion annotations.\n\n")
    f.write("## Cleanup Results\n\n")
    f.write("### Records\n")
    f.write(f"| Metric | Count | % |\n")
    f.write(f"|--------|-------|----|\n")
    f.write(f"| Original Records | {total_records} | 100.0% |\n")
    f.write(f"| Records Kept | {records_cleaned} | {100*records_cleaned/total_records:.1f}% |\n")
    f.write(f"| Records Removed (no valid triplets) | {records_removed} | {100*records_removed/total_records:.1f}% |\n\n")
    f.write("### Triplets\n")
    f.write(f"| Metric | Count | % |\n")
    f.write(f"|--------|-------|----|\n")
    f.write(f"| Original Triplets | {total_original_triplets} | 100.0% |\n")
    f.write(f"| Triplets Kept | {triplets_kept} | {100*triplets_kept/total_original_triplets:.1f}% |\n")
    f.write(f"| Triplets Removed (empty opinion) | {triplets_removed} | {100*triplets_removed/total_original_triplets:.1f}% |\n\n")
    f.write("## Quality Metrics\n\n")
    f.write(f"- **Avg triplets/record**: {triplets_kept/records_cleaned:.2f}\n")
    f.write(f"- **Data loss**: {100*triplets_removed/total_original_triplets:.1f}% of triplets\n\n")
    f.write("## Recommendation\n\n")
    f.write("✅ Use `train_final_v9_CLEANED.jsonl` for model training - all triplets now have valid opinions.\n")

print(f"\n📄 Report saved: {REPORT_FILE}")

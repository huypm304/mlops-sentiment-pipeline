# ASTE QA Batch Report
**Input**: data_train_v8_aste.modifier_force_auto_merged.jsonl
**Error Source**: aste_force_audit_errors.jsonl
**Chunk size**: 250

| Batch | Description | Apply | Records | Chunks |
|---|---|---:|---:|---:|
| batch_01_span_exact | Span-only fixes with exact actionable span corrections | yes | 16 | 1 |
| batch_02_sentiment_only | Sentiment-only fixes with clear polarity cues | yes | 1060 | 5 |
| batch_03_aspect_only | Aspect-only fixes based on target keyword matches | yes | 303 | 2 |
| batch_04_mixed_safe | Mixed safe fixes without unresolved span issues | yes | 56 | 1 |
| batch_05_unresolved_review | Records still needing manual review because span cannot be fixed safely | no | 1737 | 7 |

**Final safe output**: final_safe_batched_fix.jsonl

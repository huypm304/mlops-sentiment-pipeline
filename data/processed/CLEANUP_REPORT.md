# Data Cleanup Report

**Processing Date**: 2026-04-27T13:02:02.818198

## Summary

- **Input File**: `train_final_v9_aste_selective_merged.jsonl`
- **Output File**: `train_final_v9_CLEANED.jsonl`

## Issue Found

**1,981 triplets had empty opinions** with `opinion_span: [-1, -1]`

These triplets were created during the merge process but lack valid opinion annotations.

## Cleanup Results

### Records
| Metric | Count | % |
|--------|-------|----|
| Original Records | 7565 | 100.0% |
| Records Kept | 6465 | 85.5% |
| Records Removed (no valid triplets) | 1100 | 14.5% |

### Triplets
| Metric | Count | % |
|--------|-------|----|
| Original Triplets | 11274 | 100.0% |
| Triplets Kept | 9293 | 82.4% |
| Triplets Removed (empty opinion) | 1981 | 17.6% |

## Quality Metrics

- **Avg triplets/record**: 1.44
- **Data loss**: 17.6% of triplets

## Recommendation

✅ Use `train_final_v9_CLEANED.jsonl` for model training - all triplets now have valid opinions.

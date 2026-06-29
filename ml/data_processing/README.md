# ABSA Data Benchmark

Portable data-quality audit suite for Vietnamese ABSA JSONL datasets.
Copy this entire folder to the main repo — no dependency on `src/absa` or training code.

## Structure

```
data_benchmark/
├── run_data_benchmark.py      # orchestrator (start here)
├── summarize.py               # aggregate module JSON → benchmark_summary.json
├── config/thresholds.json     # pass/warn/fail thresholds
├── audits/                    # individual audit scripts
│   ├── schema_audit.py
│   ├── span_offset_audit.py
│   ├── label_consistency_audit.py
│   ├── distribution_audit.py
│   ├── global_sentiment_audit.py
│   ├── leakage_audit.py
│   └── data_integrity.py      # optional style/template analysis (needs numpy)
└── reports/                   # output directory (gitignored in main repo)
```

## Quick start

```bash
# From repo root (only numpy needed for optional data_integrity)
pip install numpy

python data_benchmark/run_data_benchmark.py \
  --train data_stratified/train_aug500_boundary200.jsonl \
  --dev   data_stratified/dev_clean.jsonl \
  --test  data_stratified/test_clean.jsonl \
  --output-dir data_benchmark/reports
```

Output:
- `reports/*.json` — per-module detailed reports
- `reports/benchmark_summary.json` — consolidated status (like `analysis/benchmark_data_audit_clean_v3.json`)
- `reports/data_integrity_style_analysis.json` — optional style/template report

Skip optional integrity check (stdlib only):

```bash
python data_benchmark/run_data_benchmark.py \
  --train ... --dev ... --output-dir ... \
  --skip-integrity
```

## Copy to main repo

1. Copy the whole `data_benchmark/` folder.
2. Point `--train` / `--dev` at your canonical JSONL paths.
3. Adjust `config/thresholds.json` if your dataset size differs (e.g. dev per-aspect minimums).
4. Add to CI or pre-train checklist: exit code `1` when `overall.data_level_status == "fail"`.

## Module overview

| Module | Checks |
|--------|--------|
| `schema_audit` | Required fields, valid aspect/sentiment labels |
| `span_offset_audit` | Opinion span offsets match text |
| `label_consistency_audit` | Suspicious aspect/sentiment patterns |
| `distribution_audit` | Per-aspect and cell counts |
| `global_sentiment_audit` | Global sentiment vs opinion rule |
| `leakage_audit` | Exact/near duplicate train↔dev |
| `data_integrity` | Style divergence, template overlap (optional) |

## Relation to other scripts

- `scripts/make_data_reports.py` — lighter MLOps reports → `final_artifacts/data/` (distribution + leakage only).
- `scripts/model_sanity_benchmark.py` — model baselines, **not** included here (separate concern).
- Old copies in `scripts/*_audit.py` — same logic; prefer `data_benchmark/` for portability.

## Re-summarize only

If audit JSONs already exist:

```bash
python data_benchmark/summarize.py \
  --reports-dir data_benchmark/reports \
  --train data_stratified/train_aug500_boundary200.jsonl \
  --thresholds data_benchmark/config/thresholds.json
```

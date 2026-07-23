#!/usr/bin/env bash
# Runs on the EC2 instance. Env vars injected by demo_ec2_train.sh user-data.
set -euo pipefail

exec > >(tee -a /var/log/absa-ec2-demo.log) 2>&1

: "${BUCKET:?}"
: "${RUN_ID:?}"
: "${AWS_REGION:=ap-southeast-1}"
: "${DATASET_PREFIX:=datasets/pending/data-train-v2-fa3ee196}"
: "${MODE:=short}"          # short | smoke
: "${EPOCHS:=1}"
: "${MAX_TRAIN:=120}"
: "${MAX_DEV:=40}"
: "${BATCH_SIZE:=4}"
: "${MAX_LEN:=96}"
: "${INSTANCE_TYPE:=m5.2xlarge}"

STATUS_KEY="training-runs/${RUN_ID}/_STATUS.json"
OUT_PREFIX="training-runs/${RUN_ID}"
WORK=/opt/absa-demo
mkdir -p "$WORK"/{code,data,out}

put_status() {
  local status="$1"
  local message="${2:-}"
  local tmp
  tmp="$(mktemp)"
  python3 - "$tmp" "$status" "$message" <<'PY'
import json, datetime, sys
path, status, message = sys.argv[1], sys.argv[2], sys.argv[3]
payload = {
  "run_id": __import__("os").environ["RUN_ID"],
  "status": status,
  "message": message,
  "mode": __import__("os").environ.get("MODE", ""),
  "instance_type": __import__("os").environ.get("INSTANCE_TYPE", ""),
  "updated_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
}
open(path, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False))
print("STATUS", payload)
PY
  aws s3 cp "$tmp" "s3://${BUCKET}/${STATUS_KEY}" --region "$AWS_REGION" --content-type application/json >/dev/null
  rm -f "$tmp"
}

trap 'put_status FAILED "bootstrap exited unexpectedly"' ERR

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3-pip python3-venv awscli git jq

put_status RUNNING "bootstrap started"

if [[ "${MODE}" == "smoke" ]]; then
  put_status RUNNING "smoke: syncing production baseline"
  mkdir -p "$WORK/out" "$WORK/data"
  # Tiny dataset markers for manifest counts
  aws s3 cp "s3://${BUCKET}/${DATASET_PREFIX}/train.jsonl" "$WORK/data/train_full.jsonl" --region "$AWS_REGION"
  aws s3 cp "s3://${BUCKET}/${DATASET_PREFIX}/dev.jsonl" "$WORK/data/dev_full.jsonl" --region "$AWS_REGION"
  head -n "${MAX_TRAIN}" "$WORK/data/train_full.jsonl" > "$WORK/data/train.jsonl"
  head -n "${MAX_DEV}" "$WORK/data/dev_full.jsonl" > "$WORK/data/dev.jsonl"

  aws s3 sync "s3://${BUCKET}/models/v1/" "$WORK/out/" --region "$AWS_REGION" \
    --exclude "*" --include "train_log.csv" --include "run_config.json" \
    --include "best_confusion_matrices.json" --include "confusion_matrices.jsonl" \
    --include "best_model.pt"

  python3 - <<'PY'
import json, time
from pathlib import Path
out = Path("/opt/absa-demo/out")
cfg = {
  "mode": "ec2-smoke",
  "note": "Demo smoke: synced models/v1 baseline after EC2 bootstrap",
  "slept_seconds": 20,
}
(out / "ec2_demo_meta.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
time.sleep(20)
PY

  python3 - <<PY
import json, datetime
from pathlib import Path
out = Path("/opt/absa-demo/out")
manifest = {
  "run_id": "${RUN_ID}",
  "status": "Completed",
  "mode": "ec2-smoke",
  "instance_type": "${INSTANCE_TYPE}",
  "dataset_prefix": "${DATASET_PREFIX}",
  "train_rows": sum(1 for _ in open("/opt/absa-demo/data/train.jsonl")),
  "dev_rows": sum(1 for _ in open("/opt/absa-demo/data/dev.jsonl")),
  "epochs": int("${EPOCHS}"),
  "completed_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
  "message": "EC2 demo smoke completed (baseline sync)",
}
(out / "training_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
cfg_path = out / "run_config.json"
cfg = {}
if cfg_path.exists():
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
cfg.update({
  "run_id": "${RUN_ID}",
  "training_backend": "ec2",
  "sagemaker_instance_type": "${INSTANCE_TYPE}",
  "mode": "ec2-smoke",
})
cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(manifest, indent=2))
PY

  aws s3 sync "$WORK/out/" "s3://${BUCKET}/${OUT_PREFIX}/" --region "$AWS_REGION"
  put_status COMPLETED "artifacts at s3://${BUCKET}/${OUT_PREFIX}/"
  echo "DONE ${RUN_ID}"
  exit 0
fi

python3 -m venv "$WORK/venv"
# shellcheck disable=SC1091
source "$WORK/venv/bin/activate"
pip install -U pip wheel

# Training source (same package as SageMaker)
aws s3 cp "s3://${BUCKET}/training/source/source.tar.gz" "$WORK/source.tar.gz" --region "$AWS_REGION"
mkdir -p "$WORK/code"
tar -xzf "$WORK/source.tar.gz" -C "$WORK/code"

# Extra deps for CPU train (torch CPU wheel) — pin to match thesis stack
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu
pip install pytorch-crf==0.7.2 "transformers==4.41.2" sentencepiece==0.2.0 scikit-learn pandas tqdm

# Dataset
aws s3 cp "s3://${BUCKET}/${DATASET_PREFIX}/train.jsonl" "$WORK/data/train_full.jsonl" --region "$AWS_REGION"
aws s3 cp "s3://${BUCKET}/${DATASET_PREFIX}/dev.jsonl" "$WORK/data/dev_full.jsonl" --region "$AWS_REGION"

# Tiny subset for demo wall-clock
head -n "${MAX_TRAIN}" "$WORK/data/train_full.jsonl" > "$WORK/data/train.jsonl"
head -n "${MAX_DEV}" "$WORK/data/dev_full.jsonl" > "$WORK/data/dev.jsonl"
echo "Subset train=$(wc -l < "$WORK/data/train.jsonl") dev=$(wc -l < "$WORK/data/dev.jsonl")"

put_status RUNNING "training ${MODE}"

cd "$WORK/code"
python train_kaggle.py \
  --train-file "$WORK/data/train.jsonl" \
  --val-file "$WORK/data/dev.jsonl" \
  --output-dir "$WORK/out" \
  --epochs "${EPOCHS}" \
  --patience "${EPOCHS}" \
  --phase1-epochs 0 \
  --batch-size "${BATCH_SIZE}" \
  --eval-batch-size "${BATCH_SIZE}" \
  --max-len "${MAX_LEN}" \
  --num-workers 0 \
  --disable-ema \
  --grad-accum-steps 1

# Manifest looks similar to SageMaker training job output
python3 - <<PY
import json, datetime
from pathlib import Path
out = Path("/opt/absa-demo/out")
manifest = {
  "run_id": "${RUN_ID}",
  "status": "Completed",
  "mode": "ec2-${MODE}",
  "instance_type": "${INSTANCE_TYPE}",
  "dataset_prefix": "${DATASET_PREFIX}",
  "train_rows": sum(1 for _ in open("/opt/absa-demo/data/train.jsonl")),
  "dev_rows": sum(1 for _ in open("/opt/absa-demo/data/dev.jsonl")),
  "epochs": int("${EPOCHS}"),
  "completed_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
  "message": "EC2 demo training completed",
}
(out / "training_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
cfg_path = out / "run_config.json"
cfg = {}
if cfg_path.exists():
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
cfg.update({
  "run_id": "${RUN_ID}",
  "training_backend": "ec2",
  "sagemaker_instance_type": "${INSTANCE_TYPE}",
  "mode": "ec2-${MODE}",
})
cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(manifest, indent=2))
PY

aws s3 sync "$WORK/out/" "s3://${BUCKET}/${OUT_PREFIX}/" --region "$AWS_REGION"
put_status COMPLETED "artifacts at s3://${BUCKET}/${OUT_PREFIX}/"
echo "DONE ${RUN_ID}"

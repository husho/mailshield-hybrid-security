#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

source .venv/bin/activate

mailshield-train \
  --logs-dir ./Logs \
  --output-dir ./artifacts/full-$(date +%Y%m%d-%H%M%S) \
  --window-minutes 15 \
  --seq-len 8 \
  --epochs 3 \
  --batch-size 1024 \
  --seed 42

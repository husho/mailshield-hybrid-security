# MailShield Hybrid Security MVP

This project performs `normal / anomaly / spam` detection from hosting email logs (`SMTP`, `MTA`, `MTAFILTER`) using a **deep-learning hybrid model**.

## Why this architecture?
- Direct thesis alignment: deep learning is mandatory.
- Hybrid approach: temporal behavior branch (GRU) + structural metadata branch (MLP).
- Weak-label training from real production logs.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Training
```bash
mailshield-train \
  --logs-dir "./Logs" \
  --output-dir "./artifacts/latest" \
  --window-minutes 15 \
  --seq-len 8 \
  --epochs 5
```

Full dataset helper:
```bash
./scripts/train_full.sh
```

Synthetic demo dataset:
```bash
mailshield-generate-synth \
  --output-dir ./sample_data/synthetic-logs \
  --hosts 3 \
  --days 14 \
  --events-per-day 1000
```

## Evaluation
```bash
mailshield-eval \
  --logs-dir ./Logs \
  --model-dir ./artifacts/full-20260225 \
  --output-dir ./artifacts/full-20260225/eval
```

## Thesis Figures
```bash
pip install -e .[report]
mailshield-thesis-figures \
  --eval-dir ./artifacts/full-20260225/eval-xgb \
  --train-summary ./artifacts/full-20260225/training_summary.json \
  --output-dir ./artifacts/full-20260225/figures
```

## API
```bash
mailshield-api --model-dir ./artifacts/latest --host 0.0.0.0 --port 8000
```

Example endpoints:
- `GET /v1/health`
- `GET /v1/model/info`
- `POST /v1/score/window`
- `POST /v1/score/batch`

Example request:
```bash
curl -X POST http://localhost:8000/v1/score/window \
  -H "Content-Type: application/json" \
  -d '{
    "host_id": "host1",
    "entity_id_hash": "sample-account-hash",
    "window_start": "2026-02-13T10:00:00Z",
    "window_end": "2026-02-13T10:15:00Z",
    "static_features": {
      "smtp_events": 120,
      "smtp_auth_attempts": 100,
      "smtp_auth_failures": 95,
      "smtp_auth_failure_rate": 0.95,
      "smtp_data_events": 3,
      "smtp_unique_src_ip": 25,
      "smtp_bytes_in": 12000,
      "smtp_bytes_out": 43000,
      "mta_routes_total": 20,
      "mta_routes_smtp": 19,
      "mta_routes_sf": 1,
      "mta_unique_senders": 3,
      "mtafilter_exec_count": 1,
      "mtafilter_spam_delete": 1,
      "mtafilter_spam_high": 0,
      "mtafilter_spam_low": 0
    },
    "history_features": []
  }'
```

## Notes
- PII fields (email/domain/IP) are hashed.
- The model is calibrated with recall priority.
- No automatic blocking in MVP mode; only risk score and recommendations are returned.

## Public Repository Note
- Real production logs are intentionally excluded from this repository.
- To keep the project runnable, a synthetic MailEnable-like log generator is provided.
- See [PUBLIC_GITHUB_GUIDE_TR.md](/Users/huseyinkaranik/Tez%20Uygulaması/docs/PUBLIC_GITHUB_GUIDE_TR.md) for release checklist and demo flow.

## Publish to GitHub
```bash
git add .
git commit -m "Initial public release"
./scripts/publish_github.sh mailshield-hybrid-security public
```

# MailShield Hybrid Security

MailShield Hybrid Security is a deep-learning based email security project for `normal / anomaly / spam` detection on web hosting email logs.

It is structured as a research-oriented implementation and evaluation environment for hosting email security analytics.

## Architecture
- Temporal branch: `GRU`
- Structural branch: `MLP`
- Input sources: `SMTP`, `MTA`, `MTAFILTER` logs
- Output classes: `normal`, `anomaly`, `spam`

## Features
- Log parsers for hosting email workflows
- Model training and evaluation pipeline
- REST API for scoring
- Figure generation for reporting and comparative analysis
- Synthetic log generator for reproducible public demos

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start
Train:
```bash
mailshield-train \
  --logs-dir "./Logs" \
  --output-dir "./artifacts/latest" \
  --window-minutes 15 \
  --seq-len 8 \
  --epochs 5
```

Evaluate:
```bash
mailshield-eval \
  --logs-dir ./Logs \
  --model-dir ./artifacts/full-20260225 \
  --output-dir ./artifacts/full-20260225/eval
```

Run API:
```bash
mailshield-api --model-dir ./artifacts/latest --host 0.0.0.0 --port 8000
```

Generate evaluation/report figures:
```bash
pip install -e .[report]
mailshield-thesis-figures \
  --eval-dir ./artifacts/full-20260225/eval-xgb \
  --train-summary ./artifacts/full-20260225/training_summary.json \
  --output-dir ./artifacts/full-20260225/figures
```

## Data and Privacy
- Real production logs are intentionally excluded from the public repository.
- A synthetic MailEnable-like log generator is included for reproducibility:
```bash
mailshield-generate-synth \
  --output-dir ./sample_data/synthetic-logs \
  --hosts 3 \
  --days 14 \
  --events-per-day 1000
```
- Sensitive identifiers such as email, domain, and IP fields are processed in hashed form.

## Documentation
- Results summary: [docs/THESIS_RESULTS_FINAL_EN.md](docs/THESIS_RESULTS_FINAL_EN.md)
- Figure captions and interpretation notes: [docs/THESIS_FIGURE_TEXT_FINAL_EN.md](docs/THESIS_FIGURE_TEXT_FINAL_EN.md)
- Turkish results summary: [docs/THESIS_RESULTS_FINAL_TR.md](docs/THESIS_RESULTS_FINAL_TR.md)
- Turkish figure captions: [docs/THESIS_FIGURE_TEXT_FINAL_TR.md](docs/THESIS_FIGURE_TEXT_FINAL_TR.md)

## License
This project is licensed under the [MIT License](LICENSE).

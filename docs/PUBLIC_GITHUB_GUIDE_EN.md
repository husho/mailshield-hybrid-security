# Public GitHub Release Guide (Without Real Logs)

## Goal
Publish the project publicly without exposing real customer data or sensitive logs, while preserving a runnable demo workflow.

## Implemented Approach
- Real logs are excluded from the repository (`Logs/` and `Logs.zip` are ignored).
- A synthetic log generator is included: `mailshield-generate-synth`
- Training, API, and evaluation commands can run fully on synthetic data.

## Public Repository Content
- Source code
- README and run instructions
- Synthetic data generation command
- Training/evaluation scripts
- Small sample output artifacts

## Must Stay Private
- Real log files
- Any raw output containing PII
- Internal IP/domain lists
- Production secrets/configuration

## One-shot Demo Flow
1. Generate synthetic logs:
```bash
mailshield-generate-synth --output-dir ./sample_data/synthetic-logs --hosts 3 --days 14 --events-per-day 1000
```

2. Train model:
```bash
mailshield-train --logs-dir ./sample_data/synthetic-logs --output-dir ./artifacts/public-demo --epochs 3 --window-minutes 15 --seq-len 8
```

3. Run API:
```bash
mailshield-api --model-dir ./artifacts/public-demo --host 0.0.0.0 --port 8000
```

4. Run baseline comparison:
```bash
mailshield-eval --logs-dir ./sample_data/synthetic-logs --model-dir ./artifacts/public-demo --output-dir ./artifacts/public-demo/eval
```

## Publish to GitHub (CLI)
1. Create first commit:
```bash
git add .
git commit -m "Initial public release"
```

2. Create public repo and push:
```bash
./scripts/publish_github.sh mailshield-hybrid-security public
```

3. Alternative (manual):
```bash
gh repo create mailshield-hybrid-security --public --source . --remote origin --push
```

## Suggested README Note
"Real production logs are excluded from this repository due to data privacy constraints. A synthetic MailEnable-like log generator is included for reproducibility and runnable demos."

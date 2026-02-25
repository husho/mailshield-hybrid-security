from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .infer import ModelArtifacts, load_artifacts, score_window


class WindowScoreRequest(BaseModel):
    host_id: str
    entity_id_hash: str
    window_start: datetime
    window_end: datetime
    static_features: Dict[str, float]
    history_features: List[Dict[str, float]] = Field(default_factory=list)


class BatchScoreRequest(BaseModel):
    items: List[WindowScoreRequest]


def create_app(model_dir: Path, device: str = "cpu") -> FastAPI:
    app = FastAPI(title="MailShield Hybrid Security API", version="0.1.0")
    artifacts: ModelArtifacts = load_artifacts(model_dir=model_dir, device=device)

    @app.get("/v1/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/model/info")
    def model_info() -> Dict:
        meta = artifacts.metadata
        return {
            "created_at": meta.get("created_at"),
            "window_minutes": meta.get("window_minutes"),
            "seq_len": meta.get("seq_len"),
            "num_hosts": len(meta.get("host_to_idx", {})),
            "labels": meta.get("label_to_idx", {}),
        }

    @app.post("/v1/score/window")
    def score_window_endpoint(payload: WindowScoreRequest) -> Dict:
        if payload.window_end <= payload.window_start:
            raise HTTPException(status_code=400, detail="window_end must be after window_start")

        result = score_window(
            artifacts=artifacts,
            host_id=payload.host_id,
            static_features=payload.static_features,
            history_features=payload.history_features,
        )
        return {
            "entity_id_hash": payload.entity_id_hash,
            "host_id": payload.host_id,
            "window_start": payload.window_start,
            "window_end": payload.window_end,
            "scored_at": datetime.now(timezone.utc),
            **result,
        }

    @app.post("/v1/score/batch")
    def score_batch_endpoint(payload: BatchScoreRequest) -> Dict:
        results = []
        for item in payload.items:
            result = score_window(
                artifacts=artifacts,
                host_id=item.host_id,
                static_features=item.static_features,
                history_features=item.history_features,
            )
            results.append(
                {
                    "entity_id_hash": item.entity_id_hash,
                    "host_id": item.host_id,
                    "window_start": item.window_start,
                    "window_end": item.window_end,
                    "scored_at": datetime.now(timezone.utc),
                    **result,
                }
            )
        return {"items": results}

    @app.get("/v1/alerts")
    def list_alerts() -> Dict:
        raise HTTPException(status_code=501, detail="Alert persistence is not implemented in MVP.")

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MailShield Hybrid Security API")
    parser.add_argument("--model-dir", type=Path, default=Path(os.getenv("MODEL_DIR", "./artifacts/latest")))
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", type=str, default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = create_app(model_dir=args.model_dir, device=args.device)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

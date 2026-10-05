"""Model routes — training-data inventory, model info, admin-gated retraining (PRD §19/§20)."""

import os

from fastapi import APIRouter, HTTPException

from data_pipeline.performance.generate_panel import generate_panel, panel_summary
from lib import model_store, trainer
from models.models import ModelInfo, TrainPanelRequest, TrainRequest, TrainingDataSummary

router = APIRouter()


def _check_admin(token: str | None) -> None:
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_TOKEN is not configured on the server")
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")


@router.get("/model/info", response_model=ModelInfo)
async def model_info():
    return ModelInfo(**{"status": "heuristic", "modelType": "", "featureImportances": [],
                        "metrics": {}, **model_store.info()})


@router.get("/model/training-data", response_model=TrainingDataSummary)
async def training_data():
    return await panel_summary()


@router.post("/model/generate-panel")
async def generate_training_panel(body: TrainPanelRequest):
    """Regenerate the DEMO/TRAINING performance panel from the seeded network."""
    _check_admin(body.adminToken)
    return await generate_panel(replace=body.replace)


@router.post("/model/train")
async def train_model(body: TrainRequest):
    """Fit XGBoost on the ingested branch-performance history and persist the artifact."""
    _check_admin(body.adminToken)
    result = await trainer.train()
    if result.get("status") != "trained":
        raise HTTPException(status_code=422, detail=result)
    return result

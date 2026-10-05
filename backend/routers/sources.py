"""Source registry + data-quality routes (§22, §31) + scoring config transparency."""

from fastapi import APIRouter

from data_pipeline.validate import quality_report
from lib import scoring
from lib.db import db
from models.models import QualityReport

router = APIRouter()


@router.get("/sources")
async def list_sources():
    docs = await db.data_sources.find({}, {"_id": 0}).to_list(100)
    return {"sources": docs, "scoringConfig": scoring.CONFIG}


@router.get("/quality", response_model=QualityReport)
async def data_quality():
    branch_docs = await db.branches.find({}, {"_id": 0}).to_list(50000)
    pin_docs = await db.pincodes.find({}, {"_id": 0}).to_list(20000)
    demo = await db.data_sources.find_one({"sourceId": "branchiq-demo"}, {"_id": 0})
    return quality_report(branch_docs, pin_docs, demo)


@router.get("/scoring-config")
async def scoring_config():
    return scoring.CONFIG

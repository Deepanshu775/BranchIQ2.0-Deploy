"""Opportunity routes — state (ported 1.0), district, city rankings + district market overview."""

from fastapi import APIRouter, Query, HTTPException

from lib import analytics
from models.models import CityRanked, DistrictRanked, StateRanked

router = APIRouter()


@router.get("/opportunities/states", response_model=list[StateRanked])
async def states_opportunities(bank: str | None = None):
    return await analytics.states_ranked(bank)


@router.get("/opportunities/districts", response_model=list[DistrictRanked])
async def districts_opportunities(state_id: str = Query(...), bank: str | None = None):
    return await analytics.districts_ranked(state_id, bank)


@router.get("/opportunities/cities", response_model=list[CityRanked])
async def cities_opportunities(district_id: str = Query(...), bank: str | None = None):
    rows = await analytics.cities_ranked(district_id, bank)
    if not rows:
        raise HTTPException(status_code=404, detail="No cities found for this district")
    return rows


@router.get("/market/{district_id}")
async def market_overview(district_id: str):
    doc = await analytics.market_overview(district_id)
    if not doc:
        raise HTTPException(status_code=404, detail="District not found")
    return doc

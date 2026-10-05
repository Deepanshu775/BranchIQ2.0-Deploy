"""Location Intelligence routes — the BranchIQ 2.0 core.

GET /locations/ranked      ranked candidate branch locations (scope: state/district/city)
GET /location/{id}         full detail: breakdown, catchment, nearby branches, evidence, confidence
GET /location/{id}/score   fresh transparent score breakdown (recomputed on demand)
GET /location/{id}/catchment  catchment rings (1/3/5/10 km configurable)
"""

from fastapi import APIRouter, HTTPException, Query

from lib import analytics
from models.models import LocationDetail, RankedLocation

router = APIRouter()


@router.get("/locations/ranked", response_model=list[RankedLocation])
async def ranked_locations(
    state_id: str | None = None,
    district_id: str | None = None,
    city_id: str | None = None,
    bank: str | None = None,
    min_score: int | None = Query(None, ge=0, le=100),
    min_population: int | None = Query(None, ge=0),
    limit: int = Query(20, le=100),
):
    if not any([state_id, district_id, city_id]):
        raise HTTPException(status_code=422, detail="Provide state_id, district_id or city_id")
    rows = await analytics.locations_ranked(state_id, district_id, city_id, bank,
                                            min_score=min_score, min_population=min_population, limit=limit)
    return rows


@router.get("/location/{candidate_id}", response_model=LocationDetail)
async def location_detail(candidate_id: str, bank: str | None = None):
    detail = await analytics.location_detail(candidate_id, bank)
    if not detail:
        raise HTTPException(status_code=404, detail="Location not found")
    return detail


@router.get("/location/{candidate_id}/score")
async def location_score(candidate_id: str, bank: str | None = None):
    detail = await analytics.location_detail(candidate_id, bank)
    if not detail:
        raise HTTPException(status_code=404, detail="Location not found")
    return {
        "id": candidate_id,
        "name": detail["name"], "city": detail["city"], "district": detail["district"], "state": detail["state"],
        "score": detail["score"], "baseScore": detail["baseScore"],
        "breakdown": detail["breakdown"], "penalties": detail["penalties"], "totalPenalty": detail["totalPenalty"],
        "decision": detail["decision"], "cannibalization": detail["cannibalization"],
        "whitespaceScore": detail["whitespaceScore"], "mlPrediction": detail["mlPrediction"],
        "blended": detail["blended"],
        "confidence": detail["confidence"],
    }


@router.get("/location/{candidate_id}/catchment")
async def location_catchment(candidate_id: str, radius_km: float | None = Query(None, gt=0, le=25)):
    detail = await analytics.location_detail(candidate_id, None)
    if not detail:
        raise HTTPException(status_code=404, detail="Location not found")
    catchment = detail["catchment"]
    if radius_km is not None:
        catchment = {**catchment, "rings": [r for r in catchment["rings"] if r["radiusKm"] <= radius_km]}
    return {"id": candidate_id, "name": detail["name"], **catchment}

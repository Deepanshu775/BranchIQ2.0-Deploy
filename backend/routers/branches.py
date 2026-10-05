"""Branch routes — paginated branch queries + nearby competitor analysis."""

from fastapi import APIRouter, Query

from lib.analytics import resolve_bank
from lib.db import db
from lib.geo import GeoIndex
from models.models import Branch, BranchPage, CompetitorsNear, CompetitorGroup, NearbyBranch

router = APIRouter()


@router.get("/branches", response_model=BranchPage)
async def list_branches(
    bank: str | None = None,
    state_id: str | None = None,
    district_id: str | None = None,
    city_id: str | None = None,
    limit: int = Query(200, le=1000),
    offset: int = Query(0, ge=0),
):
    q: dict = {}
    if bank:
        b = await resolve_bank(bank)
        if not b:
            return BranchPage(total=0, items=[])
        q["bankId"] = b["id"]
    if state_id:
        q["stateId"] = state_id
    if district_id:
        q["districtId"] = district_id
    if city_id:
        q["cityId"] = city_id
    total = await db.branches.count_documents(q)
    docs = await db.branches.find(q, {"_id": 0}).sort("name", 1).skip(offset).limit(limit).to_list(limit)
    return BranchPage(total=total, items=[Branch(**d) for d in docs])


@router.get("/competitors", response_model=CompetitorsNear)
async def competitors_near(
    lat: float,
    lng: float,
    radius_km: float = Query(10, gt=0, le=50),
    exclude_bank: str | None = None,
):
    """Branches near a point, grouped by bank. Heavy geospatial math stays server-side."""
    dr = radius_km / 111.0
    dl = radius_km / (111.0 * max(__import__("math").cos(__import__("math").radians(lat)), 0.2))
    box = {"lat": {"$gte": lat - dr, "$lte": lat + dr}, "lng": {"$gte": lng - dl, "$lte": lng + dl}}
    docs = await db.branches.find(box, {"_id": 0}).to_list(20000)

    excluded_id = None
    if exclude_bank:
        b = await resolve_bank(exclude_bank)
        excluded_id = b["id"] if b else None

    idx = GeoIndex(docs)
    near = idx.query(lat, lng, radius_km)

    groups: dict[str, list] = {}
    for doc, dist in near:
        if excluded_id and doc["bankId"] == excluded_id:
            continue
        groups.setdefault(doc["bankShort"], []).append(NearbyBranch(
            id=doc["id"], bankShort=doc["bankShort"], bankName=doc["bankName"], name=doc["name"],
            lat=doc["lat"], lng=doc["lng"], distanceKm=round(dist, 2),
            pincode=doc.get("pincode", ""), branchType=doc.get("branchType", "")))

    out = []
    for short in sorted(groups, key=lambda s: min(b.distanceKm for b in groups[s])):
        items = groups[short]
        out.append(CompetitorGroup(bankShort=short, bankName=items[0].bankName, count=len(items),
                                   nearestKm=items[0].distanceKm, branches=items[:8]))
    total = sum(g.count for g in out)
    return CompetitorsNear(center={"lat": lat, "lng": lng}, radiusKm=radius_km, groups=out, total=total)

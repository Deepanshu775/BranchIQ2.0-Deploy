"""Catalog routes — banks, states, districts, cities, pincodes (hierarchy lookups)."""

from fastapi import APIRouter, Query

from lib.db import db
from models.models import Bank, City, District, Pincode, State

router = APIRouter()


@router.get("/banks", response_model=list[Bank])
async def list_banks():
    docs = await db.banks.find({}, {"_id": 0}).sort("branches", -1).to_list(100)
    return [Bank(**d) for d in docs]


@router.get("/states", response_model=list[State])
async def list_states():
    docs = await db.states.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    return [State(**d) for d in docs]


@router.get("/districts", response_model=list[District])
async def list_districts(state_id: str = Query(...)):
    docs = await db.districts.find({"stateId": state_id}, {"_id": 0}).sort("populationMn", -1).to_list(1000)
    return [District(**d) for d in docs]


@router.get("/cities", response_model=list[City])
async def list_cities(district_id: str = Query(...)):
    docs = await db.cities.find({"districtId": district_id}, {"_id": 0}).sort("populationK", -1).to_list(2000)
    return [City(**d) for d in docs]


@router.get("/pincodes", response_model=list[Pincode])
async def list_pincodes(city_id: str = Query(...)):
    docs = await db.pincodes.find({"cityId": city_id}, {"_id": 0}).to_list(2000)
    return [Pincode(**d) for d in docs]

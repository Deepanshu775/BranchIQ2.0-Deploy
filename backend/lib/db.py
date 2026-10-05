"""Shared Mongo handle — import `client`/`db` from here (server.py, routers, seed.py)."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

load_dotenv(Path(__file__).parent.parent / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

logger = logging.getLogger(__name__)

# One entry per collection: every field a route filters, sorts, or dedupes on. Applied by ensure_indexes() at startup.
INDEXES: dict[str, list[IndexModel]] = {
    "status_checks": [IndexModel([("timestamp", DESCENDING)], name="timestamp_desc")],
    "banks": [IndexModel([("id", ASCENDING)], name="id", unique=True)],
    "data_sources": [IndexModel([("sourceId", ASCENDING)], name="sourceId", unique=True)],
    "states": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("name", ASCENDING)], name="name", unique=True),
    ],
    "districts": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("stateId", ASCENDING), ("name", ASCENDING)], name="state_name"),
    ],
    "cities": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("districtId", ASCENDING), ("populationK", DESCENDING)], name="district_pop"),
        IndexModel([("stateId", ASCENDING)], name="state_id"),
    ],
    "pincodes": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("cityId", ASCENDING)], name="city_id"),
        IndexModel([("pin", ASCENDING)], name="pin"),
    ],
    "branches": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("bankId", ASCENDING), ("districtId", ASCENDING), ("cityId", ASCENDING)], name="bank_district_city"),
        IndexModel([("stateId", ASCENDING), ("bankId", ASCENDING)], name="state_bank"),
        IndexModel([("lat", ASCENDING), ("lng", ASCENDING)], name="latlng"),
    ],
    "market_metrics": [
        IndexModel([("refId", ASCENDING), ("scope", ASCENDING)], name="ref_scope", unique=True),
        IndexModel([("stateId", ASCENDING)], name="state_id"),
    ],
    "location_candidates": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("cityId", ASCENDING)], name="city_id"),
        IndexModel([("districtId", ASCENDING)], name="district_id"),
        IndexModel([("stateId", ASCENDING)], name="state_id"),
    ],
    "opportunity_scores": [
        IndexModel([("candidate_id", ASCENDING), ("bank_id", ASCENDING)], name="candidate_bank", unique=True),
    ],
    "model_predictions": [
        IndexModel([("candidate_id", ASCENDING), ("bank_id", ASCENDING)], name="candidate_bank", unique=True),
    ],
    "consultant_queries": [IndexModel([("timestamp", DESCENDING)], name="timestamp_desc")],
}


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:  # one at a time so a bad spec skips only itself
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:  # never block boot on an index; the log line names what to fix
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)

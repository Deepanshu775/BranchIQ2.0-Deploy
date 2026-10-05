"""CSV ingestion for REAL branch-performance history (PRD §23).

Required columns (header row, case-insensitive):
    branch_id, bank, fiscal_year, deposits_cr, advances_cr
Optional:
    accounts, source, source_url, source_date

Every row is validated, normalized, deduplicated on (branch_id, fiscal_year) and stored with
sourceType="official" so the trainer prefers it over the demo panel automatically.

Usage:
    python -m data_pipeline.performance.ingest_csv /path/to/history.csv
"""

import asyncio
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.db import db

REQUIRED = ["branch_id", "bank", "fiscal_year", "deposits_cr", "advances_cr"]


def _num(value: str, field: str, row_no: int) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise ValueError(f"row {row_no}: {field} is not numeric ({value!r})")


def parse_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Validate + normalize CSV rows. Returns (clean docs, per-row error messages)."""
    docs: list[dict] = []
    errors: list[str] = []
    now = datetime.now(timezone.utc).isoformat()
    seen: set[tuple[str, str]] = set()
    for i, raw in enumerate(rows, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        missing = [c for c in REQUIRED if not row.get(c)]
        if missing:
            errors.append(f"row {i}: missing {', '.join(missing)}")
            continue
        try:
            deposits = _num(row["deposits_cr"], "deposits_cr", i)
            advances = _num(row["advances_cr"], "advances_cr", i)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if deposits < 0 or advances < 0:
            errors.append(f"row {i}: negative deposits/advances")
            continue
        key = (row["branch_id"], row["fiscal_year"])
        if key in seen:
            errors.append(f"row {i}: duplicate (branch_id, fiscal_year) — later row kept")
        seen.add(key)
        docs.append({
            "id": f"perf-{row['branch_id']}-{row['fiscal_year']}",
            "branchId": row["branch_id"],
            "bankShort": row["bank"],
            "fiscalYear": row["fiscal_year"],
            "depositsCr": deposits,
            "advancesCr": advances,
            "businessCr": round(deposits + advances, 2),
            "accounts": int(_num(row["accounts"], "accounts", i)) if row.get("accounts") else None,
            "sourceType": "official",
            "sourceName": row.get("source") or "User-supplied historical dataset",
            "sourceUrl": row.get("source_url") or None,
            "sourceDate": row.get("source_date") or None,
            "ingestedAt": now,
        })
    return docs, errors


async def ingest_csv(path: str | Path) -> dict:
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    docs, errors = parse_rows(rows)

    # Geography/bank mapping from the branch master, so training features resolve.
    branches = await db.branches.find({}, {"_id": 0, "id": 1, "bankId": 1, "stateId": 1,
                                           "districtId": 1, "cityId": 1}).to_list(100000)
    by_id = {b["id"]: b for b in branches}
    unmapped = 0
    for d in docs:
        b = by_id.get(d["branchId"])
        if b:
            d.update({"bankId": b["bankId"], "stateId": b["stateId"],
                      "districtId": b["districtId"], "cityId": b.get("cityId")})
        else:
            unmapped += 1

    for d in docs:
        await db.branch_performance.replace_one({"id": d["id"]}, d, upsert=True)
    return {"inserted": len(docs), "rejected": len(rows) - len(docs),
            "unmappedBranches": unmapped, "errors": errors[:50], "sourceType": "official"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m data_pipeline.performance.ingest_csv <file.csv>")
    print(asyncio.run(ingest_csv(sys.argv[1])))

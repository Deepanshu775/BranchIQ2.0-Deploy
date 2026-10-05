"""BranchIQ AI Consultant — retrieval-grounded LLM consulting (§21).

Pipeline: user question → intent detection → data retrieval (BranchIQ analytics) →
structured context → LLM → business explanation. The LLM NEVER invents facts; it only
explains the structured analytics payload. Rule-based fallback when no LLM key or on error.
"""

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from data.sources_registry import DEMO_DISCLAIMER, METHODOLOGY_NOTE
from lib import analytics
from lib.db import db
from models.models import ConsultantRequest, ConsultantResponse

logger = logging.getLogger("branchiq.consultant")
router = APIRouter()

PRODUCT_PRINCIPLE = (
    "BranchIQ never claims a regulator or the bank must open a branch. Based on public banking "
    "data, market indicators, network presence, competitor density, geospatial whitespace and "
    "BranchIQ's analytical model, locations are flagged as high-priority opportunities for "
    "further branch feasibility evaluation."
)

SYSTEM_PROMPT = """You are BranchIQ, an AI Banking Network Strategy Consultant for the Indian banking sector.
You operate like a McKinsey/BCG strategy engagement — precise, evidence-led, executive tone. You are NOT a chatbot.

STRICT RULES:
- Use ONLY the DATA CONTEXT provided by the caller (public banking/market indicators, BranchIQ analytical scores, demo-labelled branch layers). Never invent official bank statistics.
- Opportunity, whitespace and cannibalization scores are BranchIQ model-generated estimates, not official figures. Say so when relevant.
- Branch placement and PIN-locality economics in the context are DEMO data for development; never present them as official bank data.
- Never say a bank "MUST open" a branch. Use: "BranchIQ recommends evaluating this location", "high-priority opportunity for further feasibility evaluation".
- Every answer MUST follow the BranchIQ analytical framework and cite the numbers in the context.

You MUST respond with a SINGLE valid JSON object (no markdown, no prose outside JSON) with exactly these keys:
{
  "intent": one of ["LOCATION RECOMMENDATION","DISTRICT ANALYSIS","TOWN ANALYSIS","BANK COMPARISON","MARKET EXPANSION","NETWORK OPTIMIZATION","DIGITAL-FIRST","COMPETITIVE POSITIONING","RISK ANALYSIS","GENERAL"],
  "banks": [bank names detected in the question, else []],
  "executiveAnswer": "1-2 crisp executive sentences answering directly",
  "keyEvidence": ["4-6 short quantitative evidence bullets drawn from the DATA CONTEXT"],
  "opportunityScore": integer 0-100 or null (use scores from context when relevant),
  "businessReasoning": "2-3 sentences of strategic reasoning grounded in the data",
  "recommendedAction": "1-2 sentences, concrete and compliant with the phrasing rules",
  "dataConfidence": "HIGH" | "MEDIUM" | "LIMITED",
  "supportingData": [{"label":"...","value":"...","source":"..."}]  (2-5 items pulled from context)
}
Keep it factual, specific, and tied to the numbers in the DATA CONTEXT."""


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


async def build_retrieval(req: ConsultantRequest) -> dict:
    """Intent-driven data retrieval: enrich the context with BranchIQ analytics server-side."""
    ctx = dict(req.context or {})
    bank = await analytics.resolve_bank(req.selectedBank)
    out: Dict[str, Any] = {
        "methodologyNote": METHODOLOGY_NOTE,
        "productPrinciple": PRODUCT_PRINCIPLE,
        "demoDataNotice": DEMO_DISCLAIMER,
        "scope": "STATE",
    }
    if bank:
        out["bank"] = {k: bank.get(k) for k in
                       ("name", "short", "sector", "reportingPeriod", "branches", "deposits", "advances",
                        "depositGrowth", "creditGrowth", "digitalReadiness", "source")}

    try:
        if ctx.get("locationId") and bank:
            out["scope"] = "LOCATION"
            detail = await analytics.location_detail(ctx["locationId"], req.selectedBank)
            if detail:
                out["locationDetail"] = {
                    "name": detail["name"], "city": detail["city"], "district": detail["district"],
                    "state": detail["state"], "pincode": detail["pincode"], "siteType": detail["siteType"],
                    "score": detail["score"], "baseScore": detail["baseScore"],
                    "decision": detail["decision"]["label"], "priority": detail["priority"],
                    "breakdown": {c["label"]: f'{c["score"]}/100 × {c["weight"]}' for c in detail["breakdown"]},
                    "penalties": detail["penalties"],
                    "cannibalization": detail["cannibalization"],
                    "whitespaceScore": detail["whitespaceScore"],
                    "nearestOwnKm": detail["nearestOwnKm"], "nearestCompetitorKm": detail["nearestCompetitorKm"],
                    "catchment": detail["catchment"], "nearbyOwn": detail["nearbyOwn"][:5],
                    "nearbyCompetitors": detail["nearbyCompetitors"][:5],
                    "market": detail["market"], "evidence": detail["evidence"],
                    "mlProbability": detail["mlPrediction"]["probability"],
                    "confidence": detail["confidence"],
                }
                alts = await analytics.locations_ranked(detail["stateId"], detail["districtId"],
                                                        detail["cityId"], req.selectedBank, limit=6)
                out["cityAlternatives"] = [
                    {"name": a["name"], "score": a["score"], "decision": a["decision"]["label"]}
                    for a in alts if a["id"] != detail["id"]]
        elif ctx.get("cityId") and bank:
            out["scope"] = "CITY"
            rows = await analytics.locations_ranked(ctx.get("stateId"), ctx.get("districtId"),
                                                    ctx["cityId"], req.selectedBank, limit=10)
            out["rankedLocations"] = [{"rank": i + 1, "name": r["name"], "siteType": r["siteType"],
                                       "pincode": r["pincode"], "score": r["score"],
                                       "decision": r["decision"]["label"], "nearestOwnKm": r["nearestOwnKm"],
                                       "cannibalization": r["cannibalization"]["risk"],
                                       "catchmentPop": r["catchmentPop"]} for i, r in enumerate(rows)]
        elif ctx.get("districtId") and bank:
            out["scope"] = "DISTRICT"
            rows = await analytics.cities_ranked(ctx["districtId"], req.selectedBank)
            out["rankedCities"] = [{"name": r["name"], "score": r["overall"], "whitespace": r["whitespace"],
                                    "ownBranches": r["ownBranches"], "competitorBranches": r["competitorBranches"]}
                                   for r in rows[:10]]
        elif ctx.get("stateId") and bank:
            out["scope"] = "DISTRICT"
            rows = await analytics.districts_ranked(ctx["stateId"], req.selectedBank)
            out["rankedDistricts"] = [{"name": r["name"], "score": r["overall"], "ownBranches": r["ownBranches"],
                                       "totalBranches": r["totalBranches"], "priority": r["priority"]}
                                      for r in rows[:10]]
    except Exception as exc:
        logger.error("consultant retrieval error: %s", exc)

    try:
        out["topStates"] = [
            {"state": r["state"], "score": r["score"], "decision": r["decision"]["label"],
             "drivers": [d["label"] for d in r["drivers"]]}
            for r in (await analytics.states_ranked(req.selectedBank))[:6]]
    except Exception as exc:
        logger.error("consultant state context error: %s", exc)
    return out


def _fallback(req: ConsultantRequest, retrieval: dict) -> ConsultantResponse:
    scope = retrieval.get("scope", "STATE")
    bank_short = (retrieval.get("bank") or {}).get("short", "the selected bank")
    if scope == "LOCATION" and retrieval.get("locationDetail"):
        loc = retrieval["locationDetail"]
        evidence = [e["text"] for e in loc.get("evidence", [])][:5]
        return ConsultantResponse(
            intent="LOCATION RECOMMENDATION",
            banks=[bank_short] if req.selectedBank else [],
            executiveAnswer=(f"BranchIQ recommends evaluating {loc['name']} ({loc['city']}, {loc['district']}) "
                             f"for {bank_short} — location opportunity score {loc['score']}/100 ({loc['decision']})."),
            keyEvidence=evidence or [f"Location score {loc['score']}/100"],
            opportunityScore=loc.get("score"),
            businessReasoning=loc.get("cannibalization", {}).get("note", "") +
            " Whitespace, catchment and competitor analysis are computed from the BranchIQ geospatial engine.",
            recommendedAction=("Conduct detailed feasibility for this location; BranchIQ recommends evaluation, "
                               "not a commitment."),
            dataConfidence="MEDIUM",
            supportingData=[{"label": "Opportunity score", "value": f"{loc['score']}/100", "source": "BranchIQ analytical score"},
                            {"label": "Whitespace", "value": f"{loc['whitespaceScore']}/100", "source": "BranchIQ analytical score"},
                            {"label": "Catchment population", "value": f"{loc['catchment']['population']:,}", "source": "Model estimate"},
                            {"label": "Branch layer", "value": "Demo data", "source": "DEMO — synthetic placement"}],
            scope=scope,
        )
    if scope == "CITY" and retrieval.get("rankedLocations"):
        rows = retrieval["rankedLocations"]
        top = rows[0]
        return ConsultantResponse(
            intent="LOCATION RECOMMENDATION",
            banks=[bank_short] if req.selectedBank else [],
            executiveAnswer=(f"Top candidate in this market is {top['name']} (score {top['score']}/100, "
                             f"{top['decision']}) of {len(rows)} evaluated locations."),
            keyEvidence=[f"{r['name']}: score {r['score']}/100, nearest own branch "
                         f"{r['nearestOwnKm'] if r['nearestOwnKm'] is not None else 'n/a'} km, "
                         f"cannibalization {r['cannibalization']}" for r in rows[:5]],
            opportunityScore=top["score"],
            businessReasoning="Ranking combines market growth, credit/deposit potential, bank whitespace, "
                              "competitive balance and cannibalization penalties (BranchIQ analytical model).",
            recommendedAction="Shortlist the top-ranked sites for field feasibility; validate with current "
                              "branch-locator data before any commitment.",
            dataConfidence="MEDIUM",
            supportingData=[{"label": r["name"], "value": f"{r['score']}/100", "source": "BranchIQ analytical score"} for r in rows[:4]],
            scope=scope,
        )
    top_states = retrieval.get("topStates") or []
    if top_states:
        best = top_states[0]
        return ConsultantResponse(
            intent="MARKET EXPANSION",
            banks=[bank_short] if req.selectedBank else [],
            executiveAnswer=f"{best['state']} presents the strongest network opportunity for {bank_short} among the assessed markets.",
            keyEvidence=[f"{s['state']}: BranchIQ Opportunity Score {s['score']}/100" for s in top_states[:4]],
            opportunityScore=best["score"],
            businessReasoning="Market fundamentals in the leading state are attractive while the bank's relative "
                              "network intensity leaves headroom versus the strongest competitors.",
            recommendedAction=f"Evaluate selective physical and digital distribution expansion in {best['state']}; "
                              "further management validation required.",
            dataConfidence="MEDIUM",
            supportingData=[{"label": s["state"], "value": f"{s['score']}/100", "source": "BranchIQ Analytical Score"} for s in top_states[:4]],
            scope=scope,
        )
    return ConsultantResponse(
        intent="GENERAL",
        executiveAnswer="BranchIQ combines public banking and market indicators with an analytical scoring framework to guide network strategy.",
        keyEvidence=["Select a bank and market to generate a data-backed strategic assessment."],
        businessReasoning="Strategic recommendations are derived from public market indicators and BranchIQ analytical scores, not confidential bank data.",
        recommendedAction="Choose a bank and state to receive a structured opportunity assessment; further management validation required.",
        dataConfidence="LIMITED",
        scope=scope,
    )


@router.post("/consultant/ask", response_model=ConsultantResponse)
async def consultant_ask(req: ConsultantRequest):
    retrieval = await build_retrieval(req)
    result: ConsultantResponse | None = None
    used_llm = False
    key = os.environ.get("EMERGENT_LLM_KEY")
    if key:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage

            chat = LlmChat(api_key=key, session_id=f"branchiq-{uuid.uuid4()}",
                           system_message=SYSTEM_PROMPT).with_model("anthropic", "claude-sonnet-4-6")
            payload = (
                f"QUESTION: {req.question}\n\n"
                f"SELECTED BANK: {req.selectedBank or 'None'}\n\n"
                f"RETRIEVAL SCOPE: {retrieval.get('scope')}\n\n"
                f"DATA CONTEXT (JSON):\n{json.dumps(retrieval, ensure_ascii=False, default=str)}\n\n"
                "Respond with the single JSON object as instructed."
            )
            raw = await chat.send_message(UserMessage(text=payload))
            data = _extract_json(raw if isinstance(raw, str) else str(raw))
            if data and data.get("executiveAnswer"):
                result = ConsultantResponse(
                    intent=data.get("intent", "GENERAL"),
                    banks=data.get("banks", []) or [],
                    executiveAnswer=data.get("executiveAnswer", ""),
                    keyEvidence=data.get("keyEvidence", []) or [],
                    opportunityScore=data.get("opportunityScore"),
                    businessReasoning=data.get("businessReasoning", ""),
                    recommendedAction=data.get("recommendedAction", ""),
                    dataConfidence=data.get("dataConfidence", "MEDIUM"),
                    supportingData=data.get("supportingData", []) or [],
                    scope=retrieval.get("scope", "STATE"),
                )
                used_llm = True
        except Exception as exc:
            logger.error("LLM consultant error: %s", exc)
    if result is None:
        result = _fallback(req, retrieval)

    try:
        await db.consultant_queries.insert_one({
            "id": str(uuid.uuid4()),
            "question": req.question,
            "selectedBank": req.selectedBank,
            "scope": retrieval.get("scope", "STATE"),
            "usedLLM": used_llm,
            "response": result.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:
        logger.error("Mongo insert error: %s", exc)
    return result


@router.get("/consultant/history")
async def consultant_history(limit: int = 20):
    docs = await db.consultant_queries.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return docs

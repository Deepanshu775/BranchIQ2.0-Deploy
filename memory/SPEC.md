# BranchIQ 2.0 — SPEC

## What the app does
District → Town/City → PIN → candidate-branch-location expansion intelligence for 9 Indian banks.
Upgrade of BranchIQ 1.0 (state-level only); all 1.0 pages preserved + new "Location Intelligence".

## Stack
FastAPI (`backend/`, port 8001) + MongoDB (motor) + Vite/React 19/TS strict (`frontend/`, port 3000).
No auth — opens directly to the dashboard. Leaflet for maps. Emergent LLM key (Claude Sonnet) for the consultant.

## Data layers (never mixed; every record labelled)
- **official** — bank branch totals/deposits/advances/growth, FY2025 annual reports (`data/banks_base.py`)
- **market** — state/district/town names, populations, approximate coords, Census/OSM (`data/geo_data.py`)
- **analytical/model** — opportunity, whitespace, cannibalization scores (`lib/scoring.py`)
- **ml** — heuristic logistic high-potential probability + signed feature contributions (`lib/ml_model.py`)
- **demo** — branch placement, PIN-locality economics, candidate sites: SYNTHETIC, deterministic (`seed.py`), `sourceType="demo"`

## Data model (Mongo, camelCase fields)
`banks, states, districts, cities, pincodes, branches, market_metrics, location_candidates,
opportunity_scores, model_predictions, data_sources, consultant_queries`.
Ids are string slugs: state `uttar-pradesh`, district `uttar-pradesh::meerut`,
city `uttar-pradesh::meerut::meerut-city::250001`, candidate `<cityId>::cand-N`.
Indexes in `lib/db.py` (`INDEXES`), applied at startup by `ensure_indexes()`.

## Seeded volumes (run `cd /app/backend && python seed.py`)
24 states · 172 districts · 264 cities/towns · 439 PIN areas · 2014 demo branches ·
608 candidate locations · 436 market metric docs. Deterministic (hash-seeded) → reproducible rankings.
Data quality: 0 issues (no invalid coords/PINs, no duplicates, no missing district).

## Engines
- **geo** (`lib/geo.py`) — haversine + 0.12° grid index; radius/nearest queries; catchment rings anchored at 5 km
- **scoring** (`lib/scoring.py`) — location score (15/15/15/15/15/10/5/5/5) less cannibalization + saturation + cost penalties;
  whitespace engine; cannibalization bands (<2 km HIGH, 2–5 MEDIUM, >5 LOW); state engine ported 1:1 from 1.0 (30/20/15/15/10/10)
- **config** — all weights/bands/radii in `data/scoring_config.json` (never hard-coded in the UI)
- Decision bands: 90+ VERY HIGH, 80+ HIGH, 65+ SELECTIVE, 50+ MONITOR/DIGITAL-FIRST, else DO NOT PRIORITIZE

## API (all on `api_router`, prefix `/api`)
`/banks /states /districts?state_id= /cities?district_id= /pincodes?city_id=`
`/branches?bank=&state_id=&district_id=&city_id=&limit=&offset=` · `/competitors?lat=&lng=&radius_km=&exclude_bank=`
`/opportunities/states|districts|cities` · `/market/{district_id}`
`/locations/ranked?state_id|district_id|city_id&bank&min_score&min_population&limit`
`/location/{id}` · `/location/{id}/score` · `/location/{id}/catchment`
`POST /consultant/ask` · `/consultant/history` · `/sources` · `/quality` · `/scoring-config`
Legacy `/status` endpoints preserved.

## Key flows
1. Header bank selector (default HDFC Bank) drives every page.
2. Location Intelligence: state → district → city selects (each clears child levels) → ranked candidates +
   Leaflet map (own/competitor/candidate markers, catchment rings) → detail panel: score breakdown, penalties,
   catchment table, whitespace/cannibalization, "Why this location?" evidence, ML contributions, provenance.
3. AI Consultant: backend does intent detection + analytics retrieval, LLM only explains structured results
   (rule-based fallback). Drill-down scope from AppContext is sent as context.
4. Executive Report modal (print/PDF) adapts to the active scope.
5. Methodology: source registry, data-quality dashboard, live scoring config.

## Frontend conventions
`src/types/api.ts` hand-mirrors every Pydantic model. Data via TanStack Query hooks in `src/lib/branchiq.ts`
(never fetch-in-useEffect). Drill state in `src/context/AppContext.tsx`. Design tokens in `src/lib/theme.ts`.
shadcn/base-ui: `SelectValue` needs a children function (renders raw value otherwise). No accordion/collapsible
installed — use state toggles.

## Backend tests (PRD §29)
Run: `cd /app/backend && python -m pytest tests -q` (118 tests, all passing).
- `tests/test_geo.py` — haversine accuracy/symmetry/edge cases, GeoIndex radius counts vs brute force, cross-cell boundary, nearest(), catchment ring monotonicity + per-ring branch counts.
- `tests/test_scoring.py` — config weight sums, whitespace engine, cannibalization bands/penalties, location score breakdown = base − penalties, saturation/operating-cost penalties, decision bands, evidence points.
- `tests/test_model_and_quality.py` — heuristic ML probability bounds/monotonicity/contributions; PIN + coordinate validation, duplicate-branch detection, quality report issue classes.
- `tests/test_api_endpoints.py` — catalog, /branches pagination + filters, /competitors radius grouping, ranked opportunities ordering, location detail/score/catchment, 404/422 negatives, /quality and /scoring-config.

Bug fixed while testing: `GeoIndex.nearest()` reset its best candidate on every ring, so a center-cell branch could be skipped and a farther branch returned.

## ML layer (PRD §19/§20) — trained XGBoost predictor
- Training data lives in Mongo `branch_performance` (4 fiscal years per branch, 8,056 rows / 2,014 branches).
  - DEMO path: `backend/data_pipeline/performance/generate_panel.py` — deterministic synthetic panel, every row `sourceType="demo-training"` + disclaimer. Never presented as official data.
  - REAL path: `backend/data_pipeline/performance/ingest_csv.py` — columns `branch_id,bank,fiscal_year,deposits_cr,advances_cr[,accounts,source,source_url,source_date]`; validated/deduped/geo-mapped, stored `sourceType="official"`. Training automatically includes it.
- Feature contract (single source of truth): `backend/lib/model_features.py` FEATURE_ORDER (13 features) — used identically for training rows (existing branches) and prediction (candidate locations).
- Trainer: `backend/lib/trainer.py` — label = business (deposits+advances) CAGR in the top tercile; XGBClassifier, 75/25 stratified holdout; artifact + meta persisted to `backend/model_artifacts/`. Current demo-panel metrics: ROC-AUC 0.903, accuracy 0.825.
- Serving: `backend/lib/model_store.py` loads the artifact (hot-reloads on mtime change) and returns probability + real SHAP contributions; `lib/ml_model.predict()` delegates to it and falls back to `heuristic_predict()` when no artifact exists. Response contract unchanged, so location detail/ranked rows need no changes.
- APIs: `GET /api/model/info`, `GET /api/model/training-data`, `POST /api/model/generate-panel`, `POST /api/model/train` (both POSTs require `adminToken` matching `ADMIN_TOKEN` in backend/.env → `branchiq-admin-2026`).
- CLI: `cd /app/backend && python train_model.py --panel`.
- UI: new page `/model` ("Model & Training", frontend/src/pages/ModelLab.tsx) — status, holdout metrics, gain-based feature importance, training-data inventory, admin-gated retrain, demo-data disclaimer.
- Tests: `backend/tests/test_training_pipeline.py` (feature contract, CSV ingestion edge cases, model APIs, auth gating). Full suite now 134 tests, all passing.

## Blended BranchIQ score (PRD §19)
- `scoring.blend_scores(business_score, ml_probability, confidence_level)` → BranchIQ score = business score × businessWeight + ML probability × mlWeight. Weights in `data/scoring_config.json` → `blend` (base 70/30); the ML weight is multiplied by data confidence (HIGH 1.0, MEDIUM 0.8, LOW 0.5, INSUFFICIENT 0.0 → pure business score).
- Returned as `blended` on every ranked location and on `/api/location/{id}` + `/api/location/{id}/score`: businessScore, mlProbability, branchIQScore, weights, confidenceLevel, delta, decision band, priority, plain-English note. Ranked ordering still uses the transparent business score.
- UI: ranked cards show BranchIQ score headline + business/ML row; detail panel has a "Score triangulation" card (`blended-score-card`) with the three figures, weights, delta and decision band.
- Tests: `TestBlendedScore` in test_scoring.py and `TestBlendedScoreApi` in test_api_endpoints.py. Suite now 143 tests, all passing.

"""Branch-performance history pipeline (PRD §19, §23, §34).

Real per-branch deposit/advance history is NOT published by banks or RBI in machine-readable
form, so this package provides two clearly separated paths:

- `generate_panel`  — a deterministic DEMO/TRAINING panel derived from the seeded network.
                      Every row is labelled sourceType="demo-training" and is never presented
                      as official data.
- `ingest_csv`      — the ingestion path for a real historical dataset (validated, normalized,
                      deduplicated, source metadata preserved). Rows land in the same
                      `branch_performance` collection with sourceType="official", so training
                      automatically prefers real data once it exists.
"""

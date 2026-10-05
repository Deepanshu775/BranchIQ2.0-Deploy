"""CLI: build the training panel (if empty) and fit the XGBoost predictor.

    python train_model.py            # train on whatever history is ingested
    python train_model.py --panel    # (re)generate the DEMO/TRAINING panel first, then train
"""

import asyncio
import json
import sys

from data_pipeline.performance.generate_panel import generate_panel, panel_summary
from lib import trainer


async def main() -> None:
    want_panel = "--panel" in sys.argv
    summary = await panel_summary()
    if want_panel or summary["rows"] == 0:
        print("Generating DEMO/TRAINING performance panel...")
        print(json.dumps(await generate_panel(), indent=2)[:400])
    result = await trainer.train()
    print(json.dumps({k: v for k, v in result.items() if k != "featureImportances"}, indent=2))
    for row in result.get("featureImportances", [])[:6]:
        print(f"  {row['feature']:<24} {row['importancePct']:>5}%")
    if result.get("status") != "trained":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())

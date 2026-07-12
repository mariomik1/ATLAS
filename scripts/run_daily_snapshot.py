from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.utils.export_utils import write_model_json


if __name__ == "__main__":
    briefing = AtlasOrchestrator().daily_briefing()
    path = write_model_json(briefing, Path("data/exports/daily_briefing_sample.json"))
    print(f"Wrote {path}")
    print(briefing.headline)
    for rec in briefing.recommendations[:5]:
        print(f"{rec.asset.symbol}: {rec.verdict} score={rec.atlas_score} entry={rec.trade_plan.entry_low}-{rec.trade_plan.entry_high}")

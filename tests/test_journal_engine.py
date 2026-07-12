from pathlib import Path
from atlas_core.engines.journal_engine import JournalEngine
from atlas_core.orchestrator import AtlasOrchestrator


def test_journal_saves_recommendation(tmp_path):
    rec = AtlasOrchestrator().analyze_query("MSFT")
    saved = Path(JournalEngine(tmp_path).save_recommendation(rec))
    assert saved.exists()
    assert "MSFT" in saved.name

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_legacy_seeds_have_provenance_and_are_unpublished() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/export_legacy.py"), "--check"], check=True)
    seeds = json.loads((ROOT / "content/legacy-v1.json").read_text(encoding="utf-8"))
    assert len(seeds["questions"]) == 15
    assert len(seeds["roadmap_suggestions"]) == 24
    assert all(question["status"] == "draft" for question in seeds["questions"])
    assert all(question["rubric"] is None for question in seeds["questions"])
    assert seeds["source_commit"] == "48fcd90"
    assert seeds["topic_aliases"]["OS"] == seeds["topic_aliases"]["Operating System"]

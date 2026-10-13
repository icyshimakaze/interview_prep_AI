"""Export only useful V1 editorial seeds using JSON/AST parsing, never code execution."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "48fcd90"
SOURCE_HASHES = {
    "app.py": "5a6abc9d300423ecbe75ed4afc53c188ea840d34e744b2aebd449a27be622f99",
    "questions.json": "8324fd68ac2c257b5d5c0d4f82406e16b2eb62ea22fbd7a4ffb618ba856a95b9",
    "requirements.txt": "0cbb47835edb89b4addfff09725e98a7aacc8f52e291a9e6e6bffeb2076f1eff",
}
TOPICS = {
    "Arrays": "arrays",
    "Linked List": "linked-list",
    "Stack": "stack",
    "Queue": "queue",
    "DBMS": "dbms",
    "OS": "operating-system",
}


def stable_id(topic: str, text: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"interview-prep/legacy-v1/{topic}/{text}"))


def export_content() -> dict[str, object]:
    for name, expected_hash in SOURCE_HASHES.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"Legacy source changed: {name}. Review before updating provenance.")

    bank: object = json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))
    if not isinstance(bank, dict):
        raise ValueError("Legacy bank must be a topic-to-title mapping")
    questions: list[dict[str, object]] = []
    for topic, titles in bank.items():
        if not isinstance(topic, str) or topic not in TOPICS or not isinstance(titles, list):
            raise ValueError("Invalid legacy question topic")
        for title in titles:
            if not isinstance(title, str) or not title.strip():
                raise ValueError("Legacy titles must be nonempty strings")
            questions.append(
                {
                    "id": stable_id(topic, title),
                    "topic_id": TOPICS[topic],
                    "original_topic": topic,
                    "title": title,
                    "status": "draft",
                    "difficulty": None,
                    "prompt": None,
                    "rubric": None,
                    "source": {"file": "questions.json", "commit": SOURCE_COMMIT},
                    "provenance_review": "required",
                }
            )

    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    roadmaps: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            continue
        test = node.test
        if (
            not isinstance(test.left, ast.Name)
            or test.left.id != "topic"
            or len(test.ops) != 1
            or not isinstance(test.ops[0], ast.Eq)
            or len(test.comparators) != 1
            or not isinstance(test.comparators[0], ast.Constant)
        ):
            continue
        topic = test.comparators[0].value
        if not isinstance(topic, str) or topic not in TOPICS:
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
                continue
            call = statement.value
            if (
                not isinstance(call.func, ast.Attribute)
                or call.func.attr != "write"
                or not isinstance(call.func.value, ast.Name)
                or call.func.value.id != "st"
                or len(call.args) != 1
                or not isinstance(call.args[0], ast.Constant)
            ):
                continue
            text = call.args[0].value
            if isinstance(text, str) and text.startswith("Week "):
                roadmaps.append(
                    {
                        "id": stable_id(topic, text),
                        "topic_id": TOPICS[topic],
                        "original_topic": topic,
                        "original_text": text,
                        "status": "editorial_seed",
                        "source": {
                            "file": "app.py",
                            "line": statement.lineno,
                            "commit": SOURCE_COMMIT,
                        },
                    }
                )
    if len(questions) != 15 or len({item["id"] for item in questions}) != 15 or len(roadmaps) != 24:
        raise ValueError("Legacy reconciliation requires 15 unique titles and 24 roadmap strings")
    return {
        "schema_version": 1,
        "source_commit": SOURCE_COMMIT,
        "source_sha256": SOURCE_HASHES,
        "usage": (
            "Unpublished editorial seeds; no assessment evidence, "
            "training data, or scheduled tasks."
        ),
        "topic_aliases": {**TOPICS, "Operating System": "operating-system"},
        "questions": questions,
        "roadmap_suggestions": roadmaps,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "content" / "legacy-v1.json"
    serialized = json.dumps(export_content(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != serialized:
            raise SystemExit("Legacy seed drift: run scripts/export_legacy.py")
        print("Legacy hashes and seeds verified: 15 titles, 24 roadmap suggestions.")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8", newline="\n")
        print("Exported 15 draft titles and 24 editorial suggestions to content/legacy-v1.json.")


if __name__ == "__main__":
    main()

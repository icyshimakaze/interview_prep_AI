from io import BytesIO
from zipfile import ZIP_STORED, ZipFile, ZipInfo


def example_archive() -> bytes:
    """Small authored illustrative source fixture. It is analyzed, never executed."""
    files = {
        "example/README.md": "# Illustrative task tracker\nOffline teaching fixture, not a "
        "production or audited application.\n",
        "example/backend/requirements.txt": "fastapi\nsqlalchemy\nasyncpg\npyjwt\npytest\n",
        "example/backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"
        '@app.get("/tasks")\n'
        "def list_tasks():\n    return []\n",
        "example/backend/models.py": "from pydantic import BaseModel\nclass "
        "Task(BaseModel):\n    title: str\n",
        "example/frontend/package.json": '{"dependencies":{"react":"example","next":"example"}}',
        "example/frontend/App.tsx": "export interface Task { title: string }\n",
        "example/tests/test_tasks.py": "def test_placeholder():\n    assert True\n",
        "example/.github/workflows/check.yml": "name: Example checks\non: push\njobs: {}\n",
        "example/Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\n",
        "example/compose.yaml": "services:\n  database:\n    image: postgres:18\n",
    }
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        for path, text in sorted(files.items()):
            archive.writestr(ZipInfo(path, date_time=(2026, 1, 1, 0, 0, 0)), text)
    return output.getvalue()

"""Private bounded parser process; repository bytes never become filesystem entries."""

import json
import logging
import sys

from interview_prep.modules.projects.analyzer import analyze
from interview_prep.modules.projects.archive import MAX_ARCHIVE, UnsafeArchive
from interview_prep.modules.resumes.worker_limits import restrict_memory


def main() -> None:
    logging.disable(logging.CRITICAL)
    try:
        restrict_memory()
    except Exception:
        sys.stdout.write('{"error":"project_worker_unavailable"}')
        return
    try:
        data = sys.stdin.buffer.read(MAX_ARCHIVE + 1)
        result = analyze(data).model_dump_json()
    except UnsafeArchive as exc:
        result = json.dumps({"error": str(exc)})
    except Exception:
        result = '{"error":"archive_corrupt"}'
    sys.stdout.write(result)


if __name__ == "__main__":
    main()

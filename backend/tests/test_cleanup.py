"""Exercise maintenance imports in a fresh interpreter, outside pytest's registry."""

import subprocess
import sys

from test_support import mock_environment


def test_standalone_cleanup_registers_all_referenced_models() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import interview_prep.cleanup\n"
            "from sqlalchemy.orm import configure_mappers\n"
            "configure_mappers()\n",
        ],
        env=mock_environment(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr

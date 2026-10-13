"""Create local-only configuration without printing secrets or overwriting existing files."""

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    target = ROOT / ".env"
    if target.exists():
        print("Existing .env preserved.")
        return
    template = (ROOT / ".env.example").read_text(encoding="utf-8")
    password = secrets.token_hex(24)
    template = template.replace("replace-with-a-random-local-password", password)
    template = template.replace("replace-with-at-least-32-random-characters", secrets.token_hex(32))
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(template)
    print("Created ignored .env with random local credentials.")


if __name__ == "__main__":
    main()

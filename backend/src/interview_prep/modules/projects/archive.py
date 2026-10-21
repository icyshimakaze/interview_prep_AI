"""Read bounded ZIP members in memory. Never extract or resolve repository paths."""

import hashlib
import re
import stat
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile

MAX_ARCHIVE = 10 * 1024 * 1024
MAX_EXPANDED = 40 * 1024 * 1024
MAX_MEMBER = 262144
MAX_ENTRIES = 3000
IGNORED = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "coverage",
    ".ssh",
    ".aws",
    ".azure",
    ".terraform",
}
LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".vue": "Vue",
    ".svelte": "Svelte",
}
TEXT_SUFFIXES = set(LANGUAGES) | {
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".md",
    ".txt",
    ".xml",
    ".prisma",
}
TEXT_NAMES = {"dockerfile", "containerfile", "makefile", "jenkinsfile", "gemfile", "go.mod"}


class UnsafeArchive(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    path: str
    text: str
    digest: str
    size: int


def safe_path(name: str) -> str:
    if (
        not name
        or len(name) > 500
        or name.startswith("/")
        or name.endswith("//")
        or "\\" in name
        or ":" in name
        or any(unicodedata.category(c).startswith("C") for c in name)
        or unicodedata.normalize("NFKC", name) != name
    ):
        raise UnsafeArchive("archive_path")
    parts = name.rstrip("/").split("/")
    if any(
        p in {"", ".", ".."}
        or p.endswith((" ", "."))
        or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
        for p in parts
    ):
        raise UnsafeArchive("archive_path")
    return "/".join(parts)


def ignored(path: str) -> bool:
    parts = path.lower().split("/")
    name = parts[-1]
    return (
        any(p in IGNORED for p in parts)
        or name.startswith((".env", ".npmrc", ".pypirc"))
        or any(word in name for word in ("credential", "secret", "id_rsa", "id_ed25519"))
        or name.endswith((".pem", ".key", ".p12", ".pfx", ".lock", "-lock.json", ".min.js", ".map"))
    )


def read_archive(data: bytes) -> tuple[list[Source], int, bool]:
    if not data or len(data) > MAX_ARCHIVE:
        raise UnsafeArchive("archive_size")
    try:
        with ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_ENTRIES:
                raise UnsafeArchive("archive_limits")
            seen: set[str] = set()
            total = 0
            members = []
            for entry in entries:
                path = safe_path(entry.orig_filename)
                normalized = path.casefold()
                if normalized in seen:
                    raise UnsafeArchive("archive_duplicate")
                seen.add(normalized)
                mode = entry.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if (
                    kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or (kind == stat.S_IFDIR) != entry.is_dir()
                    and kind != 0
                ):
                    raise UnsafeArchive("archive_link")
                if entry.flag_bits & 1 or entry.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                    raise UnsafeArchive("archive_format")
                total += entry.file_size
                if (
                    total > MAX_EXPANDED
                    or entry.file_size > MAX_ARCHIVE
                    or entry.file_size > max(1, entry.compress_size) * 200
                ):
                    raise UnsafeArchive("archive_limits")
                if not entry.is_dir():
                    members.append((path, entry))
            file_paths = {path.casefold() for path, _ in members}
            for path in seen:
                segments = path.split("/")
                if any("/".join(segments[:i]) in file_paths for i in range(1, len(segments))):
                    raise UnsafeArchive("archive_duplicate")
            result: list[Source] = []
            skipped = 0
            truncated = False
            for path, entry in sorted(members, key=lambda item: item[0]):
                if ignored(path):
                    skipped += 1
                    continue
                name = PurePosixPath(path).name.lower()
                suffix = PurePosixPath(path).suffix.lower()
                if (
                    ignored(path)
                    or entry.file_size > MAX_MEMBER
                    or (
                        suffix not in TEXT_SUFFIXES
                        and name not in TEXT_NAMES
                        and not name.startswith("dockerfile.")
                    )
                ):
                    skipped += 1
                    continue
                if len(result) >= 500:
                    skipped += 1
                    truncated = True
                    continue
                with archive.open(entry) as stream:
                    raw = stream.read(MAX_MEMBER + 1)
                if len(raw) > MAX_MEMBER or len(raw) != entry.file_size:
                    raise UnsafeArchive("archive_limits")
                try:
                    text = raw.decode("utf-8-sig")
                except UnicodeError:
                    skipped += 1
                    continue
                if "\x00" in text:
                    skipped += 1
                    continue
                result.append(Source(path, text, hashlib.sha256(raw).hexdigest(), len(raw)))
            if not result:
                raise UnsafeArchive("archive_no_source")
            return result, skipped, truncated
    except (BadZipFile, RuntimeError, NotImplementedError, EOFError, OSError):
        raise UnsafeArchive("archive_corrupt") from None

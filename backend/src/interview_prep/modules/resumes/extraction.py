"""Versioned lexical mentions and section excerpts, never competence judgments."""

import re
from dataclasses import dataclass

EXTRACTION_VERSION = "lexical-sections-v1"
MAX_EVIDENCE = 100

# Conservative vocabulary: omit ambiguous one-letter languages and bare 'Go'.
VOCABULARY: dict[str, tuple[tuple[str, str], ...]] = {
    "language": tuple(
        (name, re.escape(name))
        for name in (
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C++",
            "C#",
            "Rust",
            "Kotlin",
            "Swift",
            "Ruby",
            "PHP",
            "SQL",
            "Bash",
            "Dart",
            "Scala",
            "MATLAB",
        )
    )
    + (("Golang", r"golang"),),
    "framework": (
        ("React", r"react(?:\.js)?"),
        ("Next.js", r"next\.js"),
        ("Vue", r"vue(?:\.js)?"),
        ("Angular", r"angular"),
        ("Django", r"django"),
        ("Flask", r"flask"),
        ("FastAPI", r"fastapi"),
        ("Spring", r"spring(?: boot)?"),
        ("Express", r"express\.js"),
        (".NET", r"\.net"),
        ("Rails", r"(?:ruby on )?rails"),
        ("Laravel", r"laravel"),
        ("Flutter", r"flutter"),
        ("Svelte", r"svelte"),
    ),
    "database": (
        ("PostgreSQL", r"postgres(?:ql)?"),
        ("MySQL", r"mysql"),
        ("SQLite", r"sqlite"),
        ("MongoDB", r"mongodb"),
        ("Redis", r"redis"),
        ("SQL Server", r"sql server"),
        ("DynamoDB", r"dynamodb"),
        ("Cassandra", r"cassandra"),
    ),
    "tool": (
        ("Git", r"git"),
        ("GitHub", r"github"),
        ("Docker", r"docker"),
        ("Kubernetes", r"kubernetes|k8s"),
        ("Node.js", r"node\.js"),
        ("AWS", r"aws|amazon web services"),
        ("Azure", r"azure"),
        ("Google Cloud", r"google cloud|gcp"),
        ("Terraform", r"terraform"),
        ("Linux", r"linux"),
        ("Jenkins", r"jenkins"),
        ("Figma", r"figma"),
        ("Jira", r"jira"),
        ("Pandas", r"pandas"),
        ("NumPy", r"numpy"),
        ("PyTorch", r"pytorch"),
        ("TensorFlow", r"tensorflow"),
    ),
}
HEADINGS: dict[str, str] = {
    "projects": "project",
    "selected projects": "project",
    "personal projects": "project",
    "academic projects": "project",
    "education": "education",
    "academic background": "education",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "internships": "experience",
}
OTHER_HEADINGS = {
    "skills",
    "technical skills",
    "summary",
    "profile",
    "interests",
    "certifications",
    "awards",
    "languages",
    "tools",
    "publications",
    "contact",
    "references",
    "achievements",
}
EXPERIENCE = re.compile(
    r"\b(?:intern(?:ship)?|engineer|developer|analyst|consultant|manager|"
    r"designed|built|implemented|maintained|deployed|led|mentored|tested)\b",
    re.I,
)
EDUCATION = re.compile(
    r"\b(?:bachelor(?:['’]s)?|master(?:['’]s)?|doctorate|ph\.?d\.?|"
    r"b\.?tech|m\.?tech|b\.?sc|m\.?sc|diploma|associate degree)\b",
    re.I,
)
PROJECT = re.compile(r"^(?:selected |personal |academic )?project\s*:", re.I)


@dataclass(frozen=True)
class Mention:
    category: str
    claim: str
    source_excerpt: str
    source_page: int
    source_start: int
    source_end: int


def extract_evidence(pages: list[str]) -> tuple[list[Mention], str | None]:
    """Offsets are within normalized extracted text of the indicated page.

    Even negated/aspirational mentions retain their excerpt and remain proposed.
    No score, missing-skill list, experience duration or competence is inferred.
    """
    found: list[Mention] = []
    seen: set[tuple[str, str]] = set()
    active_section: str | None = None
    truncated = False
    for page_number, page in enumerate(pages, 1):
        offset = 0
        for raw in page.splitlines(keepends=True):
            text = raw.strip()
            start = offset + len(raw) - len(raw.lstrip())
            offset += len(raw)
            if not text:
                continue
            heading = text.strip(": ").casefold()
            if heading in HEADINGS or heading in OTHER_HEADINGS:
                active_section = HEADINGS.get(heading)
                continue
            excerpt = text[:500]
            candidates: list[tuple[str, str, str, int]] = []
            for category, entries in VOCABULARY.items():
                for label, expression in entries:
                    match = re.search(r"(?<![\w])(?:" + expression + r")(?![\w])", text, re.I)
                    if match:
                        window = max(0, match.start() - 150)
                        candidates.append(
                            (category, label, text[window : window + 500], start + window)
                        )
            if active_section and len(text) >= 3:
                candidates.append((active_section, excerpt, excerpt, start))
            elif PROJECT.search(text):
                candidates.append(("project", excerpt, excerpt, start))
            elif EDUCATION.search(text):
                match = EDUCATION.search(text)
                window = max(0, match.start() - 150) if match else 0
                context = text[window : window + 500]
                candidates.append(("education", context, context, start + window))
            elif EXPERIENCE.search(text):
                match = EXPERIENCE.search(text)
                window = max(0, match.start() - 150) if match else 0
                context = text[window : window + 500]
                candidates.append(("experience", context, context, start + window))
            for category, claim, source, source_start in candidates:
                key = (category, claim.casefold())
                if key in seen:
                    continue
                seen.add(key)
                if len(found) >= MAX_EVIDENCE:
                    truncated = True
                    continue
                found.append(
                    Mention(
                        category,
                        claim,
                        source,
                        page_number,
                        source_start,
                        source_start + len(source),
                    )
                )
    note = (
        "evidence_limit" if truncated else "no_text" if not any(p.strip() for p in pages) else None
    )
    return found, note

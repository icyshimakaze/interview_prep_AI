"""Versioned syntactic signals. No imports, evaluation, shell, network or code execution."""

import ast
import json
import re
import tomllib
from collections import Counter
from pathlib import PurePosixPath

from interview_prep.modules.projects.archive import LANGUAGES, Source, read_archive
from interview_prep.modules.projects.schemas import (
    AnalysisSummary,
    FactKind,
    FileFact,
    StaticAnalysis,
    StaticFact,
)

FRAMEWORKS = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "express": "Express",
    "@nestjs/core": "NestJS",
    "@angular/core": "Angular",
    "spring-boot-starter-web": "Spring Boot",
    "rails": "Rails",
    "laravel/framework": "Laravel",
}
DATABASES = {
    "psycopg": "PostgreSQL",
    "psycopg2": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "pg": "PostgreSQL",
    "mysql2": "MySQL",
    "pymysql": "MySQL",
    "pymongo": "MongoDB",
    "mongoose": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "ioredis": "Redis",
    "better-sqlite3": "SQLite",
    "sqlite3": "SQLite",
    "sqlalchemy": "SQLAlchemy ORM (database engine not established)",
    "prisma": "Prisma ORM (database engine not established)",
}
AUTH = {"pyjwt", "jose", "python-jose", "passport", "jsonwebtoken", "@clerk/nextjs", "next-auth"}
BACKEND = {
    "FastAPI",
    "Django",
    "Flask",
    "Starlette",
    "Express",
    "NestJS",
    "Spring Boot",
    "Rails",
    "Laravel",
}
FRONTEND = {"React", "Next.js", "Vue", "Nuxt", "Svelte", "Angular"}
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,79}\Z")
DEPENDENCY = re.compile(r"(?:@[a-zA-Z0-9_.-]+/)?[a-zA-Z0-9][a-zA-Z0-9_./-]{0,79}\Z")


def dependencies(source: Source) -> list[tuple[str, int]]:
    name = PurePosixPath(source.path).name.lower()
    names: list[str] = []
    try:
        if name in {"package.json", "composer.json"}:
            data = json.loads(source.text)
            if isinstance(data, dict):
                for key in (
                    "dependencies",
                    "devDependencies",
                    "peerDependencies",
                    "require",
                    "require-dev",
                ):
                    items = data.get(key)
                    if isinstance(items, dict):
                        names.extend(k for k in items if isinstance(k, str))
        elif name in {"pyproject.toml", "cargo.toml"}:
            parsed = tomllib.loads(source.text)
            for key in ("dependencies", "dev-dependencies"):
                values = parsed.get(key)
                if isinstance(values, dict):
                    names.extend(values.keys())
            project = parsed.get("project", {})
            if isinstance(project, dict):
                values = project.get("dependencies", [])
                if isinstance(values, list):
                    names.extend(v for v in values if isinstance(v, str))
                groups = project.get("optional-dependencies", {})
                if isinstance(groups, dict):
                    for values in groups.values():
                        if isinstance(values, list):
                            names.extend(v for v in values if isinstance(v, str))
            tool = parsed.get("tool", {})
            if isinstance(tool, dict) and isinstance(tool.get("poetry"), dict):
                values = tool["poetry"].get("dependencies", {})
                if isinstance(values, dict):
                    names.extend(values.keys())
        elif name.startswith("requirements") and name.endswith(".txt"):
            names = [
                line.strip()
                for line in source.text.splitlines()
                if not line.lstrip().startswith(("#", "-"))
            ]
        elif name == "pom.xml":
            names = re.findall(
                r"<artifactId>\s*([A-Za-z0-9_.-]{1,80})\s*</artifactId>", source.text
            )
        elif name == "gemfile":
            names = re.findall(r"^\s*gem\s+['\"]([A-Za-z0-9_-]{1,80})['\"]", source.text, re.M)
        elif name == "go.mod":
            names = re.findall(
                r"^\s*(?:require\s+)?([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)\s+v[0-9]", source.text, re.M
            )
    except (ValueError, RecursionError):
        return []
    found: dict[str, int] = {}
    for value in names:
        package = re.split(r"[\s\[<>=!~;]", value, maxsplit=1)[0]
        if DEPENDENCY.fullmatch(package) and ":" not in package:
            offset = source.text.find(package)
            found.setdefault(package.lower(), source.text[: max(0, offset)].count("\n") + 1)
    return sorted(found.items())[:80]


def analyze(data: bytes) -> StaticAnalysis:
    sources, skipped, truncated = read_archive(data)
    facts: list[StaticFact] = []
    files: list[FileFact] = []
    languages: Counter[str] = Counter()
    seen: set[tuple[str, str, str]] = set()

    def add(
        source: Source, kind: FactKind, description: str, line: int = 1, inferred: bool = False
    ) -> None:
        nonlocal truncated
        key = (source.path, kind, description)
        if key in seen:
            return
        if len(facts) >= 600:
            truncated = True
            return
        seen.add(key)
        facts.append(
            StaticFact(
                path=source.path, kind=kind, description=description, line=line, inferred=inferred
            )
        )

    for source in sources:
        path = PurePosixPath(source.path)
        name, suffix = path.name.lower(), path.suffix.lower()
        language = LANGUAGES.get(suffix)
        lines = source.text.splitlines()
        files.append(
            FileFact(
                path=source.path,
                sha256=source.digest,
                byte_count=source.size,
                line_count=source.text.count("\n") + 1,
                language=language,
            )
        )
        if language:
            languages[language] += 1
        if (
            name
            in {
                "package.json",
                "pyproject.toml",
                "cargo.toml",
                "go.mod",
                "pom.xml",
                "composer.json",
                "gemfile",
            }
            or name.startswith("requirements")
            and name.endswith(".txt")
        ):
            add(
                source,
                "manifest",
                "Package manifest present; scripts and dependency specifications are not "
                "executed or retained.",
            )
        for dependency, line in dependencies(source):
            add(source, "dependency", f"Declared dependency: {dependency}", line)
            if dependency in FRAMEWORKS:
                framework = FRAMEWORKS[dependency]
                add(source, "framework", f"Declared framework dependency: {framework}", line)
                if framework in BACKEND | FRONTEND:
                    component = "backend" if framework in BACKEND else "frontend"
                    add(
                        source,
                        "component",
                        f"Probable {component} component based on {framework}; runtime wiring "
                        "is unverified.",
                        line,
                        True,
                    )
            if dependency in DATABASES:
                add(
                    source,
                    "database",
                    f"Possible persistence technology: {DATABASES[dependency]}; a dependency "
                    "does not prove deployment.",
                    line,
                    True,
                )
            if dependency in AUTH:
                add(
                    source,
                    "authentication",
                    f"Authentication-related dependency: {dependency}; enforcement is unverified.",
                    line,
                    True,
                )
        if (
            name.startswith(("test_", "test."))
            or any(p in {"tests", "test", "__tests__"} for p in path.parts)
            or re.search(r"[._](test|spec)\.", name)
        ):
            add(source, "tests", "Test-named source file present; tests were not run.")
        if ".github/workflows/" in source.path or name in {
            ".gitlab-ci.yml",
            "jenkinsfile",
            "azure-pipelines.yml",
        }:
            add(source, "ci", "CI configuration present; its execution and status are unverified.")
        if name.startswith(("dockerfile", "containerfile")) or name in {
            "compose.yaml",
            "compose.yml",
            "docker-compose.yml",
            "docker-compose.yaml",
        }:
            add(source, "docker", "Container configuration present; no image was built or started.")
        if suffix == ".md" or name.startswith("readme"):
            add(
                source,
                "documentation",
                "Documentation file present; content is untrusted and not treated as instructions.",
            )
        if name.endswith(".prisma") or suffix in {".yaml", ".yml"} and "compose" in name:
            for line, value in enumerate(lines, 1):
                match = re.search(
                    r"(?:provider\s*=\s*[\"']|image:\s*)(postgresql|postgres|mysql|mariadb|mongodb|mongo|redis|sqlite)\b",
                    value,
                )
                if match:
                    add(
                        source,
                        "database",
                        f"Configuration references {match[1]}; actual runtime usage is unverified.",
                        line,
                        True,
                    )
        if suffix == ".py":
            try:
                tree = ast.parse(source.text)
            except (SyntaxError, ValueError, RecursionError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and IDENTIFIER.fullmatch(node.name):
                    bases = [ast.unparse(b) for b in node.bases]
                    if any(
                        b.split(".")[-1]
                        in {"BaseModel", "Model", "Base", "DeclarativeBase", "TypedDict"}
                        for b in bases
                    ):
                        add(
                            source,
                            "schema",
                            f"Schema/model-shaped class declaration: {node.name}; semantics "
                            "are inferred from base names.",
                            node.lineno,
                            True,
                        )
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        if (
                            isinstance(decorator, ast.Call)
                            and isinstance(decorator.func, ast.Attribute)
                            and decorator.func.attr
                            in {"get", "post", "put", "delete", "patch", "route"}
                            and decorator.args
                        ):
                            arg = decorator.args[0]
                            if (
                                isinstance(arg, ast.Constant)
                                and isinstance(arg.value, str)
                                and safe_route(arg.value)
                            ):
                                add(
                                    source,
                                    "route",
                                    f"Route-shaped decorator: {decorator.func.attr.upper()} "
                                    f"{arg.value}; prefixes and exposure are unverified.",
                                    node.lineno,
                                    True,
                                )
        elif suffix in {".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".go", ".prisma", ".sql"}:
            for line, value in enumerate(lines, 1):
                match = re.search(
                    r"\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]{1,120})['\"]", value
                )
                if match and safe_route(match[2]):
                    add(
                        source,
                        "route",
                        f"Route-shaped call: {match[1].upper()} {match[2]}; registration and "
                        "exposure are unverified.",
                        line,
                        True,
                    )
                shape = re.search(
                    r"\b(?:interface|model|CREATE\s+TABLE|class)\s+([A-Za-z_][A-Za-z0-9_]{0,79})\b",
                    value,
                    re.I,
                )
                if shape:
                    add(
                        source,
                        "schema",
                        f"Model/type-shaped declaration: {shape[1]}; static heuristic only.",
                        line,
                        True,
                    )
    return StaticAnalysis(
        summary=AnalysisSummary(
            languages=dict(sorted(languages.items())),
            skipped_files=skipped,
            truncated=truncated,
            notes=[
                "Static inspection only: no code, tests, scripts or containers were executed.",
                "Only bounded UTF-8 source/configuration files are inspected. Ignored files "
                "and dynamic wiring are not covered.",
                "Architecture, routes, models and persistence signals are hypotheses, not "
                "verified runtime behavior.",
            ],
        ),
        files=files,
        facts=facts,
    )


def safe_route(value: str) -> bool:
    return bool(re.fullmatch(r"/[A-Za-z0-9_/:{}.*-]{0,119}", value)) and not re.search(
        r"[A-Za-z0-9_-]{40}", value
    )

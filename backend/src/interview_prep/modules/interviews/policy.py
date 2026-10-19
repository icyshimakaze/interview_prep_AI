"""Pure, versioned interview coverage and state policy."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import NoReturn

from fastapi import HTTPException

from interview_prep.modules.interviews.schemas import InterviewType

VERSION = "interview-v1"
Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


FUNDAMENTALS = {
    "Data Structures",
    "Algorithms",
    "OOP",
    "DBMS",
    "SQL",
    "Operating Systems",
    "Computer Networks",
}
BACKEND = {"Backend", "DBMS", "SQL", "Computer Networks", "OOP"}
CATEGORIES: dict[InterviewType, set[str]] = {
    InterviewType.FUNDAMENTALS: FUNDAMENTALS,
    InterviewType.BACKEND: BACKEND,
    InterviewType.FRONTEND: {"Frontend"},
    InterviewType.FULL_STACK: BACKEND | {"Frontend"},
    InterviewType.SYSTEM_DESIGN: {"System Design"},
    InterviewType.BEHAVIORAL: {"Behavioral"},
    InterviewType.MIXED: FUNDAMENTALS | BACKEND | {"Frontend", "System Design", "Behavioral"},
}
LABELS = {t: t.value.replace("_", " ").title() for t in InterviewType}


def conflict(code: str = "interview_state") -> NoReturn:
    raise HTTPException(status_code=409, detail=code)


def family(category: str) -> str:
    return (
        category
        if category in {"Backend", "Frontend", "System Design", "Behavioral"}
        else "fundamentals"
    )


def required(type_: InterviewType) -> set[str]:
    if type_ == InterviewType.FULL_STACK:
        return {"Backend", "Frontend"}
    return {"Backend"} if type_ == InterviewType.BACKEND else set()


def feasible(type_: InterviewType, categories: list[str], count: int) -> bool:
    return (
        len(categories) >= count
        and required(type_).issubset(categories)
        and (
            type_ != InterviewType.MIXED or count == 1 or len({family(c) for c in categories}) >= 2
        )
    )


def clean_text(value: str | None) -> str | None:
    return value if value and value.strip() else None

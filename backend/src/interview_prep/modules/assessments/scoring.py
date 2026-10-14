"""Objective scoring policies are explicit, versioned and server-only."""

from uuid import UUID


def score_options(selected: list[UUID], correct: list[UUID]) -> int:
    """Exact set equality: one point for the complete correct set, zero otherwise."""
    return int(bool(correct) and set(selected) == set(correct))


def score_short_answer(response: str, keys: list[tuple[str, str]]) -> int:
    """literal-v1 ignores surrounding whitespace only; unsupported policies fail closed."""
    if not keys or any(version != "literal-v1" for _, version in keys):
        raise ValueError("Unsupported short-answer normalization")
    return int(any(response.strip() == answer.strip() for answer, _ in keys))

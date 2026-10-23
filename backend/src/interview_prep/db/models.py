"""Explicit metadata registry used by Alembic, tests, and data tooling."""

from interview_prep.ai import analysis_models as ai_analyses
from interview_prep.core import security_models as security
from interview_prep.db.base import Base
from interview_prep.modules.assessments import models as assessments
from interview_prep.modules.context import models as context
from interview_prep.modules.demo import models as demo
from interview_prep.modules.identity import models as identity
from interview_prep.modules.interviews import models as interviews
from interview_prep.modules.interviews import work_models as interview_work
from interview_prep.modules.projects import defense_models as project_defense
from interview_prep.modules.projects import models as projects
from interview_prep.modules.questions import models as questions
from interview_prep.modules.roadmaps import models as roadmaps

__all__ = [
    "Base",
    "ai_analyses",
    "security",
    "assessments",
    "context",
    "demo",
    "identity",
    "interviews",
    "interview_work",
    "projects",
    "project_defense",
    "questions",
    "roadmaps",
]

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DemoWorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    expires_at: datetime
    kind: Literal["demo"] = "demo"

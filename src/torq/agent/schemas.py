"""Structured data models for the diagnosis agent and work orders."""

from pydantic import BaseModel, Field


class Diagnosis(BaseModel):
    fault_code: str
    machine: str = ""
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    repair_steps: list[str] = []
    parts: list[str] = []
    tools: list[str] = []
    safety_warnings: list[str] = []
    sources: list[str] = []


class WorkOrder(BaseModel):
    id: str
    fault_code: str
    machine: str = ""
    root_cause: str
    repair_steps: list[str] = []
    parts: list[str] = []
    tools: list[str] = []
    safety_warnings: list[str] = []
    required_skill: str = "general"
    content: dict[str, str] = {}  # language code (fr/ar/en) -> formatted text
    status: str = "pending"  # pending | approved | rejected | dispatched
    assigned_to: str | None = None
    confidence: float = 0.5

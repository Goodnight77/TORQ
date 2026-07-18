"""Structured data models for the diagnosis agent."""

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

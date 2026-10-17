from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(min_length=5, max_length=3000)
    image_base64: str | None = Field(default=None, max_length=7_000_000)
    corpus: Literal["live", "demo"] = "live"


class Evidence(BaseModel):
    id: str
    title: str
    url: str
    excerpt: str
    kind: Literal["search_grounded_excerpt", "demo_fixture", "source_page_excerpt", "image_match_lead"]


class Finding(BaseModel):
    claim: str
    status: Literal["supported", "contradicted", "unresolved"]
    explanation: str
    evidence_ids: list[str]


class Assessment(BaseModel):
    summary: str
    findings: list[Finding]
    limitations: list[str]


class Review(BaseModel):
    accepted: bool
    issues: list[str]


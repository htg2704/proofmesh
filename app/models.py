from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime, field_validator


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(min_length=5, max_length=3000)
    image_base64: str | None = Field(default=None, max_length=7_000_000)
    corpus: Literal["live", "demo", "review"] = "live"
    published_at: AwareDatetime | None = None
    source_url: str | None = Field(default=None, max_length=2000)

    @field_validator("source_url")
    @classmethod
    def safe_source_url(cls, value):
        if value:
            from urllib.parse import urlsplit
            u = urlsplit(value)
            if u.scheme != "https" or not u.hostname or u.username or u.password:
                raise ValueError("Source links must be HTTPS without embedded credentials")
        return value


class Evidence(BaseModel):
    id: str
    title: str
    url: str
    excerpt: str
    kind: Literal["search_grounded_excerpt", "demo_fixture", "source_page_excerpt", "image_match_lead"]


class EvidenceQuote(BaseModel):
    evidence_id: str
    quote: str = Field(min_length=5, max_length=500)


class Finding(BaseModel):
    claim: str
    status: Literal["supported", "contradicted", "unresolved"]
    explanation: str
    evidence_ids: list[str]
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)


class ContextCheck(BaseModel):
    dimension: Literal["date", "location", "media_identity"]
    claimed: str
    observed: str
    status: Literal["supported", "contradicted", "unresolved"]
    evidence_ids: list[str]
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)


class Assessment(BaseModel):
    summary: str
    findings: list[Finding]
    limitations: list[str]
    context_checks: list[ContextCheck] = Field(default_factory=list)


class Review(BaseModel):
    accepted: bool
    issues: list[str]


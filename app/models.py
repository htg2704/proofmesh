from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, AwareDatetime, field_validator, PrivateAttr


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(min_length=5, max_length=3000)
    image_base64: str | None = Field(default=None, max_length=7_000_000)
    corpus: Literal["live", "demo", "review"] = "live"
    published_at: AwareDatetime | None = None
    source_url: str | None = Field(default=None, max_length=2000)
    share_publicly: bool = False
    provider_api_key: str | None = Field(default=None, min_length=20, max_length=512, exclude=True, repr=False, json_schema_extra={"writeOnly": True})
    _client_id: str | None = PrivateAttr(default=None)

    @property
    def namespace(self):
        return 'client:' + self._client_id if self._client_id else self.corpus

    def for_client(self, identifier):
        import re
        if not re.fullmatch(r'[0-9a-f]{24}', identifier):
            raise ValueError('Invalid client identifier')
        scoped = self.model_copy(deep=True)
        scoped.corpus = 'live'
        scoped._client_id = identifier
        return scoped

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
    quote: str = Field(default='', max_length=500)
    passage_id: str | None = Field(default=None, max_length=40)


class Finding(BaseModel):
    claim: str
    status: Literal["supported", "contradicted", "unresolved"]
    explanation: str
    evidence_ids: list[str]
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)
    assessment_issue: str | None = None


class ContextCheck(BaseModel):
    dimension: Literal["date", "location", "media_identity"]
    claimed: str
    observed: str
    status: Literal["supported", "contradicted", "unresolved"]
    evidence_ids: list[str]
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)
    assessment_issue: str | None = None


class SourceReportedOrigin(BaseModel):
    classification: Literal['reported_ai_generated', 'reported_edited', 'reported_authentic', 'disputed', 'unknown'] = 'unknown'
    explanation: str = 'No source-based origin assessment is available.'
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)
    image_match_evidence_ids: list[str] = Field(default_factory=list)
    image_link_explanation: str | None = None


class Assessment(BaseModel):
    summary: str
    findings: list[Finding]
    limitations: list[str]
    context_checks: list[ContextCheck] = Field(default_factory=list)
    interpreted_claim: str | None = None
    media_origin: SourceReportedOrigin = Field(default_factory=SourceReportedOrigin)


class Review(BaseModel):
    accepted: bool
    issues: list[str]
    rejected_findings: list[int] = Field(default_factory=list)
    rejected_context_checks: list[int] = Field(default_factory=list)
    reject_origin: bool = False

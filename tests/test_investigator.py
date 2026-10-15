import json
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

from app.investigator import GeminiInvestigator
from app.models import Submission


def response(text=None, grounded=False):
    grounding = NS(grounding_chunks=[NS(web=NS(uri="https://science.nasa.gov/mars/", title="NASA"))],
                   grounding_supports=[NS(segment=NS(text="Perseverance landed on 18 February 2021."), grounding_chunk_indices=[0])],
                   search_entry_point=None, web_search_queries=["NASA Perseverance landing date"]) if grounded else None
    return NS(text=text, candidates=[NS(grounding_metadata=grounding)],
              usage_metadata=NS(prompt_token_count=100, candidates_token_count=50, thoughts_token_count=10, total_token_count=160))


def configure(monkeypatch):
    monkeypatch.setenv("PROOFMESH_ENABLE_LIVE", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")


def test_live_pipeline_bounds_calls_and_scopes_quota(monkeypatch):
    configure(monkeypatch)
    assessment = {"summary": "Supported by the supplied NASA excerpt.", "findings": [{"claim": "Perseverance landed in 2021", "status": "supported", "explanation": "The cited excerpt gives the date.", "evidence_ids": ["E1"]}], "limitations": []}
    client = MagicMock()
    client.models.generate_content.side_effect = [response(grounded=True), response(json.dumps(assessment)), response('{"accepted":true,"issues":[]}')]
    with patch("google.auth.default", return_value=(object(), "other-default-project")) as auth, patch("google.genai.Client") as constructor:
        constructor.return_value.__enter__.return_value = client
        result = GeminiInvestigator().investigate(Submission(claim="Perseverance landed in 2021"), "2026-10-15")
    auth.assert_called_once_with(quota_project_id="test-project")
    assert constructor.call_args.kwargs["project"] == "test-project"
    assert constructor.call_args.kwargs["http_options"].retry_options.attempts == 1
    assert client.models.generate_content.call_count == 3
    assert [call.kwargs["config"].max_output_tokens for call in client.models.generate_content.call_args_list] == [4096, 3072, 1536]
    assert result["model_calls"] == 3 and len(result["usage"]) == 3
    assert result["usage"][0]["reported_search_queries"] == 1


def test_no_grounding_stops_after_one_call_and_abstains(monkeypatch):
    configure(monkeypatch)
    client = MagicMock()
    client.models.generate_content.return_value = response("An uncited answer")
    with patch("google.auth.default", return_value=(object(), None)), patch("google.genai.Client") as constructor:
        constructor.return_value.__enter__.return_value = client
        result = GeminiInvestigator().investigate(Submission(claim="A claim lacking retrieved evidence"), "2026-10-15")
    assert client.models.generate_content.call_count == 1
    assert result["assessment"]["findings"][0]["status"] == "unresolved"
    assert result["evidence"] == [] and result["model_calls"] == 1


def test_rejected_assessment_is_not_published_as_supported(monkeypatch):
    configure(monkeypatch)
    assessment = {"summary": "Initial conclusion", "findings": [{"claim": "A claim", "status": "supported", "explanation": "Initial reasoning", "evidence_ids": ["E1"]}], "limitations": []}
    client = MagicMock()
    client.models.generate_content.side_effect = [response(grounded=True), response(json.dumps(assessment)), response('{"accepted":false,"issues":["The source does not support the entire claim."]}')]
    with patch("google.auth.default", return_value=(object(), None)), patch("google.genai.Client") as constructor:
        constructor.return_value.__enter__.return_value = client
        result = GeminiInvestigator().investigate(Submission(claim="A disputed claim"), "2026-10-15")
    assert result["assessment"]["findings"][0]["status"] == "unresolved"
    assert result["assessment"]["limitations"] == ["The source does not support the entire claim."]

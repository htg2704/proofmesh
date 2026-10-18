import json
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pytest
from app.citations import passage_catalog, validate_assessment
from app.investigator import GeminiInvestigator, choose_leads
from app.models import Assessment
from app.service import ProofMesh

TEXT='The circulated selfie is AI-generated. It is not a genuine photograph of the summit.'
SOURCE={'id':'E1','kind':'source_page_excerpt','excerpt':TEXT,'url':'https://publisher.example/factcheck','match':'partial'}

def response(value):
    return NS(text=json.dumps(value) if not isinstance(value,str) else value, candidates=[NS(grounding_metadata=None)], usage_metadata=None)

def assessment(quote='The circulated selfie is AI-generated.'):
    return {'summary':'The caption is contradicted by the source.', 'interpreted_claim':'This is an authentic photograph from the summit.',
            'findings':[{'claim':'This is an authentic photograph from the summit.','status':'contradicted','explanation':'The cited coverage says the circulated selfie was AI-generated.','evidence_ids':['E1'],'evidence_quotes':[{'evidence_id':'E1','quote':quote}]}], 'limitations':[],
            'media_origin':{'classification':'reported_ai_generated','explanation':'Published coverage describes the circulated selfie as AI-generated.','evidence_ids':['E1'],'evidence_quotes':[{'evidence_id':'E1','passage_id':'E1.P1'}]}}

def run(monkeypatch, sequence):
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true');monkeypatch.setenv('GOOGLE_CLOUD_PROJECT','test-project');monkeypatch.setenv('GEMINI_MODEL','test-model')
    client=MagicMock();client.models.generate_content.side_effect=[response('Research lead'),*[response(x) if not isinstance(x,Exception) else x for x in sequence]]
    investigator=GeminiInvestigator(fetcher=lambda url,claim:{k:v for k,v in SOURCE.items() if k!='id'},media_retriever=lambda image:{'status':'retrieved','pages':[{'url':SOURCE['url'],'kind':'image_match_lead','match':'partial','title':'Fact check','excerpt':'Image lead'}],'vision_calls':0})
    from app.models import Submission
    with patch('google.auth.default',return_value=(object(),None)),patch('google.genai.Client') as constructor:
        constructor.return_value.__enter__.return_value=client
        result=investigator.investigate(Submission(claim='Summit leaders selfie'),'2026-10-18')
    return result,client

def test_passage_ids_resolve_to_fetched_text_instead_of_model_paraphrase():
    value=assessment();value['findings'][0]['evidence_quotes']=[{'evidence_id':'E1','passage_id':'E1.P1','quote':'An invented paraphrase that must not be displayed'}]
    parsed=validate_assessment(Assessment.model_validate(value),[SOURCE])
    assert parsed.findings[0].evidence_quotes[0].quote=='The circulated selfie is AI-generated.'

def test_quote_normalization_accepts_typography_but_not_changed_negation():
    source={**SOURCE,'excerpt':'The photo wasn’t taken at the summit.'}
    value=assessment("The photo wasn't taken at the summit.");value.pop('media_origin')
    assert validate_assessment(Assessment.model_validate(value),[source])
    value['findings'][0]['evidence_quotes'][0]['quote']='The photo was taken at the summit.'
    with pytest.raises(ValueError,match='quotation'):validate_assessment(Assessment.model_validate(value),[source])

def test_wrong_passage_source_and_generated_summary_cannot_substantiate_verdict():
    value=assessment();value['findings'][0]['evidence_quotes']=[{'evidence_id':'E1','passage_id':'E2.P1'}]
    with pytest.raises(ValueError):validate_assessment(Assessment.model_validate(value),[SOURCE])
    with pytest.raises(ValueError):validate_assessment(Assessment.model_validate(assessment()),[{**SOURCE,'kind':'search_grounded_excerpt'}])

def test_one_bounded_repair_resolves_the_source_reported_ai_case(monkeypatch):
    fixed=assessment();fixed['findings'][0]['evidence_quotes']=[{'evidence_id':'E1','passage_id':'E1.P1'}]
    result,client=run(monkeypatch,[assessment('This invented wording does not occur in the fetched text.'),fixed,{'accepted':True,'issues':[]}])
    assert client.models.generate_content.call_count==4 and result['model_calls']==4
    assert result['validation']['repair_attempted'] and result['validation']['repair_succeeded']
    assert result['assessment']['findings'][0]['status']=='contradicted' and result['source_origin_validated']
    report=ProofMesh.make_report('Caption',{'sha256':'image','dhash':None},'a'*64,'live',result,datetime.now(timezone.utc))
    assert report['origin']['status']=='reported_ai_generated' and report['origin']['image_binding']=='partial'
    assert report['origin']['independent_verification']=='not_performed'

def test_failed_auxiliary_context_does_not_erase_the_valid_main_finding(monkeypatch):
    value=assessment();value['context_checks']=[{'dimension':'date','claimed':'2026','observed':'2025','status':'contradicted','evidence_ids':['E999'],'evidence_quotes':[]}]
    result,_=run(monkeypatch,[value,value,{'accepted':True,'issues':[]}])
    assert result['assessment_status']=='partial'
    assert result['assessment']['findings'][0]['status']=='contradicted'
    assert result['assessment']['context_checks'][0]['assessment_issue']=='citation_validation_failed'
    assert any(d['code']=='unknown_evidence' for d in result['validation']['diagnostics'])

def test_exhausted_repair_is_processing_failure_not_factual_uncertainty(monkeypatch):
    value=assessment('An invented quotation absent from the source.');value.pop('media_origin')
    result,client=run(monkeypatch,[value,value])
    assert client.models.generate_content.call_count==3
    assert result['assessment_status']=='validation_failed'
    assert result['assessment']['findings'][0]['assessment_issue']=='citation_validation_failed'
    assert result['assessment']['findings'][0]['evidence_quotes']==[]
    assert result['validation']['diagnostics'][0]['code']=='quote_not_found'

def test_failed_repair_request_preserves_valid_parts_and_attempt_accounting(monkeypatch):
    value=assessment();value['context_checks']=[{'dimension':'location','claimed':'Delhi','observed':'Other place','status':'contradicted','evidence_ids':['E999']}]
    result,_=run(monkeypatch,[value,RuntimeError('Simulated unavailable repair'),{'accepted':True,'issues':[]}])
    assert result['model_calls']==4 and result['provider_attempts']['citation_repair']==1
    assert result['validation']['repair_error']['type']=='RuntimeError'
    assert result['assessment']['findings'][0]['status']=='contradicted'

def test_targeted_critique_does_not_nuke_other_valid_findings(monkeypatch):
    value=assessment();value['context_checks']=[{'dimension':'location','claimed':'Summit','observed':'Summit','status':'supported','evidence_ids':['E1'],'evidence_quotes':[{'evidence_id':'E1','passage_id':'E1.P1'}]}]
    result,_=run(monkeypatch,[value,{'accepted':False,'issues':['Location is not established.'],'rejected_context_checks':[0]}])
    assert result['model_calls']==3 and result['assessment']['findings'][0]['status']=='contradicted'
    assert result['assessment']['context_checks'][0]['assessment_issue']=='review_rejected'

def test_related_article_does_not_become_verified_origin_for_the_uploaded_image():
    from app.origin import origin_from_result
    result={'source_origin_validated':True,'assessment':{'media_origin':assessment()['media_origin']},'evidence':[{**SOURCE,'match':'related'}]}
    origin=origin_from_result(result)
    assert origin['status']=='unconfirmed_media_match' and origin['source_reporting']['classification']=='reported_ai_generated'

def test_closer_factcheck_lead_is_not_displaced_by_first_two_related_results():
    pages=[{'url':'https://video.example','match':'related'},{'url':'https://social.example','match':'related'},{'url':'https://publisher.example/factcheck','match':'partial'}]
    leads=choose_leads(pages,[{'url':'https://primary.example'}])
    assert leads[0]['url']=='https://publisher.example/factcheck'
    assert leads[1]['url']=='https://primary.example'

def test_image_association_needs_real_matching_metadata_not_an_invented_link():
    value=assessment();value['media_origin']['image_match_evidence_ids']=['E2']
    association={'id':'E2','kind':'image_match_lead','excerpt':'Image association only','match':'partial'}
    parsed=validate_assessment(Assessment.model_validate(value),[SOURCE,association])
    assert parsed.media_origin.image_match_evidence_ids==['E2']
    with pytest.raises(ValueError,match='association'):validate_assessment(Assessment.model_validate(value),[SOURCE,{**association,'match':'related'}])

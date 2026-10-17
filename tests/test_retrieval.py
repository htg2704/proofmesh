import socket
from unittest.mock import patch
import pytest
from app.retrieval import public_addresses, enrich_evidence, PageText
from app.investigator import validate_assessment
from app.models import Assessment


@pytest.mark.parametrize('url',['http://example.org','https://user:pass@example.org','https://example.org:444','https://127.0.0.1','https://169.254.169.254','https://[::1]'])
def test_retrieval_rejects_unsafe_targets(url):
    with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]):
        with pytest.raises(ValueError): public_addresses(url)


def test_mixed_public_private_dns_is_rejected():
    with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('10.1.1.1',443))]):
        with pytest.raises(ValueError): public_addresses('https://example.org')


def test_failed_fetch_remains_lead_and_cannot_prove_claim():
    def fail(url,claim): raise TimeoutError()
    evidence=enrich_evidence([{'url':'https://example.org','title':'Source','excerpt':'Generated claim','kind':'search_grounded_excerpt'}],'A claim',fail)
    assert evidence[0]['fetch_status']=='unavailable'
    assessment=Assessment(summary='Claim',findings=[{'claim':'A claim','status':'supported','explanation':'A summary says so','evidence_ids':['E1']}],limitations=[])
    with pytest.raises(ValueError): validate_assessment(assessment,evidence)


def test_html_scripts_are_data_not_executed_or_cited():
    parser=PageText(); parser.feed('<script>invented proof</script><p>Actual source passage.</p><meta property="article:published_time" content="2020-01-02">')
    assert 'invented proof' not in ''.join(parser.parts)
    assert parser.published=='2020-01-02'


def test_redirected_duplicate_sources_do_not_inflate_evidence():
    leads=[{'url':'https://example.org/'+str(i),'title':'Lead','kind':'search_grounded_excerpt','excerpt':'Summary'} for i in range(2)]
    result=enrich_evidence(leads,'A claim',lambda url,claim:{'url':'https://source.org/article','kind':'source_page_excerpt','excerpt':'Actual passage'})
    assert len(result)==1

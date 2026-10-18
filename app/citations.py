"""Resolve citations to actual fetched text; never guess or repair factual words."""
import re
import unicodedata


def canonical_quote(text):
    # Typography equivalence only: no fuzzy word, number or negation matching.
    punctuation = str.maketrans({'‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-'})
    return ' '.join(unicodedata.normalize('NFKC', text).translate(punctuation).split()).casefold()


def passage_catalog(evidence):
    catalog = {}
    for source in evidence:
        if source.get('kind') != 'source_page_excerpt':
            continue
        text = ' '.join(source['excerpt'].split())
        words = text.split()
        candidates = re.split(r'(?<=[.!?;])\s+', text)
        candidates += [' '.join(words[start:start+24]) for start in range(0, len(words), 12)]
        seen = set()
        for quote in candidates:
            if not 3 <= len(quote.split()) <= 24 or quote in seen:
                continue
            seen.add(quote)
            identifier = f"{source['id']}.P{len(seen)}"
            catalog[identifier] = {'evidence_id': source['id'], 'quote': quote}
    return catalog


def items(assessment):
    yield from (('finding', i, item, item.status != 'unresolved') for i, item in enumerate(assessment.findings))
    yield from (('context', i, item, item.status != 'unresolved') for i, item in enumerate(assessment.context_checks))
    yield 'origin', 0, assessment.media_origin, assessment.media_origin.classification != 'unknown'


def citation_issues(assessment, evidence, catalog=None):
    sources = {e['id']: e for e in evidence}
    catalog = passage_catalog(evidence) if catalog is None else catalog
    problems = []
    if not assessment.findings:
        problems.append({'kind': 'assessment', 'index': 0, 'code': 'missing_findings', 'message': 'An assessment must include at least one finding'})
    for kind, index, item, conclusive in items(assessment):
        def fail(code, message, evidence_id=None):
            problems.append({'kind': kind, 'index': index, 'code': code, 'message': message, **({'evidence_id': evidence_id} if evidence_id else {})})
        if not set(item.evidence_ids) <= sources.keys():
            fail('unknown_evidence', 'Assessment cited an unknown evidence ID')
        if kind == 'origin':
            for identifier in item.image_match_evidence_ids:
                source = sources.get(identifier)
                if not source or source.get('match') not in {'full', 'partial'}:
                    fail('invalid_image_association', 'Image association must cite an actual full or partial image-match lead', identifier)
        for citation in item.evidence_quotes:
            if citation.passage_id:
                passage = catalog.get(citation.passage_id)
                if not passage or passage['evidence_id'] != citation.evidence_id:
                    fail('unknown_passage', 'Cited quotation passage does not belong to this source', citation.evidence_id)
                    continue
                # Source text wins over any model-supplied quote accompanying an ID.
                citation.quote = passage['quote']
            source = sources.get(citation.evidence_id)
            if not source or source.get('kind') != 'source_page_excerpt':
                fail('not_fetched_source', 'A source lead cannot substantiate a quotation', citation.evidence_id)
                continue
            if not 3 <= len(citation.quote.split()) <= 24:
                fail('quote_length', 'Cited quotation must contain 3 to 24 words', citation.evidence_id)
            elif canonical_quote(citation.quote) not in canonical_quote(source['excerpt']):
                fail('quote_not_found', 'Cited quotation was not found in fetched source text', citation.evidence_id)
        if conclusive and (not item.evidence_ids or set(item.evidence_ids) != {q.evidence_id for q in item.evidence_quotes}):
            fail('missing_quotes', 'Conclusive findings need an exact quotation for every cited source')
    return problems


def validate_assessment(assessment, evidence):
    problems = citation_issues(assessment, evidence)
    if problems:
        raise ValueError(problems[0]['message'])
    return assessment


def retain_valid_findings(assessment, problems, claim):
    """A rejected auxiliary context check must not erase a valid main finding."""
    for kind, index, item, _ in items(assessment):
        relevant = [p for p in problems if p['kind'] == kind and p['index'] == index]
        if not relevant:
            continue
        item.evidence_ids = []
        item.evidence_quotes = []
        if kind == 'origin':
            item.classification = 'unknown'
            item.image_match_evidence_ids = []
        else:
            item.status = 'unresolved'
            item.assessment_issue = 'citation_validation_failed'
        if kind == 'context':
            item.observed = 'Not established: ProofMesh could not validate this context check.'
        else:
            item.explanation = 'ProofMesh could not validate the citations for this part of the assessment.'
    if not assessment.findings:
        from app.models import Finding
        assessment.findings = [Finding(claim=claim, status='unresolved', explanation='ProofMesh could not complete the assessment.', evidence_ids=[], assessment_issue='citation_validation_failed')]
    if problems:
        refresh_summary(assessment)
    return assessment


def refresh_summary(assessment):
    valid = [f for f in assessment.findings if f.status != 'unresolved']
    if valid:
        assessment.summary = ' '.join(f.explanation for f in valid)
        if any(f.assessment_issue for f in assessment.findings) or any(c.assessment_issue for c in assessment.context_checks):
            assessment.summary += ' Some parts could not be validated; see assessment notes.'
    elif assessment.media_origin.classification != 'unknown':
        assessment.summary = assessment.media_origin.explanation
    else:
        assessment.summary = 'ProofMesh could not complete a validated conclusion. The source material is still available below.'

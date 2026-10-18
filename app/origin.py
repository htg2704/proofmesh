"""Source attribution and independent forensic verification are separate facts."""


def origin_from_result(result):
    origin = {'status': 'unknown', 'basis': 'not_assessed', 'independent_verification': 'not_performed',
              'explanation': 'No independent provenance or watermark verification has been performed.'}
    reported = result.get('assessment', {}).get('media_origin', {})
    if not result.get('source_origin_validated') or reported.get('classification', 'unknown') == 'unknown':
        return origin
    identifiers = set(reported.get('evidence_ids', [])) | set(reported.get('image_match_evidence_ids', []))
    sources = [e for e in result.get('evidence', []) if e['id'] in identifiers]
    binding = 'full' if any(e.get('match') == 'full' for e in sources) else 'partial' if any(e.get('match') == 'partial' for e in sources) else 'not_established'
    return {**origin, 'status': reported['classification'] if binding != 'not_established' else 'unconfirmed_media_match',
            'basis': 'published_source_reporting', 'image_binding': binding,
            'explanation': reported['explanation'], 'source_reporting': reported}

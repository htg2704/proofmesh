# ProofMesh development evaluation — October 17, 2026

Twelve cases were specified in `evaluation/cases-v04.json` before inference. They test caption context, publication time, a cropped photo, an unrelated image, public facts, abstention and an instruction injection. This is a small development set, not a held-out or representative accuracy benchmark. No independent human rater agreement is claimed.

## Outcomes

The first pass completed 9 of 12 cases; all nine matched the prespecified expectation. Three failed with provider 429 responses. After adding a single bounded retry for a 429-failed stage, those three cases were explicitly rerun. All three completed, without exercising the additional stage retry. The follow-up therefore does not establish that the retry improved availability. Original failed-attempt records are retained locally.

Across completed runs, **11 of 12 outcomes matched expectations**: nine conclusive findings, three abstentions. The known false EU flag assertion remained unresolved because exact source-quotation validation failed. That is counted as a miss, not relabeled as a success. The deliberately unrelated image was not endorsed.

| Case | Expected | Observed | Fresh seconds | Repeat model calls |
|---|---|---|---:|---:|
| earthrise-accurate | supported | supported | 24.750 | 0 |
| earthrise-recycled-today | contradicted | contradicted | 16.039 | 0 |
| earthrise-archival-context | supported | supported | 24.666 | 0 |
| earthrise-cropped | supported | supported | 28.007 | 0 |
| unrelated-image | not_supported | unresolved | 14.640 | 0 |
| india-landing-correct | supported | supported | 13.032 | 0 |
| india-landing-wrong-date | contradicted | contradicted | 8.780 | 0 |
| australia-capital-correct | supported | supported | 22.219 | 0 |
| australia-capital-wrong | contradicted | contradicted | 20.751 | 0 |
| european-flag-count | contradicted | unresolved | 13.821 | 0 |
| private-unsupported | unresolved | unresolved | 3.759 | 0 |
| instruction-injection | contradicted | contradicted | 12.664 | 0 |

All twelve exact repeats made zero model calls. Local SQLite reuse ranged from 0.9 to 21.7 ms; fresh completed pipelines ranged from 3.759 to 28.007 seconds. These are local measurements including remote inference/retrieval, not hosted latency guarantees. `not_supported` accepts contradicted or unresolved, and was prespecified for the unrelated image. The 1968 publication case uses constructed archival context; it does not imply that X existed then.

## Method and validation

Gemini researches with search grounding; the application fetches candidate source pages, then asks for structured findings and a same-model critique. Every conclusive finding and context check must cite supplied source IDs and an exact contiguous quotation of 3–24 words from each fetched passage. Generated search summaries and image-match leads cannot substantiate a verdict. Failed quotation validation downgrades the result to unresolved. This checks source structure, not independent truth or full entailment.

Images are supplied to assessment and critique as well as research. Relative dates use the supplied publication timestamp, with timezone uncertainty stated. A timestamp is context, not verified capture time. Cache identity includes the publication context and evidence-policy version, so old reports cannot silently satisfy the stronger policy.

The working cost estimate for this evaluation, including conservative reserves for the three failed attempts, is **US$0.99396**. It is not a billing receipt and excludes some infrastructure costs. Token and search counts are retained in `evaluation/results-v04.json`.

## Hosted verification and failures

Earlier Cloud Run jobs completed with attached service identities, private image storage, Firestore persistence and Cloud Tasks delivery: text 10.531 s; image 22.892 s. Their exact Firestore reuse was 104.5 ms and 178.7 ms respectively, with zero model calls. These earlier runs used the previous evidence policy.

The October 17 v0.4 reviewer browser test authenticated successfully and enforced collection isolation. Its fresh image investigation failed with Vertex 429 in research on both bounded stage attempts. No report was published. It consumed one admission; the four-attempt UTC daily cap was reached. This is an observed availability limitation, not a successful v0.4 hosted inference test. The provider error is now explicit, and starting a new job clears any previously displayed report. No automatic whole-pipeline retry occurs.

A separate user-supplied “BRICS 2026 selfie” exploratory image test returned contradicted, with a zero-call repeat. A visual comparison matched the uploaded composition in [AFP fact-check coverage](https://factcheck.afp.com/doc.afp.com.C9427KE). That test was proposed after inspecting the source and is excluded from the prespecified set. The image and full private report are not published in this repository. ProofMesh did not run a watermark or provenance detector; its independent origin status remains unknown.

## Sources and media use

Primary anchors: [NASA Earthrise](https://science.nasa.gov/resource/apollo-8s-iconic-earthrise/), [ISRO Chandrayaan-3](https://www.isro.gov.in/ISRO_EN/Chandrayaan3.html), [National Capital Authority](https://www.nca.gov.au/), and [European Union flag](https://european-union.europa.eu/principles-countries-history/symbols/european-flag_en). Earthrise image credit: NASA/Bill Anders. Educational use implies no endorsement. Public examples are frozen recorded outputs; viewing them invokes no model.

The earlier four-case demonstration remains in `docs/evaluation-results.json`. It had provider failures and a post hoc correction of one unsuitable expected label. A misleading-caption explanation also included an incidental mission-schedule error missed by critique; that historical limitation is retained here. Current public samples were replaced with v0.4 runs, not silently edited to correct the old output.

## Deterministic checks and limits

47 Python and 27 JavaScript tests cover publication anchoring, quotation validation, reviewer scope and cookie expiry/tampering, quota reservation, job completion without polling recursion, cleared stale results after failure, exact reuse, changed captions, prompt injection boundaries, private-route exclusion, recycled DOM nodes, SSRF defenses and bounded retries. Mocks and DOM fixtures do not replace live evaluation.

No precision/recall estimate, universal AI-origin detector, C2PA validation, semantic claim reuse, video or multi-image analysis is claimed. Same-model critique can miss errors. No new Instagram adapter or broader logged-in X/accessibility validation is included.

## Subsequent v0.5 hosted integration check

The ordinary visitor flow later completed a fresh Canberra claim with three model calls and one provider attempt per stage, persisted it in a private client namespace, and reused it with zero model calls. This verifies the new access/queue/storage path and is not added to the prespecified accuracy outcomes. The earlier v0.4 reviewer capacity failure remains part of the record.

## v0.6 validation-failure regression

A user report contained fetched coverage describing the circulated BRICS selfie as AI-generated, but the entire result was replaced by an unresolved finding after exact-quotation validation failed. The rejected candidate and specific failure code were not saved in that older report, so its exact bad citation cannot be reconstructed. The source set also showed a partial fact-check image match in third position; the earlier retrieval code fetched only the first two Vision leads.

The fix prioritizes full/partial image matches, provides server-resolved passage IDs, attempts one bounded citation repair, preserves unaffected findings, records diagnostic codes and distinguishes an incomplete assessment from genuinely inconclusive evidence. Source-reported AI generation is separate from independent forensic verification, with image association stated explicitly. Tests cover the source-reported AI case, changed negation, wrong-source IDs, generated-summary rejection, exhausted repair, repair request failure, targeted critique and unrelated-article origin attribution. This does not turn quotation presence into a guarantee of factual entailment or establish general detection accuracy.

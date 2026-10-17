# ProofMesh demo transcript — v0.4

Duration: 3 minutes 20 seconds. Synthetic narration uses the built-in macOS Samantha voice; no team-member voice is represented. The edited walkthrough combines actual UI actions sampled at approximately two frames per second, adjusted pauses, recorded model results and architecture/evaluation slides. The portal footage uses the local v0.4 interface; the extension footage uses the hosted synthetic feed. No new successful inference is simulated.

## 0:00 — intro

ProofMesh is a shared evidence rail built by Hounds of Singularity. The web workspace and X extension are its first applications.

## 0:10 — lookup

Checking shared evidence searches for an existing investigation about this exact claim, image and publication context. It makes no model calls. The information icon explains the difference.

## 0:22 — new

Starting a new investigation asks Google Cloud AI to research the claim, inspect source passages, and review its conclusion. It requires access and consumes a bounded allowance. Model capacity failures remain possible.

## 0:36 — reuse

Here we load a clearly labeled fictional bridge example. Checking the registry retrieves the stored report with zero model calls. This demonstrates the reuse workflow; the bridge and event are synthetic, and no real-world verification is implied.

## 0:54 — alternate

Now we change only the caption. The image is familiar but the earlier verdict does not transfer. ProofMesh returns related investigations as leads and keeps the new claim unverified. This separation is the core contract every future client must preserve.

## 1:12 — history

The next case is a saved live investigation, not new inference. It links the Earthrise photograph to fetched historical sources, with exact quotations and separate context checks. The application validates quotations against passages before displaying a conclusive finding. This is a structural check, not independent verification.

## 1:34 — misleading

The same photograph now appears with a caption saying it was taken today. The supplied publication timestamp anchors that word to October seventeenth, twenty twenty-six. The sources place the photograph in nineteen sixty-eight. The report contradicts this caption while keeping independent media-origin status unknown.

## 1:54 — unresolved

When no usable source can substantiate a private assertion, ProofMesh stays unresolved. Missing evidence does not make the claim false, and no source is invented.

## 2:06 — feed

The extension is another client of the same API. In the hosted synthetic feed, one caption can retrieve evidence while another remains unverified. Registry lookups do not launch paid investigations automatically.

## 2:22 — architecture

Cloud Run serves the API. Firestore preserves reports and job state. Cloud Tasks delivers durable work, and temporary images stay in private storage. Vision finds image-matching leads; Gemini researches and reviews fetched sources. Reviewer access uses a separate collection and reserved allowance.

## 2:42 — evaluation

The twelve-case development set produced eleven expected outcomes. One known false assertion stayed unresolved. Three first attempts failed with provider rate limits and required explicit reruns. All twelve exact repeats made zero model calls. The latest hosted reviewer test also hit capacity errors. These results are not representative accuracy.

## 3:02 — future

Social apps, Android or Gemini experiences, and AI agents could consume this rail through future integrations. An MCP adapter and SDK are not implemented yet. This release demonstrates reusable evidence infrastructure, with the web workspace as its first reference application.

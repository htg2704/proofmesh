import base64
import io
from PIL import Image, ImageDraw
from app.fingerprints import image_identity, context_key
from app.service import now

DEMO_CLAIM = "This bridge image shows a collapse today in Riverton."
ALTERNATE_CLAIM = "An illustration of a bridge used in an archive example."


def demo_image() -> bytes:
    image = Image.new("RGB", (960, 540), "#d6ddd3")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 310, 960, 540), fill="#47796f")
    draw.polygon([(0, 305), (150, 190), (300, 310)], fill="#9da891")
    draw.polygon([(620, 310), (830, 140), (960, 310)], fill="#aab09b")
    draw.rectangle((60, 275, 900, 303), fill="#343e3b")
    for x in [180, 410, 650, 820]:
        draw.rectangle((x, 290, x + 22, 430), fill="#343e3b")
    draw.rectangle((0, 0, 960, 52), fill="#1a2725")
    draw.text((25, 18), "PROOFMESH / SYNTHETIC DEMO ILLUSTRATION / NOT A NEWS PHOTOGRAPH", fill="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def seed(service):
    encoded = base64.b64encode(demo_image()).decode()
    identity = image_identity(encoded)
    stamp = now()
    key = context_key(DEMO_CLAIM, identity, "demo", stamp.date().isoformat())
    report = service.make_report(DEMO_CLAIM, identity, key, "demo", {
        "assessment": {
            "summary": "In this fictional scenario, the caption presents an older illustration as a current photograph.",
            "findings": [{"claim": DEMO_CLAIM, "status": "contradicted", "explanation": "The supplied demo archive explicitly describes an illustration assigned a 2021 archive date. This is a synthetic fixture, not a verified real-world event.", "evidence_ids": ["D1"]}],
            "limitations": ["Synthetic scenario for testing product behavior. No external research or AI detection was performed."]},
        "evidence": [{"id": "D1", "title": "Fictional bridge archive — demo fixture", "url": "/fixtures/bridge-archive", "excerpt": "Illustration: Riverton bridge. Fictional archive date: 2021-06-18. This is not a photograph of a real event.", "kind": "demo_fixture"}],
        "events": [{"stage": "fixture", "detail": "Loaded a clearly labeled synthetic investigation."}, {"stage": "registry", "detail": "Stored evidence with a media-and-caption context key."}],
        "model_calls": 0, "search_attribution_html": None}, stamp)
    service.store.put(report)
    return {"claim": DEMO_CLAIM, "alternate_claim": ALTERNATE_CLAIM, "image_base64": encoded, "report": report}

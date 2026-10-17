import base64
import hashlib
import io
import unicodedata
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 5_000_000
MAX_PIXELS = 16_000_000


def normalize_claim(claim: str) -> str:
    # Preserve capitalization, numbers, punctuation and negation.
    return " ".join(unicodedata.normalize("NFC", claim).split())


def image_identity(encoded: str | None) -> dict:
    if not encoded:
        return {"sha256": None, "dhash": None}
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_BYTES:
            raise ValueError("Image exceeds 5 MB")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("Use a PNG, JPEG or WebP image")
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError("Image exceeds 16 megapixels")
                im = ImageOps.exif_transpose(source).convert("RGB")
                im.load()
        digest = hashlib.sha256(f"{im.width}x{im.height}:".encode() + im.tobytes()).hexdigest()
        small = im.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        tiny = [small.getpixel((x, y)) for y in range(8) for x in range(9)]
        bits = sum((tiny[y * 9 + x] > tiny[y * 9 + x + 1]) << (y * 8 + x)
                   for y in range(8) for x in range(8))
        return {"sha256": digest, "dhash": f"{bits:016x}"}
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning, base64.binascii.Error) as exc:
        raise ValueError("Invalid or oversized image") from exc


def context_key(claim: str, identity: dict, corpus: str, date: str, published_at: str | None = None) -> str:
    # The reference date prevents a cached 'today' verdict being reused tomorrow.
    import json
    content = [normalize_claim(claim), identity["sha256"], corpus, date]
    if corpus != "demo":
        content.append("evidence-policy-0.4")
    if published_at:
        content.append(published_at)
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode()).hexdigest()


def similar(left: dict, right: dict) -> bool:
    if not left.get("dhash") or not right.get("dhash"):
        return False
    return (int(left["dhash"], 16) ^ int(right["dhash"], 16)).bit_count() <= 6

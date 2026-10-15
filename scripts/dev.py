"""Load repository-local settings without shell evaluation, then launch the app."""
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_settings():
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError("Invalid setting in repository .env")
        os.environ.setdefault(key, value)


if __name__ == "__main__":
    load_settings()
    os.chdir(ROOT)
    import uvicorn
    uvicorn.run("app.main:create_app", factory=True, host="127.0.0.1", port=8000)


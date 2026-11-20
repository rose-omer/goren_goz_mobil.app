"""Modelleri Hugging Face Hub'dan sabit commit ile indirir ve SHA-256 denetler (plan 4.9).

Kullanım:
    python scripts/download_models.py               # backend + mobil
    python scripts/download_models.py --target backend

Önce `scripts/models.json` içindeki `revision` ve `sha256` alanlarını doldur.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("models.json")
TARGET_DIRS = {
    "backend": ROOT / "backend" / "model_files",
    "mobile": ROOT / "mobile_app" / "assets" / "models",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("backend", "mobile", "all"), default="all")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    revision = manifest["revision"]
    if not COMMIT_RE.match(revision):
        print("models.json: 'revision' 40 karakterlik bir commit olmalı.", file=sys.stderr)
        return 2

    from huggingface_hub import hf_hub_download

    failed = False
    for item in manifest["files"]:
        if args.target != "all" and item["target"] != args.target:
            continue
        cached = Path(hf_hub_download(manifest["repo_id"], item["name"], revision=revision))
        expected = item.get("sha256")
        actual = sha256_of(cached)
        if expected and actual != expected:
            print(f"SHA-256 uyuşmuyor: {item['name']}", file=sys.stderr)
            failed = True
            continue
        dest = TARGET_DIRS[item["target"]] / item["name"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached, dest)
        note = "" if expected else " (sha256 manifestte yok; doldur)"
        print(f"{item['name']} -> {dest.relative_to(ROOT)}  {actual[:12]}{note}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

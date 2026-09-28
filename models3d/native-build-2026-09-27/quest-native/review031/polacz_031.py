"""Place this script, wydanie.json and all 20 .part files in one directory."""
from pathlib import Path
import hashlib
import json
import os

root = Path(__file__).resolve().parent
manifest = json.loads((root / "wydanie.json").read_text(encoding="utf-8"))
target = root / manifest["file"]
temporary = target.with_suffix(".apk.tmp")
if target.exists():
    with target.open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() == manifest["sha256"]:
            print("APK już jest kompletne:", target.name)
            raise SystemExit(0)
    raise SystemExit("Istniejący plik APK ma inny SHA-256. Zmień jego nazwę; nie został nadpisany.")
complete = hashlib.sha256()
try:
    with temporary.open("wb") as out:
        for part in manifest["parts"]:
            source = root / part["file"]
            data = source.read_bytes()
            if len(data) != part["size"] or hashlib.sha256(data).hexdigest() != part["sha256"]:
                raise ValueError("Uszkodzona część: " + source.name)
            complete.update(data)
            out.write(data)
            print(source.name, "OK")
        out.flush()
        os.fsync(out.fileno())
    if complete.hexdigest() != manifest["sha256"]:
        raise ValueError("Niezgodny SHA-256 złożonego APK")
    temporary.replace(target)
    print("Gotowe:", target.name)
except Exception:
    temporary.unlink(missing_ok=True)
    raise

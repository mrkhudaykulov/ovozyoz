"""Yangi reliz uchun imzolangan version.json yaratadi.
Ishlatish:  python tools\\make_release.py "Nimalar yangi" [eng_past_versiya]
"""
import base64, hashlib, json, sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ovozyoz import VERSION, UPDATE_REPO  # noqa: E402

KEY = Path.home() / ".ovozyoz" / "update_private.pem"
if not UPDATE_REPO:
    raise SystemExit("ovozyoz/__init__.py da UPDATE_REPO toʻldirilmagan")
setup = ROOT / "Output" / f"OvozYoz-Setup-{VERSION}.exe"
if not setup.exists():
    raise SystemExit(f"Topilmadi: {setup}\nAvval build.bat ni ishga tushiring")

notes = sys.argv[1] if len(sys.argv) > 1 else ""
data = json.dumps({
    "version": VERSION,
    "url": f"https://github.com/{UPDATE_REPO}/releases/download/v{VERSION}/{setup.name}",
    "sha256": hashlib.sha256(setup.read_bytes()).hexdigest(),
    "notes": notes,
    "min_version": sys.argv[2] if len(sys.argv) > 2 else "0",
}, ensure_ascii=False)
priv = serialization.load_pem_private_key(KEY.read_bytes(), password=None)
doc = {"data": data, "sig": base64.b64encode(priv.sign(data.encode("utf-8"))).decode()}
out = ROOT / "Output" / "version.json"
out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print("Tayyor:", out)
print(f"GitHub → {UPDATE_REPO} → Releases → Draft a new release")
print(f"  Tag: v{VERSION}   Fayllar: {setup.name} va version.json   → Publish release")

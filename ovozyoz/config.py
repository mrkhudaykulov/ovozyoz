"""Sozlamalar: foydalanuvchi profilida saqlanadi (%APPDATA%\\OvozYoz)."""
import json, os, shutil, sys
from pathlib import Path
from . import APP

BASE = (Path(sys.executable).parent if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent.parent)
DATA = Path(os.environ.get("APPDATA", str(Path.home()))) / APP
CFG_PATH = DATA / "config.json"

DEFAULTS = {
    "engine": "vosk",          # vosk | auto | realtime | rest
    "api_key": "",             # faqat Aisha uchun
    "vosk_model": "",          # boʻsh = avtomatik qidirish
    "hotkey": "F9",
    "mic_device": None,        # None = standart mikrofon
    "noise_gate": 500,         # shundan past ovoz jimlik hisoblanadi
    "auto_stop_sec": 90,       # jimlikdan keyin avtomatik toʻxtash
    "pause_sec": 0.7,          # Aisha oddiy rejimi: gap chegarasi
    "hover_toggle": True,
    "hover_ms": 900,
    "apostrophe": "unicode",   # unicode (oʻ) | oddiy (o')
    "typing_pause_ms": 700,    # klaviaturada yozilganda kutish
    "update_check": True,      # kuniga bir marta yangilanishni tekshirish
    "window_pos": None,
}


class Config(dict):
    def __init__(self):
        super().__init__(DEFAULTS)
        self.load()

    def load(self):
        DATA.mkdir(parents=True, exist_ok=True)
        self.first_run = not CFG_PATH.exists() and not (BASE / "config.json").exists()
        old = BASE / "config.json"
        if not CFG_PATH.exists() and old.exists():
            shutil.copy(old, CFG_PATH)  # eski versiyadan koʻchirish
        if CFG_PATH.exists():
            try:
                self.update(json.loads(CFG_PATH.read_text(encoding="utf-8")))
            except ValueError:
                pass

    def save(self):
        DATA.mkdir(parents=True, exist_ok=True)
        CFG_PATH.write_text(json.dumps(self, ensure_ascii=False, indent=2), encoding="utf-8")

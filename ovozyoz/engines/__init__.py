"""Dvigatellar roʻyxati — yangisini qoʻshish uchun shu yerga yoziladi."""
from .vosk_engine import VoskEngine
from .aisha import AishaRealtime, AishaRest

ENGINES = {"vosk": VoskEngine, "auto": AishaRealtime, "realtime": AishaRealtime, "rest": AishaRest}
LABELS = {
    "vosk": "Vosk — tekin, offline",
    "auto": "Aisha — avtomatik (pullik)",
    "realtime": "Aisha — realtime (pullik)",
    "rest": "Aisha — oddiy (pullik)",
}


def create(app):
    return ENGINES.get(app.cfg["engine"], VoskEngine)(app)

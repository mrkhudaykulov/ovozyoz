"""Vosk: tekin, offline, sinxron."""
import json, os, queue, threading
from pathlib import Path
from .base import MicEngine, RATE
from ..config import BASE

MODEL_NAME = "vosk-model-small-uz-0.22"


def _is_model(p):
    return (p / "am").is_dir() and (p / "conf").is_dir()


def _scan(p):
    """Papkaning oʻzi yoki ichidagi (2 darajagacha) model papkasi."""
    if not p or not p.is_dir():
        return None
    if _is_model(p):
        return p
    for sub in sorted(p.iterdir()):
        if sub.is_dir():
            if _is_model(sub):
                return sub
            for sub2 in sorted(sub.iterdir()) if sub.name.startswith("vosk") else []:
                if sub2.is_dir() and _is_model(sub2):
                    return sub2  # "Extract All" ichma-ich papka yaratgan holat
    return None


def find_model(cfg):
    user = cfg.get("vosk_model") or ""
    cands = []
    if user:
        cands.append(Path(user) if Path(user).is_absolute() else BASE / user)
    cands += sorted(BASE.glob("vosk-model*"))  # exe yonidagi istalgan nom
    cands.append(Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "OvozYoz" / "model")
    for c in cands:
        m = _scan(c)
        if m:
            return m
    return None


class VoskEngine(MicEngine):
    model = None  # bir marta yuklanadi

    def start(self):
        self.stopped = False
        threading.Thread(target=self.run, daemon=True).start()

    def load(self):
        if VoskEngine.model is None:
            import vosk
            vosk.SetLogLevel(-1)
            path = find_model(self.app.cfg)
            if not path:
                raise RuntimeError(f"Oʻzbekcha model topilmadi. Uni shu papkaga qoʻying: {BASE}")
            self.report("Model yuklanmoqda…")
            prev = os.getcwd()
            os.chdir(path)  # kirillcha yoʻllar muammosini chetlab oʻtish
            try:
                VoskEngine.model = vosk.Model(".")
            finally:
                os.chdir(prev)
        import vosk
        return vosk.KaldiRecognizer(VoskEngine.model, RATE)

    def run(self):
        try:
            rec = self.load()
            if self.stopped:
                return
            self.open_mic()
        except Exception as e:
            self.report(f"Vosk xatosi: {e}")
            return self.request_stop()
        self.listening()
        last = ""
        while not self.stopped or not self.q.empty():
            try:
                data = self.q.get(timeout=0.3)
            except queue.Empty:
                continue
            if rec.AcceptWaveform(data):  # gap boʻlagi tugadi
                self.final(json.loads(rec.Result()).get("text", ""))
            else:
                p = json.loads(rec.PartialResult()).get("partial", "")
                if p and p != last:
                    last = p
                    self.partial(p)
        self.final(json.loads(rec.FinalResult()).get("text", ""))

    def stop(self):
        self.stopped = True
        self.close_mic()

"""Barcha dvigatellar uchun umumiy asos: mikrofon, shovqin filtri, ilovaga xabarlar."""
import queue
import numpy as np
import sounddevice as sd

RATE, BLOCK = 16000, 1600  # 16 kHz, 100 ms bloklar


def input_devices():
    """Standart audio tizimidagi kirish qurilmalari nomlari."""
    try:
        api = sd.query_devices(kind="input")["hostapi"]
        return [d["name"] for d in sd.query_devices()
                if d["max_input_channels"] > 0 and d["hostapi"] == api]
    except Exception:
        return []


def resolve_device(name):
    """Nom boʻyicha qurilma indeksi (bir xil nomlar boshqa tizimlarda takrorlanmasligi uchun)."""
    if not name:
        return None
    try:
        api = sd.query_devices(kind="input")["hostapi"]
        for i, d in enumerate(sd.query_devices()):
            if d["name"] == name and d["hostapi"] == api and d["max_input_channels"] > 0:
                return i
    except Exception:
        pass
    return None


class MicEngine:
    needs_key = False

    def __init__(self, app):
        self.app, self.q = app, queue.Queue()
        self.stream, self.silent, self.hang, self.prev = None, 0, 0, None

    # --- ilovaga xabarlar (thread-safe) ---
    def partial(self, t):
        self.app.ui(lambda: self.app.show_text(t))

    def final(self, t):
        if t and t.strip():
            self.app.writer.q.put(t)
            self.app.ui(lambda: self.app.show_text("✓ " + t))

    def report(self, msg):
        self.app.ui(lambda: self.app.status(msg))

    def listening(self):
        self.app.ui(lambda: self.app.set_state("listening"))

    def request_stop(self):
        self.app.ui(self.app.stop)

    # --- mikrofon ---
    def open_mic(self):
        self.stream = sd.InputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=BLOCK,
                                     device=resolve_device(self.app.cfg["mic_device"]),
                                     callback=self._cb)
        self.stream.start()

    def close_mic(self):
        if self.stream:
            try:
                self.stream.stop(); self.stream.close()
            except Exception:
                pass
            self.stream = None

    def _cb(self, indata, frames, t, status):
        raw = indata[:, 0].copy()
        rms = float(np.sqrt(np.mean(raw.astype(np.float32) ** 2)))
        self.app.level = rms
        loud = rms >= self.app.cfg["noise_gate"]
        x = raw.copy()
        if loud:
            self.hang, self.silent = 5, 0  # 500 ms soʻz oxirini kesmaslik uchun
        elif self.hang > 0:
            self.hang -= 1
        else:
            x[:] = 0  # uzoq/past ovozlar jimlikka aylanadi
            self.silent += 1
            if self.silent * BLOCK / RATE > self.app.cfg["auto_stop_sec"]:
                self.silent = -10 ** 9
                self.request_stop()
        prev, self.prev = self.prev, (x, raw, loud)  # 100 ms kechiktirib yuboriladi
        if prev:
            px, praw, ploud = prev
            if loud and not ploud:
                px = praw  # soʻz boshini kesmaslik: oldingi blok toʻliq ketadi
            self.on_block(px, praw, ploud)

    def on_block(self, x, raw, loud):
        self.q.put(x.tobytes())

    # --- dvigatel interfeysi ---
    def start(self):
        raise NotImplementedError

    def stop(self):
        self.close_mic()

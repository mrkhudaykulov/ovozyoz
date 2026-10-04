"""Aisha (pullik bulut): realtime WebSocket va oddiy REST rejimlari."""
import io, json, queue, threading, time, wave
from urllib.parse import quote
import numpy as np
from .base import MicEngine, RATE, BLOCK

WS_URL = "wss://back.aisha.group/api/v1/stt/realtime?format=pcm&token={token}"
REST_URL = "https://back.aisha.group/api/v1/stt/post/"


class AishaRealtime(MicEngine):
    needs_key = True

    def start(self):
        import websocket
        self.running = self.opened = False
        url = WS_URL.format(token=quote(self.app.cfg["api_key"].strip()))
        self.ws = websocket.WebSocketApp(url, on_open=self.on_open, on_message=self.on_msg,
                                         on_error=self.on_err, on_close=self.on_close)
        threading.Thread(target=self.ws.run_forever, kwargs={"ping_interval": 20},
                         daemon=True).start()

    def on_open(self, ws):
        self.running = self.opened = True
        self.sender = threading.Thread(target=self.send_loop, daemon=True)
        self.sender.start()
        try:
            self.open_mic()
            self.listening()
        except Exception as e:
            self.report(f"Mikrofon xatosi: {e}")
            self.request_stop()

    def send_loop(self):
        import websocket
        while self.running or not self.q.empty():
            try:
                self.ws.send(self.q.get(timeout=0.3), opcode=websocket.ABNF.OPCODE_BINARY)
            except queue.Empty:
                pass
            except Exception:
                break

    def on_msg(self, ws, message):
        try:
            m = json.loads(message)
        except ValueError:
            return
        if m.get("type") == "transcription" and m.get("text"):
            (self.partial if m.get("partial") else self.final)(m["text"])
        elif m.get("type") == "error":
            self.report("Xato: " + str(m.get("message", m.get("code", ""))))

    def on_err(self, ws, err):
        if not self.opened and self.app.cfg["engine"] == "auto":
            return self.app.ui(lambda: self.app.fallback(self))  # realtime ishlamadi
        self.report(f"Tarmoq xatosi: {err}")

    def on_close(self, ws, code, msg):
        self.running = False
        self.close_mic()
        if code not in (None, 1000):
            self.report(f"Ulanish uzildi ({code}) {msg or ''}")
        self.app.ui(lambda: self.app.session_closed(self))

    def stop(self):
        was, self.running = self.running, False
        self.close_mic()

        def finish():
            if was:
                self.sender.join(timeout=2)
                try:
                    self.ws.send('{"event":"end"}')
                except Exception:
                    pass
                time.sleep(2.5)  # oxirgi natijani kutish
            try:
                self.ws.close()
            except Exception:
                pass
        threading.Thread(target=finish, daemon=True).start()


def to_wav(x):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(x.tobytes())
    return b.getvalue()


class AishaRest(MicEngine):
    """Pauzada gap boʻlagini REST orqali yuboradi."""
    needs_key = True

    def start(self):
        self.buf, self.pre, self.speech, self.quiet = [], [], False, 0
        try:
            self.open_mic()
        except Exception as e:
            self.report(f"Mikrofon xatosi: {e}")
            return self.request_stop()
        self.running = True
        threading.Thread(target=self.upload_loop, daemon=True).start()
        self.listening()

    def on_block(self, x, raw, loud):
        if loud and not self.speech:
            self.speech, self.buf = True, self.pre[:]  # soʻz boshini kesmaslik uchun
        if self.speech:
            self.buf.append(raw)
            self.quiet = 0 if loud else self.quiet + 1
            if self.quiet * BLOCK / RATE >= self.app.cfg["pause_sec"] or len(self.buf) >= 250:
                self.flush()  # pauza yoki 25 s chegara
        else:
            self.pre = (self.pre + [raw])[-3:]

    def flush(self):
        seg, self.buf, self.speech, self.quiet = self.buf, [], False, 0
        if len(seg) >= 4:  # 0.4 s dan qisqasi — shovqin
            self.q.put(np.concatenate(seg))

    def upload_loop(self):
        import requests
        key = self.app.cfg["api_key"].strip()
        while self.running or not self.q.empty():
            try:
                seg = self.q.get(timeout=0.3)
            except queue.Empty:
                continue
            self.partial("⏳ aniqlanmoqda…")
            try:
                r = requests.post(REST_URL, headers={"X-Api-Key": key}, timeout=30,
                                  files={"audio": ("gap.wav", to_wav(seg), "audio/wav")},
                                  data={"language": "uz", "has_diarization": "false"})
                if r.status_code != 200:
                    self.report(f"Server xatosi {r.status_code}: {r.text[:120]}")
                    continue
                self.final((r.json().get("transcript") or "").strip())
            except Exception as e:
                self.report(f"Tarmoq xatosi: {e}")

    def stop(self):
        self.close_mic()
        if self.speech:
            self.flush()  # oxirgi gapni ham yuboradi
        self.running = False

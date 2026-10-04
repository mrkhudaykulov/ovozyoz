"""Yangilanishlar: GitHub Releases'dagi imzolangan version.json orqali."""
import base64, hashlib, json, os, tempfile, threading, time
from . import VERSION, UPDATE_URLS, PUBKEY

UA = {"User-Agent": f"OvozYoz/{VERSION}"}  # faqat versiya, shaxsiy maʼlumot yuborilmaydi


def vtuple(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


def verify(doc):
    """Imzoni tekshiradi; soxta fayl boʻlsa xato beradi."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    key = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBKEY))
    key.verify(base64.b64decode(doc["sig"]), doc["data"].encode("utf-8"))
    return json.loads(doc["data"])


class Updater:
    def __init__(self, app):
        self.app, self.info, self.busy = app, None, False

    def enabled(self):
        return bool(PUBKEY and UPDATE_URLS)

    def start(self):
        if self.enabled():
            threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        time.sleep(15)  # ishga tushishni sekinlashtirmaslik uchun
        while True:
            if self.app.cfg["update_check"]:
                self.check(quiet=True)
            time.sleep(24 * 3600)

    def fetch(self):
        import requests
        err = None
        for url in UPDATE_URLS:
            try:
                r = requests.get(url, timeout=15, headers=UA)
                r.raise_for_status()
                return verify(r.json())
            except Exception as e:
                err = e
        raise RuntimeError(err)

    def check(self, quiet=False):
        say = (lambda m: None) if quiet else (lambda m: self.app.ui(lambda: self.app.status(m)))
        if not self.enabled():
            return say("Yangilanish manzili sozlanmagan")
        try:
            info = self.fetch()
        except Exception as e:
            return say(f"Tekshirib boʻlmadi: {e}")
        if vtuple(info.get("version")) > vtuple(VERSION):
            self.info = info
            urgent = vtuple(VERSION) < vtuple(info.get("min_version", "0"))
            self.app.ui(lambda: self.app.update_available(info, urgent))
        else:
            say(f"Sizda eng soʻnggi versiya: {VERSION}")

    def check_async(self):
        threading.Thread(target=self.check, daemon=True).start()

    def install(self):
        if self.info and not self.busy:
            self.busy = True
            threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        import requests
        info = self.info
        try:
            if not info["url"].startswith("https://"):
                raise RuntimeError("xavfsiz boʻlmagan manzil")
            path = os.path.join(tempfile.gettempdir(), f"OvozYoz-Setup-{info['version']}.exe")
            h, done, last = hashlib.sha256(), 0, -1
            with requests.get(info["url"], stream=True, timeout=30, headers=UA) as r, open(path, "wb") as f:
                r.raise_for_status()
                total = int(r.headers.get("content-length") or 0)
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk); h.update(chunk); done += len(chunk)
                    pct = done * 100 // total if total else -1
                    if pct != last:
                        last = pct
                        self.app.ui(lambda p=pct: self.app.status(f"Yangilanish yuklanmoqda… {p}%"))
            if h.hexdigest() != info["sha256"].lower():
                os.remove(path)
                raise RuntimeError("fayl buzilgan (nazorat summasi mos emas)")
        except Exception as e:
            self.busy = False
            return self.app.ui(lambda e=e: self.app.status(f"Yangilashda xato: {e}"))
        self.app.ui(lambda: self.app.run_installer(path))

"""Tanilgan matnni kursor joyiga yozadi va ovozli buyruqlarni bajaradi."""
import queue, threading, time
from . import textproc as tp
from .winapi import user32, type_text, press, VK_BACK, VK_CONTROL

UNKNOWN = "\x00"  # kursordan oldingi belgi nomaʼlum


class Writer(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app, self.q = app, queue.Queue()
        self.hwnd, self.tail, self.chunks, self.last_insert = None, "", [], 0.0

    def run(self):
        while True:
            raw = self.q.get()
            try:
                self.handle(raw)
            except Exception as e:
                self.app.ui(lambda e=e: self.app.status(f"Yozishda xato: {e}"))

    def wait_idle(self):
        w, pause = self.app.watch, self.app.cfg["typing_pause_ms"] / 1000
        while time.monotonic() - w.last_key < pause or w.down(range(8, 255)):
            time.sleep(0.05)

    def sync(self):
        w, h = self.app.watch, user32.GetForegroundWindow()
        if h != self.hwnd:
            self.hwnd, self.tail, self.chunks = h, "", []  # yangi oyna — matn boshi
        elif max(w.last_key, w.last_click) > self.last_insert:
            self.chunks = []  # foydalanuvchi aralashdi — davom etayotgan matn deb olinadi
            if w.last_key > w.last_click and w.last_vk == 0x0D:
                self.tail = "\n"
            elif w.last_key > w.last_click and w.last_vk == 0x20:
                self.tail = UNKNOWN + " "
            else:
                self.tail = UNKNOWN

    def inject(self, fn, added=""):
        w = self.app.watch
        w.paused = True
        fn()
        time.sleep(0.06)
        w.paused = False
        self.last_insert = time.monotonic()
        if added:
            self.tail = (self.tail + added)[-200:]
            self.chunks.append(added)

    def handle(self, raw):
        raw = self.app.lexicon.apply(raw)  # foydalanuvchi tuzatishlari
        k = tp.key_of(raw)
        if not k:
            return
        if k in tp.STOP:
            return self.app.ui(self.app.stop)
        self.wait_idle()
        self.sync()
        if k in tp.UNDO:
            if self.chunks:
                n = len(self.chunks.pop())
                self.inject(lambda: press(VK_BACK, times=n))
                self.tail = self.tail[:-n]
            return
        if k in tp.DEL_WORD:
            return self.inject(lambda: press(VK_CONTROL, VK_BACK))
        if k in tp.NEWLINE:
            return self.inject(lambda: type_text("\n"), "\n")
        if k in tp.PUNCT:
            p = tp.PUNCT[k]
            if self.tail[-1:] in tuple(".,!?;:"):  # avvalgi belgini almashtiradi
                self.tail = self.tail[:-1]
                return self.inject(lambda: (press(VK_BACK), type_text(p)), p)
            return self.inject(lambda: type_text(p), p)

        text = tp.trailing_punct(tp.fix_apostrophes(raw.strip(), self.app.cfg["apostrophe"]), k)
        end = self.tail.rstrip(" ")[-1:]
        if end in ("", "\n", ".", "!", "?"):
            text = text[:1].upper() + text[1:]
        if self.tail and self.tail[-1] not in " \n":
            text = " " + text
        self.inject(lambda: type_text(text), text)

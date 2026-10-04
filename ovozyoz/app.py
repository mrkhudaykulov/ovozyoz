"""Ilova markazi: holat, dvigatelni ishga tushirish, oynalar."""
import queue
import tkinter as tk
from . import APP, VERSION, AUTHOR
from .config import Config, DATA
from .textproc import Lexicon
from .winapi import Watch, Hotkey
from .writer import Writer
from . import engines
from .ui.overlay import Overlay
from .updater import Updater


class App:
    name = APP

    def __init__(self):
        self.cfg = Config()
        self.lexicon = Lexicon(DATA / "lugat.txt")
        self.level, self.state, self.session, self.settings_win = 0.0, "off", None, None
        self.uiq = queue.Queue()
        self.watch = Watch(); self.watch.start()
        self.writer = Writer(self); self.writer.start()
        self.root = tk.Tk()
        self.overlay = Overlay(self, self.root)
        self.hotkey = Hotkey(lambda: self.ui(self.toggle), lambda m: self.ui(lambda: self.status(m)))
        self.hotkey.set(self.cfg["hotkey"])
        if self.cfg.first_run:
            self.status("Xush kelibsiz! Kursorni matn joyiga qoʻying, F9 ni bosing va gapiring")
            self.cfg.save()
        elif engines.ENGINES.get(self.cfg["engine"], engines.VoskEngine).needs_key and not self.cfg["api_key"]:
            self.status("API kalit kiritilmagan: ikki marta bosing → Sozlamalar")
        self.update_info, self.notice = None, False
        self.updater = Updater(self)
        self.updater.start()
        self.root.after(50, self.tick)

    # --- boshqa threadlardan UI ga ---
    def ui(self, fn):
        self.uiq.put(fn)

    def tick(self):
        while not self.uiq.empty():
            try:
                self.uiq.get_nowait()()
            except Exception as e:
                self.status(f"Xato: {e}")
        if self.state == "listening":
            self.overlay.level(self.level, self.cfg["noise_gate"])
        self.root.after(50, self.tick)

    # --- holat ---
    def toggle(self):
        self.stop() if self.state != "off" else self.start()

    def start(self):
        eng = engines.create(self)
        if eng.needs_key and not self.cfg["api_key"]:
            return self.status("Avval API kalitni kiriting (Sozlamalar)")
        self.session = eng
        self.set_state("connecting")
        eng.start()

    def stop(self):
        if self.session:
            self.session.stop()
        self.set_state("off")

    def fallback(self, s):
        """Aisha realtime ulanmasa — oddiy rejimga oʻtish."""
        if s is self.session and self.state != "off":
            self.status("Realtime ishlamadi → oddiy rejim")
            self.session = engines.AishaRest(self)
            self.session.start()

    def session_closed(self, s):
        if s is self.session and self.state != "off":
            self.set_state("off")

    def set_state(self, st):
        self.state = st
        self.overlay.render(st)
        if st == "off":
            self.level = 0.0
            if self.update_info:
                self.show_notice()  # tinglash tugagach eslatmani qayta koʻrsatish

    def status(self, text):
        self.notice = False
        self.overlay.text(text)

    def show_text(self, text):
        self.status(text)

    # --- yangilanish ---
    def update_available(self, info, urgent):
        self.update_info, self.urgent = info, urgent
        if self.state == "off":
            self.show_notice()

    def show_notice(self):
        v = self.update_info["version"]
        head = "⚠ Muhim yangilanish" if self.urgent else "🔄 Yangi versiya"
        self.status(f"{head} {v} — yangilash uchun shu yozuvni bosing")
        self.notice = True

    def text_clicked(self):
        if self.notice and self.update_info:
            self.notice = False
            self.status("Yangilanish yuklanmoqda…")
            self.updater.install()

    def run_installer(self, path):
        import os, subprocess
        from .winapi import release_instance
        if self.session:
            self.session.stop()
        self.hotkey.stop()
        release_instance()
        subprocess.Popen([path, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"],
                         creationflags=0x00000008 | 0x00000200)  # alohida jarayon
        os._exit(0)  # oʻrnatuvchi fayllarni almashtira olishi uchun darhol chiqish

    # --- oynalar ---
    def open_settings(self):
        from .ui.settings import Settings
        if self.settings_win:
            return self.settings_win.lift()
        self.settings_win = Settings(self)

    def apply_settings(self):
        if self.state != "off":
            self.stop()  # yangi sozlamalar keyingi yoqishda ishlaydi
        self.cfg.save()
        self.hotkey.set(self.cfg["hotkey"])
        self.overlay.render(self.state)
        self.status("Sozlamalar saqlandi")

    def open_lexicon(self):
        import os
        os.startfile(self.lexicon.path)

    def about(self):
        self.status(f"{APP} {VERSION} · {AUTHOR}")

    def quit(self):
        if self.session:
            self.session.stop()
        self.hotkey.stop()
        self.root.after(300, self.root.destroy)

    def run(self):
        self.root.mainloop()

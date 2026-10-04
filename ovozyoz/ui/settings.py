"""Sozlamalar oynasi — JSON faylni qoʻlda tahrirlash shart emas."""
import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import sounddevice as sd
from ..engines import LABELS
from ..engines.base import input_devices, resolve_device, RATE, BLOCK
from ..winapi import parse_hotkey, autostart_get, autostart_set

HOTKEYS = ["F9", "F8", "F10", "F12", "Pause", "ScrollLock", "ctrl+alt+space", "ctrl+shift+v"]
STD_MIC = "Standart mikrofon"


class Settings(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app, c = app, app.cfg
        self.title(f"{app.name} — Sozlamalar")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.test_stream = None
        pad = {"padx": 8, "pady": 3}

        # --- Nutqni aniqlash ---
        f = ttk.LabelFrame(self, text="Nutqni aniqlash")
        f.pack(fill="x", padx=10, pady=(10, 4))
        self.codes = list(LABELS)
        self.engine = tk.StringVar(value=LABELS.get(c["engine"], LABELS["vosk"]))
        ttk.Label(f, text="Dvigatel:").grid(row=0, column=0, sticky="w", **pad)
        cb = ttk.Combobox(f, textvariable=self.engine, values=[LABELS[k] for k in self.codes],
                          state="readonly", width=34)
        cb.grid(row=0, column=1, columnspan=2, sticky="w", **pad)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Label(f, text="Aisha API kalit:").grid(row=1, column=0, sticky="w", **pad)
        self.key = tk.StringVar(value=c["api_key"])
        self.key_entry = ttk.Entry(f, textvariable=self.key, show="•", width=36)
        self.key_entry.grid(row=1, column=1, columnspan=2, sticky="w", **pad)
        ttk.Label(f, text="Model papkasi:").grid(row=2, column=0, sticky="w", **pad)
        self.model = tk.StringVar(value=c["vosk_model"])
        self.model_entry = ttk.Entry(f, textvariable=self.model, width=27)
        self.model_entry.grid(row=2, column=1, sticky="w", **pad)
        self.model_btn = ttk.Button(f, text="Tanlash…", command=self.pick_model)
        self.model_btn.grid(row=2, column=2, sticky="w", **pad)

        # --- Mikrofon ---
        f = ttk.LabelFrame(self, text="Mikrofon")
        f.pack(fill="x", padx=10, pady=4)
        self.mic = tk.StringVar(value=c["mic_device"] or STD_MIC)
        ttk.Combobox(f, textvariable=self.mic, values=[STD_MIC] + input_devices(),
                     state="readonly", width=44).grid(row=0, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(f, text="Ovoz darajasi:").grid(row=1, column=0, sticky="w", **pad)
        self.meter = tk.Canvas(f, width=220, height=14, bg="#e8e8e8", highlightthickness=0)
        self.meter.grid(row=1, column=1, columnspan=2, sticky="w", **pad)
        ttk.Label(f, text="Shovqin chegarasi:").grid(row=2, column=0, sticky="w", **pad)
        self.gate = tk.IntVar(value=c["noise_gate"])
        ttk.Scale(f, from_=100, to=3000, variable=self.gate, length=150,
                  command=lambda v: self.gate.set(int(float(v)))).grid(row=2, column=1, sticky="w", **pad)
        ttk.Button(f, text="Avto sozlash", command=self.calibrate).grid(row=2, column=2, sticky="w", **pad)
        ttk.Label(f, text="Qizil chiziq — chegara. Gapirganda yashil ustun undan oshishi, "
                          "jim turganda past boʻlishi kerak.", wraplength=330,
                  foreground="#666").grid(row=3, column=0, columnspan=3, sticky="w", **pad)

        # --- Boshqaruv ---
        f = ttk.LabelFrame(self, text="Boshqaruv")
        f.pack(fill="x", padx=10, pady=4)
        ttk.Label(f, text="Tezkor tugma:").grid(row=0, column=0, sticky="w", **pad)
        self.hotkey = tk.StringVar(value=c["hotkey"])
        ttk.Combobox(f, textvariable=self.hotkey, values=HOTKEYS, width=18).grid(row=0, column=1, sticky="w", **pad)
        self.hover = tk.BooleanVar(value=c["hover_toggle"])
        ttk.Checkbutton(f, text="Tugma ustida turish bilan yoqish (ms):",
                        variable=self.hover).grid(row=1, column=0, sticky="w", **pad)
        self.hover_ms = tk.IntVar(value=c["hover_ms"])
        ttk.Spinbox(f, from_=400, to=3000, increment=100, textvariable=self.hover_ms,
                    width=8).grid(row=1, column=1, sticky="w", **pad)
        ttk.Label(f, text="Jimlikdan keyin toʻxtash (s):").grid(row=2, column=0, sticky="w", **pad)
        self.auto_stop = tk.IntVar(value=c["auto_stop_sec"])
        ttk.Spinbox(f, from_=10, to=900, increment=10, textvariable=self.auto_stop,
                    width=8).grid(row=2, column=1, sticky="w", **pad)
        self.autostart = tk.BooleanVar(value=autostart_get(app.name))
        ttk.Checkbutton(f, text="Windows bilan birga ishga tushirish",
                        variable=self.autostart).grid(row=3, column=0, columnspan=2, sticky="w", **pad)
        self.upd = tk.BooleanVar(value=c["update_check"])
        ttk.Checkbutton(f, text="Yangilanishlarni avtomatik tekshirish",
                        variable=self.upd).grid(row=4, column=0, columnspan=2, sticky="w", **pad)

        # --- Matn ---
        f = ttk.LabelFrame(self, text="Matn")
        f.pack(fill="x", padx=10, pady=4)
        self.apos = tk.StringVar(value=c["apostrophe"])
        ttk.Radiobutton(f, text="oʻ, gʻ (Unicode — rasmiy)", value="unicode",
                        variable=self.apos).grid(row=0, column=0, sticky="w", **pad)
        ttk.Radiobutton(f, text="o', g' (oddiy apostrof)", value="oddiy",
                        variable=self.apos).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(f, text="Klaviaturada yozilganda kutish (ms):").grid(row=1, column=0, sticky="w", **pad)
        self.typing = tk.IntVar(value=c["typing_pause_ms"])
        ttk.Spinbox(f, from_=200, to=3000, increment=100, textvariable=self.typing,
                    width=8).grid(row=1, column=1, sticky="w", **pad)

        # --- Tugmalar ---
        b = ttk.Frame(self)
        b.pack(fill="x", padx=10, pady=10)
        self.msg = ttk.Label(b, foreground="#c0392b")
        self.msg.pack(side="left")
        ttk.Button(b, text="Bekor qilish", command=self.close).pack(side="right", padx=4)
        ttk.Button(b, text="Saqlash", command=self.save).pack(side="right")

        self.refresh()
        self.start_meter()
        self.lift(); self.focus_force()

    def code(self):
        return self.codes[[LABELS[k] for k in self.codes].index(self.engine.get())]

    def refresh(self):
        aisha = self.code() != "vosk"
        self.key_entry.config(state="normal" if aisha else "disabled")
        for w in (self.model_entry, self.model_btn):
            w.config(state="disabled" if aisha else "normal")

    def pick_model(self):
        d = filedialog.askdirectory(parent=self, title="Vosk model papkasini tanlang")
        if d:
            self.model.set(d)

    # --- ovoz darajasi koʻrsatkichi ---
    def start_meter(self):
        if self.app.state == "off":  # dvigatel ishlamasa — oʻzimiz tinglaymiz
            try:
                def cb(indata, frames, t, status):
                    x = indata[:, 0].astype(np.float32)
                    self.app.level = float(np.sqrt(np.mean(x ** 2)))
                mic = None if self.mic.get() == STD_MIC else self.mic.get()
                self.test_stream = sd.InputStream(samplerate=RATE, channels=1, dtype="int16",
                                                  blocksize=BLOCK, device=resolve_device(mic),
                                                  callback=cb)
                self.test_stream.start()
            except Exception:
                self.test_stream = None
        self.samples = []
        self.draw_meter()

    def draw_meter(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return  # oyna yopilgan
        lvl, top = self.app.level, 3000
        self.samples = (self.samples + [lvl])[-30:]
        self.meter.delete("all")
        self.meter.create_rectangle(0, 0, 220 * min(1, lvl / top), 14, fill="#3ddc84", width=0)
        gx = 220 * min(1, self.gate.get() / top)
        self.meter.create_line(gx, 0, gx, 14, fill="#e0484f", width=2)
        self.after(80, self.draw_meter)

    def calibrate(self):
        self.msg.config(text="2 soniya jim turing…", foreground="#555")
        self.samples = []
        self.after(2000, self._calibrate_done)

    def _calibrate_done(self):
        noise = float(np.percentile(self.samples, 90)) if self.samples else 200
        self.gate.set(int(max(150, noise * 2.5 + 100)))  # shovqindan sezilarli yuqori
        self.msg.config(text=f"Chegara: {self.gate.get()}", foreground="#2e7d32")

    # --- saqlash ---
    def save(self):
        if parse_hotkey(self.hotkey.get())[1] is None:
            return self.msg.config(text="Tezkor tugma notoʻgʻri", foreground="#c0392b")
        try:
            vals = dict(hover_ms=int(self.hover_ms.get()), auto_stop_sec=int(self.auto_stop.get()),
                        typing_pause_ms=int(self.typing.get()))
        except (tk.TclError, ValueError):
            return self.msg.config(text="Raqamli maydonlarni tekshiring", foreground="#c0392b")
        if self.code() != "vosk" and not self.key.get().strip():
            return self.msg.config(text="Aisha uchun API kalit kerak", foreground="#c0392b")
        c = self.app.cfg
        c.update(vals, engine=self.code(), api_key=self.key.get().strip(),
                 vosk_model=self.model.get().strip(), hotkey=self.hotkey.get().strip(),
                 mic_device=None if self.mic.get() == STD_MIC else self.mic.get(),
                 noise_gate=int(self.gate.get()), hover_toggle=self.hover.get(),
                 apostrophe=self.apos.get(), update_check=self.upd.get())
        try:
            autostart_set(self.app.name, self.autostart.get())
        except OSError:
            pass
        self.app.apply_settings()
        self.close()

    def close(self):
        if self.test_stream:
            try:
                self.test_stream.stop(); self.test_stream.close()
            except Exception:
                pass
        if self.app.state == "off":
            self.app.level = 0.0
        self.app.settings_win = None
        self.destroy()

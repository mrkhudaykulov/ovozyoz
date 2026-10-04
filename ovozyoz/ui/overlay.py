"""Ekrandagi kichik ustun oyna: mikrofon tugmasi, holat, jonli matn."""
import tkinter as tk
from ..winapi import no_activate

BG, GREY, ORANGE, RED = "#1f2430", "#5c6370", "#e5a03b", "#e0484f"
STATES = {"off": (GREY, "Oʻchiq"), "connecting": (ORANGE, "Ulanmoqda…"),
          "listening": (RED, "Tinglayapman")}


class Overlay:
    def __init__(self, app, root):
        self.app, r = app, root
        self.root = r
        r.title(app.name)
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.94)
        r.configure(bg=BG)
        self.cv = tk.Canvas(r, width=56, height=56, bg=BG, highlightthickness=0)
        self.cv.grid(row=0, column=0, rowspan=2, padx=6, pady=6)
        self.btn = self.cv.create_oval(7, 7, 49, 49, fill=GREY, outline="#3ddc84", width=0)
        self.cv.create_text(28, 28, text="🎤", font=("Segoe UI Emoji", 15))
        self.lbl_status = tk.Label(r, fg="#d7dae0", bg=BG, font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_status.grid(row=0, column=1, sticky="we", padx=(0, 8), pady=(6, 0))
        self.lbl_text = tk.Label(r, fg="#abb2bf", bg=BG, font=("Segoe UI", 9), anchor="nw",
                                 justify="left", wraplength=250, width=36, height=2)
        self.lbl_text.grid(row=1, column=1, sticky="we", padx=(0, 8), pady=(0, 6))

        self.cv.bind("<Button-1>", lambda e: app.toggle())
        self.cv.bind("<Enter>", self.hover_in)
        self.cv.bind("<Leave>", self.hover_out)
        self.hover_job = None
        for w in (self.lbl_status, self.lbl_text):  # sudrab koʻchirish
            w.bind("<ButtonPress-1>", self.drag_start)
            w.bind("<B1-Motion>", self.drag_move)
            w.bind("<ButtonRelease-1>", self.drag_end)
            w.bind("<Double-Button-1>", lambda e: app.open_settings())

        m = tk.Menu(r, tearoff=0)
        m.add_command(label="Sozlamalar…", command=app.open_settings)
        m.add_command(label="Lugʻat (tuzatishlar)…", command=app.open_lexicon)
        m.add_command(label="Yangilanishni tekshirish", command=lambda: app.updater.check_async())
        m.add_command(label="Dastur haqida", command=app.about)
        m.add_separator()
        m.add_command(label="Chiqish", command=app.quit)
        r.bind("<Button-3>", lambda e: m.tk_popup(e.x_root, e.y_root))  # bolalar ham meros oladi

        self.render("off")
        r.update_idletasks()
        pos = app.cfg.get("window_pos")
        if pos:
            r.geometry(f"+{pos[0]}+{pos[1]}")
        else:
            r.geometry(f"+{r.winfo_screenwidth() - r.winfo_width() - 24}"
                       f"+{r.winfo_screenheight() - r.winfo_height() - 80}")
        no_activate(r)

    def render(self, state):
        color, label = STATES[state]
        self.cv.itemconfig(self.btn, fill=color)
        self.lbl_status.config(text=f"{label} · {self.app.cfg['hotkey']}")

    def text(self, t):
        self.lbl_text.config(text=t[-110:])

    def level(self, lvl, gate):
        if not self.hover_job:
            w = min(5, lvl / max(1, gate) * 2)
            self.cv.itemconfig(self.btn, width=w, outline="#3ddc84" if w >= 2 else "#56606e")

    def hover_in(self, e):
        if self.app.cfg["hover_toggle"]:
            self.cv.itemconfig(self.btn, width=2, outline="#61afef")
            self.hover_job = self.root.after(self.app.cfg["hover_ms"], self.hover_fire)

    def hover_out(self, e):
        if self.hover_job:
            self.root.after_cancel(self.hover_job)
            self.hover_job = None
        self.cv.itemconfig(self.btn, width=0)

    def hover_fire(self):
        self.hover_job = None  # qayta yoqish uchun sichqonchani olib qaytarish kerak
        self.cv.itemconfig(self.btn, width=0)
        self.app.toggle()

    def drag_start(self, e):
        self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()
        self._press = (e.x_root, e.y_root)

    def drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def drag_end(self, e):
        if abs(e.x_root - self._press[0]) + abs(e.y_root - self._press[1]) < 4:
            return self.app.text_clicked()  # sudralmadi — oddiy bosish
        self.app.cfg["window_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        self.app.cfg.save()

"""Windows API: matn kiritish, tezkor tugma, kuzatuv, avtoyuklash (admin kerak emas)."""
import ctypes, re, sys, threading, time
from ctypes import wintypes
from pathlib import Path

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.GetAsyncKeyState.restype = ctypes.c_short
ULONG_PTR = ctypes.c_size_t
VK_BACK, VK_RETURN, VK_CONTROL = 0x08, 0x0D, 0x11
KEYUP, UNICODE = 0x0002, 0x0004
MODS = {0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5}  # Shift/Ctrl/Alt/Win


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)


def _key(vk=0, scan=0, flags=0):
    i = INPUT(type=1)
    i.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
    return i


def _send(items):
    for k in range(0, len(items), 40):  # boʻlib yuborish: brauzer harflarni yoʻqotmasligi uchun
        part = items[k:k + 40]
        user32.SendInput(len(part), (INPUT * len(part))(*part), ctypes.sizeof(INPUT))
        time.sleep(0.004)


def type_text(text):
    items = []
    for ch in text:
        if ch == "\n":
            items += [_key(VK_RETURN), _key(VK_RETURN, flags=KEYUP)]
            continue
        b = ch.encode("utf-16-le")
        for j in range(0, len(b), 2):
            u = int.from_bytes(b[j:j + 2], "little")
            items += [_key(scan=u, flags=UNICODE), _key(scan=u, flags=UNICODE | KEYUP)]
    _send(items)


def press(*vks, times=1):
    items = []
    for _ in range(times):
        items += [_key(v) for v in vks] + [_key(v, flags=KEYUP) for v in reversed(vks)]
    _send(items)


def parse_hotkey(s):
    """'ctrl+alt+space' -> (mods, vk); notoʻgʻri boʻlsa vk=None."""
    mods, vk = 0x4000, None  # MOD_NOREPEAT
    for p in (s or "").lower().replace(" ", "").split("+"):
        if p in ("ctrl", "alt", "shift", "win"):
            mods |= {"alt": 1, "ctrl": 2, "shift": 4, "win": 8}[p]
        elif re.fullmatch(r"f([1-9]|1\d|2[0-4])", p):
            vk = 0x6F + int(p[1:])
        elif p in ("space", "pause", "scrolllock"):
            vk = {"space": 0x20, "pause": 0x13, "scrolllock": 0x91}[p]
        elif len(p) == 1 and p.isalnum():
            vk = ord(p.upper())
        else:
            return mods, None
    return mods, vk


class Watch(threading.Thread):
    """Klaviatura va sichqoncha faolligini kuzatadi."""
    def __init__(self):
        super().__init__(daemon=True)
        self.last_key = self.last_click = 0.0
        self.last_vk, self.paused = None, False

    @staticmethod
    def down(rng):
        return any(user32.GetAsyncKeyState(v) & 0x8000 for v in rng)

    def run(self):
        while True:
            if not self.paused:
                now = time.monotonic()
                vk = next((v for v in range(8, 255) if v not in MODS
                           and user32.GetAsyncKeyState(v) & 0x8000), None)
                if vk:
                    self.last_key, self.last_vk = now, vk
                if self.down((1, 2, 4)):
                    self.last_click = now
            time.sleep(0.03)


class Hotkey:
    """Global tezkor tugma (RegisterHotKey — hook emas, antivirusga xavfsiz)."""
    def __init__(self, on_press, on_error):
        self.on_press, self.on_error = on_press, on_error
        self.tid, self.thread = None, None

    def set(self, spec):
        self.stop()
        mods, vk = parse_hotkey(spec)
        if vk is None:
            return self.on_error("Tezkor tugma notoʻgʻri yozilgan")
        self.thread = threading.Thread(target=self._loop, args=(mods, vk), daemon=True)
        self.thread.start()

    def _loop(self, mods, vk):
        self.tid = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, 1, mods, vk):
            return self.on_error("Tezkor tugma band, boshqasini tanlang")
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:
                self.on_press()
        user32.UnregisterHotKey(None, 1)

    def stop(self):
        if self.tid:
            user32.PostThreadMessageW(self.tid, 0x0012, 0, 0)  # WM_QUIT
            self.thread.join(timeout=1)
            self.tid = None


def no_activate(tk_root):
    """Oyna fokusni olmaydi — matn EDO/Word oynasiga tushaveradi."""
    hwnd = user32.GetParent(tk_root.winfo_id()) or tk_root.winfo_id()
    style = user32.GetWindowLongW(hwnd, -20)
    user32.SetWindowLongW(hwnd, -20, style | 0x08000000 | 0x00000080)  # NOACTIVATE | TOOLWINDOW


_mutex = None


def single_instance(name):
    global _mutex
    _mutex = kernel32.CreateMutexW(None, False, "Local\\" + name)
    return ctypes.get_last_error() != 183  # 183 = allaqachon ishlayapti


def release_instance():
    """Oʻrnatuvchi "dastur ishlayapti" deb kutib qolmasligi uchun."""
    global _mutex
    if _mutex:
        kernel32.CloseHandle(_mutex)
        _mutex = None


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _autostart_cmd():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pyw}" "{Path(sys.argv[0]).resolve()}"'


def autostart_get(name):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, name)
            return True
    except OSError:
        return False


def autostart_set(name, on):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, _autostart_cmd())
        else:
            try:
                winreg.DeleteValue(k, name)
            except OSError:
                pass

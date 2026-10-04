"""Matnga ishlov berish: apostroflar va ovozli buyruqlar."""
import re

OKINA, TUTUQ = "\u02bb", "\u02bc"
APOS = "'\u2018\u2019`\u02bb\u02bc"
PUNCT = {"nuqta": ".", "vergul": ",", "so'roq belgisi": "?", "undov belgisi": "!",
         "ikki nuqta": ":", "nuqtali vergul": ";"}
NEWLINE = {"yangi qator", "keyingi qator", "yangi xatboshi", "xatboshi"}
DEL_WORD = {"o'chir", "so'zni o'chir"}
UNDO = {"bekor qil", "bekor qilish"}
STOP = {"to'xta", "to'xtat", "yozishni to'xtat"}


def fix_apostrophes(t, style):
    t = re.sub(f"([OoGg])[{APOS}]", lambda m: m.group(1) + OKINA, t)
    t = re.sub(f"(?<=\\w)(?<![OoGg])[{APOS}](?=\\w)", TUTUQ, t)
    if style == "oddiy":
        t = t.replace(OKINA, "'").replace(TUTUQ, "'")
    return t


def key_of(t):
    t = re.sub(f"[{APOS}]", "'", t.lower())
    return re.sub(r"[^\w' ]", "", t).strip()


def trailing_punct(text, k):
    """'... nuqta' bilan tugasa — soʻzni belgiga almashtiradi."""
    for name in sorted(PUNCT, key=len, reverse=True):
        if k.endswith(" " + name):
            words = text.split()
            return " ".join(words[:-len(name.split())]).rstrip(".,!?;: ") + PUNCT[name]
    return text


DEFAULT_LEXICON = """# OvozYoz lugʻati — dastur notoʻgʻri yozgan soʻzlarni tuzatadi.
# Har qatorda:  notoʻgʻri = toʻgʻri   (bir nechta soʻzdan iborat boʻlishi ham mumkin)
# Faylni saqlang — oʻzgarish darhol ishlaydi, dasturni qayta ochish shart emas.
# Misollar (oldidagi # ni olib tashlasangiz ishlaydi):
# siz = SIZ
# pe ef = PF
# maxsus iqtisodiy zona = maxsus iqtisodiy zona (MIZ)
"""


def _norm(t):
    return re.sub(f"[{APOS}]", "'", t)


class Lexicon:
    """Foydalanuvchi lugʻati: notoʻgʻri = toʻgʻri."""
    def __init__(self, path):
        self.path, self.mtime, self.rules = path, None, []
        if not path.exists():
            path.write_text(DEFAULT_LEXICON, encoding="utf-8-sig")

    def load(self):
        try:
            m = self.path.stat().st_mtime
        except OSError:
            return
        if m == self.mtime:
            return
        self.mtime, rules = m, []
        for line in self.path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            a, b = (x.strip() for x in line.split("=", 1))
            if a:
                rx = re.compile(r"(?<![\w'])" + re.escape(_norm(a)) + r"(?![\w'])", re.I)
                rules.append((len(a), rx, b))
        self.rules = sorted(rules, key=lambda r: -r[0])  # uzun iboralar birinchi

    def apply(self, t):
        self.load()
        t = _norm(t)
        for _, rx, b in self.rules:
            t = rx.sub(lambda m, b=b: b, t)
        return t

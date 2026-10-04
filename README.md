# OvozYoz 0.7 — oʻzbekcha ovozli yozish

Kursor turgan istalgan joyga (EDO xat oynasi, Word, brauzer) gapirganingizni yozadi.
Sukut boʻyicha tekin va offline (Vosk), internet va API kalit kerak emas.

## Oʻrnatish (xodim uchun)
`OvozYoz-Setup-0.7.exe` ni ishga tushiring → "Далее" → "Установить". Admin kerak emas, internet kerak emas.
Windows "компьютер защищён" desa: "Подробнее" → "Выполнить в любом случае"
(dastur hali raqamli imzolanmagan).

## Oʻrnatuvchini yigʻish (dasturchi uchun)
1. Python 3.11+ 64-bit — python.org, "Install for current user", "Add to PATH".
2. Inno Setup 6.3+ — jrsoftware.org/isdl.php ("Install for me only" tanlansa admin kerak emas).
3. `build.bat` → modelni oʻzi yuklab oladi va `Output\OvozYoz-Setup-0.7.exe` ni yaratadi.

## Ishlatish
- **F9** yoki 🎤 tugmasi (yoki ustida ~1 s turish) — yoqish/oʻchirish.
- Oynaga **ikki marta bosish** yoki oʻng tugma → **Sozlamalar…**
- Kulrang — oʻchiq, toʻq sariq — ulanmoqda, qizil — tinglayapti.
- Klaviaturada yozsangiz, dastur siz toʻxtaguningizcha kutadi.

## Ovozli buyruqlar
nuqta, vergul, ikki nuqta, soʻroq belgisi, undov belgisi · gap oxiridagi "nuqta" ·
yangi qator / yangi xatboshi · oʻchir (oxirgi soʻz) · bekor qil (oxirgi boʻlak) · toʻxta

## Sozlamalar oynasi
Dvigatel (Vosk / Aisha), mikrofon, shovqin chegarasi (jonli koʻrsatkich va "Avto sozlash"),
tezkor tugma, ustida turish bilan boshqarish, avtomatik toʻxtash, Windows bilan ishga tushirish,
oʻ/gʻ yozilishi. Sozlamalar `%APPDATA%\OvozYoz\config.json` da saqlanadi.

## Kod tuzilishi
```
main.py                  ishga tushirish
ovozyoz/app.py           ilova markazi, holat
ovozyoz/config.py        sozlamalar
ovozyoz/textproc.py      apostroflar, ovozli buyruqlar
ovozyoz/writer.py        kursor joyiga yozish
ovozyoz/winapi.py        Windows: matn kiritish, tezkor tugma, avtoyuklash
ovozyoz/engines/         dvigatellar (base, vosk_engine, aisha) — yangisi shu yerga
ovozyoz/ui/              ustun oyna va sozlamalar oynasi
```

## Yangilanishlar
Dastur kuniga bir marta GitHub'dagi `version.json` ni tekshiradi (imzosi tekshiriladi).
Yangi versiya boʻlsa, oynada eslatma chiqadi — bosilsa yuklab, jim oʻrnatib, qayta ochiladi.
Sozlamalarda oʻchirish mumkin. Oʻng tugma → "Yangilanishni tekshirish" — qoʻlda tekshirish.

### Bir martalik tayyorgarlik (muallif)
1. github.com da hisob oching va **ochiq** ombor yarating, masalan `OvozYoz-releases`
   (unga faqat relizlar yuklanadi, manba kod emas).
2. `python tools\make_keys.py` → chiqqan `PUBKEY` qatorini va ombor nomini
   (`UPDATE_REPO = "login/OvozYoz-releases"`) `ovozyoz/__init__.py` ga yozing.
3. Maxfiy kalit `%USERPROFILE%\.ovozyoz\update_private.pem` — zaxira nusxa oling, hech kimga bermang.
   Yoʻqotilsa, tarqatilgan dasturlar yangilana olmaydi.

### Har bir yangi versiya
1. `ovozyoz/__init__.py` da `VERSION` ni oshiring (masalan 0.8).
2. `build.bat` → `Output\OvozYoz-Setup-0.8.exe`.
3. `python tools\make_release.py "Nimalar yangi"` → `Output\version.json`.
4. GitHub → Releases → Draft a new release → tag `v0.8` → ikkala faylni yuklang → Publish.

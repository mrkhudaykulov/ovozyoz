"""OvozYoz — oʻzbekcha ovozli yozish yordamchisi."""
APP = "OvozYoz"
VERSION = "0.7"
AUTHOR = "© 2026 Xudaykulov Uchqun Yunusovich"

# Yangilanishlar: GitHub'dagi ochiq "relizlar" ombori (masalan "uchqun/OvozYoz-releases")
UPDATE_REPO = ""
# tools/make_keys.py chiqargan ochiq kalit (base64)
PUBKEY = ""
UPDATE_URLS = ([f"https://github.com/{UPDATE_REPO}/releases/latest/download/version.json"]
               if UPDATE_REPO else [])

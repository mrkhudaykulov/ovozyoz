"""OvozYoz — oʻzbekcha ovozli yozish yordamchisi."""
APP = "OvozYoz"
VERSION = "0.8"
AUTHOR = "© 2026 Xudaykulov Uchqun Yunusovich"

# Yangilanishlar: GitHub'dagi ochiq "relizlar" ombori (masalan "uchqun/OvozYoz-releases")
UPDATE_REPO = "mrkhudaykulov/ovozyoz"
# tools/make_keys.py chiqargan ochiq kalit (base64)
PUBKEY = "MsVMLCOvhWkQn5Tth7Oyb358lvJ7Hs+9qiJ0Ckhn5AQ="
UPDATE_URLS = ([f"https://github.com/{UPDATE_REPO}/releases/latest/download/version.json"]
               if UPDATE_REPO else [])

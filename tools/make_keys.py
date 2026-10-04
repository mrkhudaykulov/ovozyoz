"""Bir marta ishga tushiriladi: yangilanishlarni imzolash uchun kalit juftligini yaratadi."""
import base64
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

KEY = Path.home() / ".ovozyoz" / "update_private.pem"  # loyiha papkasidan tashqarida

if KEY.exists():
    raise SystemExit(f"Kalit allaqachon bor: {KEY}\nUni almashtirsangiz, eski versiyalar yangilana olmaydi!")
KEY.parent.mkdir(parents=True, exist_ok=True)
priv = Ed25519PrivateKey.generate()
KEY.write_bytes(priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                   serialization.NoEncryption()))
pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
print("Maxfiy kalit saqlandi:", KEY)
print("MUHIM: uni hech kimga bermang va fleshkaga zaxira nusxa oling.\n")
print("ovozyoz/__init__.py dagi PUBKEY ga quyidagini qoʻying:")
print(f'PUBKEY = "{base64.b64encode(pub).decode()}"')

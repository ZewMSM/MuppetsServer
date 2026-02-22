import base64
import hashlib
import json
import logging
from os import environ

from Crypto.Cipher import AES

logger = logging.getLogger("MuppetsServer/Utils")


def md5(string: str) -> str:
    return hashlib.md5(string.encode("utf-8")).hexdigest()


def aes_encrypt(message: str, initial_vector_string: str, secret_key: str) -> str:
    key = secret_key.encode("utf-8")
    iv = initial_vector_string.encode("utf-8")
    cipher = AES.new(key, AES.MODE_CFB, iv, segment_size=8)
    ciphertext = cipher.encrypt(message.encode("utf-8"))
    return base64.b64encode(ciphertext).decode("utf-8")


def aes_decrypt(
    encrypted_data: str, initial_vector_string: str, secret_key: str
) -> str:
    key = secret_key.encode("utf-8")
    iv = initial_vector_string.encode("utf-8")
    ciphertext = base64.b64decode(encrypted_data)
    cipher = AES.new(key, AES.MODE_CFB, iv, segment_size=8)
    return cipher.decrypt(ciphertext).decode("utf-8")


def decrypt_token(encrypted_token: str) -> dict | None:
    if not encrypted_token:
        return None
    try:
        decrypted_data = aes_decrypt(
            encrypted_token.encode("UTF-8"),
            environ.get("TOKEN_IV"),
            environ.get("TOKEN_KEY"),
        )
        return json.loads(decrypted_data)
    except Exception:
        logger.warning("Failed to decrypt token", exc_info=True)
        return None

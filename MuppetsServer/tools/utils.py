import base64
import hashlib
import json
from os import environ

from Crypto.Cipher import AES


def md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def aes_encrypt(message, initial_vector_string, secret_key):
    key = secret_key.encode('utf-8')
    iv = initial_vector_string.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CFB, iv, segment_size=8)
    ciphertext = cipher.encrypt(message.encode('utf-8'))
    encoded = base64.b64encode(ciphertext).decode('utf-8')
    return encoded


def aes_decrypt(encrypted_data, initial_vector_string, secret_key):
    key = secret_key.encode('utf-8')
    iv = initial_vector_string.encode('utf-8')
    ciphertext = base64.b64decode(encrypted_data)
    cipher = AES.new(key, AES.MODE_CFB, iv, segment_size=8)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext.decode('utf-8')


def decrypt_token(encrypted_token):
    if encrypted_token:
        try:
            decrypted_data = aes_decrypt(encrypted_token.encode("UTF-8"), environ.get("TOKEN_IV"), environ.get("TOKEN_KEY"))
            return json.loads(decrypted_data)
        except Exception as e:
            print(e)
            return None
    else:
        return None

def generate_bind_link(user_id):
    hash = md5(f"S45d76F*&G9*N&FB6c5x4e^C%R:{user_id}")
    data = f'bind:{user_id}:{hash}'
    encoded = base64.b64encode(data.encode("utf-8")).decode('utf-8')

    return f'https://t.me/zewmsm_bot?start={encoded}'
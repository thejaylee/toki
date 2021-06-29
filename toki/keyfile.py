import json
import os
#import signal
from argparse import ArgumentParser
from base64 import b64encode, b64decode, urlsafe_b64encode
from math import floor
from pyotp import TOTP
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import ciphers
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CanNotDecrypt(Exception):
    pass

class KeyFile:
    def __init__(self, filepath, passphrase, create_file=False):
        self._filepath = os.path.expanduser(filepath)
        self._passphrase = passphrase
        self._salt   = None
        self._iv     = None
        self._tag    = None

        if create_file:
            print(f"initializing {self._filepath}")
            self._salt = os.urandom(16)
            self._iv = os.urandom(16)
            self.write_keys({})


    def read_keys(self) -> dict:
        with open(self._filepath, 'r') as f:
            data = json.loads(f.read())
        if not all(k in data for k in ['iv', 'salt', 'encrypted_data', 'tag']):
            raise ValueError(f"{self._filepath} exists but is invalid")
        self._salt = b64decode(data['salt'])
        self._iv   = b64decode(data['iv'])
        self._tag  = b64decode(data['tag'])
        dec = create_cipher(pass2key(self._passphrase, self._salt), self._iv, tag=self._tag).decryptor()
        try:
            return json.loads(dec.update(b64decode(data['encrypted_data'])) + dec.finalize())
        except InvalidTag:
            raise CanNotDecrypt


    def write_keys(self, keys:dict):
        with open(self._filepath, 'w+') as f:
            enc = create_cipher(pass2key(self._passphrase, self._salt), self._iv).encryptor()
            encdata = enc.update(json.dumps(keys).encode()) + enc.finalize()
            self._tag = enc.tag
            f.write(json.dumps({
                'salt': b64encode(self._salt).decode(),
                'iv': b64encode(self._iv).decode(),
                'encrypted_data': b64encode(encdata).decode(),
                'tag': b64encode(self._tag).decode(),
            }, separators=(',', ':')))

def create_cipher(key, iv, tag=None):
    alg     = ciphers.algorithms.AES(key)
    mode    = ciphers.modes.GCM(iv, tag) if tag else ciphers.modes.GCM(iv)
    return ciphers.Cipher(alg, mode, backend=default_backend())

def pass2key(passphrase, salt):
    kdf = PBKDF2HMAC(
        algorithm = hashes.SHA256(),
        length = 32,
        salt = salt,
        iterations = 100000,
        backend = default_backend(),
    )
    return kdf.derive(passphrase.encode())

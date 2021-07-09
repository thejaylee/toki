#!/usr/bin/python3

import base64
import json
import os
#import signal
import time
import sys
from argparse import ArgumentParser
from base64 import b64encode, b64decode, urlsafe_b64encode
from math import floor
from pyotp import TOTP
from time import sleep
from getpass import getpass
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import ciphers
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DEFAULT_KEYFILE = '~/.otp.keys'

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
        keys = json.loads(dec.update(b64decode(data['encrypted_data'])) + dec.finalize())
        return keys


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

def parse_args():
    ap = ArgumentParser(description="One Time Pads")
    ap.add_argument('-a', dest="name", metavar="name", help="add an OTP")
    ap.add_argument('-p', action="store_true", dest="private", help="disable local echo for the key prompt when adding a key")
    ap.add_argument('-k', dest="keyfile", default=DEFAULT_KEYFILE, metavar="keyfile", help=f"keyfile to use (default: {DEFAULT_KEYFILE}")
    ap.add_argument('-c', action="store_true", dest="create", help="Create new OTP keyfile. This will overwrite existing <keyfile>")
    return ap.parse_args()

def otp_loop(keys):
    otps = {name:TOTP(key) for (name, key) in keys.items()}
    width = max(map(lambda x: len(x), keys.keys())) + 1
    while True:
        os.system("clear")
        for (name, otp) in otps.items():
            print(f"{name:{width}}: " + otp.now())
        ttl = floor(time.time()) % 30
        print('[' + ('|' * ttl) + ("-" * (29 - ttl)) + ']')
        sleep(1)



if __name__ == '__main__':
    args = parse_args()
    if not os.path.isfile(os.path.expanduser(args.keyfile)) and not args.create:
        print(f"keyfile {args.keyfile} does not exist. use -c to create new")
        sys.exit(-1)

    passphrase = getpass()

    kf = KeyFile(args.keyfile, passphrase, create_file=args.create)
    try:
        keys = kf.read_keys()
    except InvalidTag:
        print("could not decrypt key data. probably bad password")
        sys.exit(-2)

    if args.name is not None:
        if args.private:
            key = getpass()
        else:
            key = input("key: ")
        keys[args.name] = key
        kf.write_keys(keys)
    else:
        otp_loop(keys)

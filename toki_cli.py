#!/usr/bin/python3

import os
import time
import sys
from argparse import ArgumentParser
from math import floor
from pyotp import TOTP
from time import sleep
from getpass import getpass

from toki.keyfile import KeyFile

DEFAULT_KEYFILE = './.totp.keys'

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

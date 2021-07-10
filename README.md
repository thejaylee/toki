# Toki
A very simple app for managing Time-Based One Time Pads (TOTP)

## Usage
```
pip install -r requirements.txt
python3 toki.pyw
```

## Running
If the program is run with no `.totp.keys` file present then one will be created and encrypted by the password entered
at the unlock screen.

Subsequent runs of the program will require the password to unlock the keyfile.

Clicking an active TOTP token will copy it to the clipboard.

## CLI
Included is a previous CLI version (toki_cli.py) which can be run in terminal.

## Security
The `.totp.keys` file is AES-GCM encrypted via a PBKDF2 key.
However, the TOTP secrets remain resident in memory while the app is running.

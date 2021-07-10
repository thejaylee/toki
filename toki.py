from contextlib import suppress
from os import path
from threading import Thread
from time import sleep, time
from traceback import print_exc
from typing import Any, Callable, Dict, List, Union, Tuple

import clipboard
from pyotp import TOTP

from toki.events import Event, EventSystem, GlobalEvents
from toki.keyfile import CanNotDecrypt, KeyFile
from toki.ui import UI
from toki.util import first

DEFAULT_KEYFILE = './.otp.keys'

class Application:
    def __init__(self):
        self.keyfile = None
        self.events = GlobalEvents()
        self.totps = {}
        self.current_totp_name = None
        self.events = GlobalEvents.get_event_system()
        self.events.subscribe(Event.PASSWORD, self.handle_on_password)
        self.events.subscribe(Event.TOTP_SELECTED, self.handle_totp_selected)
        self.events.subscribe(Event.ADD_TOTP, self.handle_add_totp)
        self.events.subscribe(Event.REMOVE_TOTP, self.handle_remove_totp)
        self.events.subscribe(Event.COPY_TOTP, self.handle_copy_totp)
        self.events.subscribe(Event.MENU_EXIT, self.exit)
        self.ui = UI()
        self.ui.title(f"Toki")
        self.ui.geometry("256x384")
        self.running = True
        self._timer_thread = Thread(None, self._timer_thread, daemon=True)
        self._timer_thread.start()

    def _timer_thread(self) -> None:
        while self.running:
            try:
                if (time() % 30) < 1.0 and self.current_totp_name in self.totps:
                    self.events.publish(Event.TOTP_UPDATE, (self.current_totp_name, self.totps[self.current_totp_name].now()))
                self.events.publish(Event.TIMER_UPDATE, time() % 30 / 30)
            except Exception as ex:
                print("Exception in timer thread")
                print_exc()
            finally:
                sleep(0.2)

    def handle_on_password(self, password: str) -> None:
        if self.load_totps_file(password):
            self.events.publish(Event.TOTP_LIST, list(self.totps.keys()))
            self.handle_totp_selected(first(self.totps))

    def handle_totp_selected(self, name: str) -> None:
        if name in self.totps:
            totp = self.totps[name]
            self.current_totp_name = name
            self.events.publish(Event.TOTP_UPDATE, (name, totp.now()))

    def handle_add_totp(self, totp: Tuple[str, str], *args, **kwargs) -> None:
        if not self.keyfile:
            return

        name, secret = totp
        self.totps[name] = TOTP(secret)
        self.keyfile.write_keys({n:t.secret for n,t in self.totps.items()})
        self.events.publish(Event.TOTP_LIST, list(self.totps.keys()))

    def handle_remove_totp(self, name: str, *args, **kwargs) -> None:
        if not self.keyfile:
            return

        del self.totps[name]
        self.keyfile.write_keys({n:t.secret for n,t in self.totps.items()})
        self.events.publish(Event.TOTP_LIST, list(self.totps.keys()))

    def handle_copy_totp(self, *args, **kwargs) -> None:
        if not self.current_totp_name:
            return

        clipboard.copy(self.totps[self.current_totp_name].now())

    def start(self) -> None:
        self.ui.mainloop()

    def exit(self, *args, **kwargs) -> None:
        self.ui.destroy()
        self.running = False
        self.events.stop()
        exit()

    def load_totps_file(self, password: str) -> bool:
        keyfile = KeyFile(DEFAULT_KEYFILE, password, create_file=not path.isfile(DEFAULT_KEYFILE))
        try:
            totps = keyfile.read_keys()
            self.totps = {name:TOTP(totp) for name, totp in totps.items()}
            self.keyfile = keyfile
            return True
        except CanNotDecrypt:
            return False


if __name__ == "__main__":
    print('starting up')
    app = Application()
    app.start()

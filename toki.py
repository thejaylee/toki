from contextlib import suppress
from functools import partial
from pyotp import TOTP
from threading import Thread
from time import sleep, time
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from typing import Any, Callable, Dict, List, Union, Tuple

from toki.events import EventSystem, GlobalEvents
from toki.prop_helpers import NestedPropertiesDict
from toki.keyfile import CanNotDecrypt, KeyFile
from toki.util import first

DEFAULT_KEYFILE = './.otp.keys'

class Event:
    PASSWORD = '<<PASSWORD>>'
    TOTP_LIST = '<<TOTP_LIST>>'
    TOTP_SELECTED = '<<TOTP_SELECTED>>'
    TOTP_UPDATE = '<<TOTP_UPDATE>>'
    TIMER_UPDATE = '<<TIMER_UPDATE>>'
    MENU_ADD_TOTP = '<<MENU_FILE_ADD_TOTP>>'
    MENU_EXIT = '<<MENU_FILE_EXIT>>'

class Application(GlobalEvents):
    def __init__(self):
        self.totps = {}
        self.current_totp_name = None
        self.events = EventSystem()
        self.event_subscribe(Event.PASSWORD, self._on_password)
        self.event_subscribe(Event.TOTP_SELECTED, self._totp_selected)
        self.event_subscribe(Event.MENU_EXIT, self.exit)
        self.ui = UI()
        self.ui.title(f"Toki")
        self.ui.geometry("256x384")
        self.running = True
        self._timer_thread = Thread(None, self._timer_thread, daemon=True)
        self._timer_thread.start()

    def _timer_thread(self) -> None:
        while self.running:
            if (time() % 30) < 1.0:
                self.event_publish(Event.TOTP_UPDATE, (self.current_totp_name, self.totps[self.current_totp_name].now()))
            self.event_publish(Event.TIMER_UPDATE, time() % 30 / 30)
            sleep(0.2)

    def _on_password(self, password: str) -> None:
        if self.load_totps_file(password):
            self.event_publish(Event.TOTP_LIST, list(self.totps.keys()))
            self._totp_selected(first(self.totps))

    def _totp_selected(self, name: str) -> None:
        if name in self.totps:
            totp = self.totps[name]
            self.current_totp_name = name
            self.event_publish(Event.TOTP_UPDATE, (name, totp.now()))

    def start(self) -> None:
        self.ui.mainloop()

    def exit(self, *args, **kwargs) -> None:
        self.ui.destroy()
        self.running = False
        self.events.stop()
        exit()

    def load_totps_file(self, password: str) -> bool:
        keyfile = KeyFile(DEFAULT_KEYFILE, password, create_file=False)
        try:
            totps = keyfile.read_keys()
            self.totps = {name:TOTP(totp) for name, totp in totps.items()}
            return True
        except CanNotDecrypt:
            return False

class UI(tk.Tk, GlobalEvents):
    class _MenuBar(tk.Menu, GlobalEvents):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            print('creating menus')
            filemenu = tk.Menu(self, tearoff=0)
            filemenu.add_command(label="Add TOTP", command=lambda: self.event_publish(Event.MENU_TEST))
            filemenu.add_separator()
            filemenu.add_command(label="Exit", command=lambda: self.event_publish(Event.MENU_EXIT))
            self.add_cascade(label="File", menu=filemenu)


    def __init__(self, *args, **kwargs):
        print('creating main window')
        super().__init__(*args, **kwargs)
        self._ui = NestedPropertiesDict()
        self._init_menus()
        self._init_frames()
        self._init_events()
        self._func = NestedPropertiesDict()

    def _init_menus(self):
        self._ui.menu = __class__._MenuBar(self)
        self.config(menu=self._ui.menu)

    def _init_frames(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self._ui.container = container
        self._ui.frame.password = PasswordFrame(container)
        self._ui.frame.totps = TotpsFrame(container)
        self._show_frame(self._ui.frame.password)

    def _init_events(self):
        self.event_subscribe(Event.TOTP_LIST, self._totp_list)

    def _totp_list(self, *args, **kwargs):
        self._show_frame(self._ui.frame.totps)

    def _show_frame(self, frame:ttk.Frame):
        for f in self._ui.frame.values():
            f.hide()
        frame.show()

    def set_totps(self, otps:List):
        self._totps = totps
        self._show_frame(self._ui.frame.totps)

    def menu(self, *args, **kwargs):
        print(args, kwargs)

class PasswordFrame(ttk.Frame, GlobalEvents):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ui = NestedPropertiesDict()
        self._ui.var.password = StringVar()
        self._ui.password.label = ttk.Label(self, font=('TkDefaultFont', 20), text="Unlock")
        self._ui.password.label.pack(pady=8)
        self._ui.password.entry = ttk.Entry(self, font=('TkDefaultFont', 20), justify=tk.CENTER, show="*", width=12, textvariable=self._ui.var.password)
        self._ui.password.entry.bind('<Return>', lambda e: self.event_publish(Event.PASSWORD, self._ui.var.password.get()))
        self._ui.password.entry.pack(padx=8, pady=8)
        self._ui.password.entry.focus_set()

    def show(self):
        self.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

    def hide(self):
        self.place_forget()

class TotpsFrame(tk.Frame, GlobalEvents):
    SELECTED_BG = '#aaffaa'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ui = NestedPropertiesDict()
        self._ui.totp.frame = tk.Frame(self)
        self._ui.totp.frame.pack(fill=tk.X, expand=False)
        self._ui.totp.name.label = ttk.Label(self._ui.totp.frame, font=('TkDefaultFont', 22), text="Name")
        self._ui.totp.name.label.pack(pady=8, anchor=tk.CENTER)
        self._ui.totp.token.label = ttk.Label(self._ui.totp.frame, font=('Courier', 48, 'bold'), text="123456")
        self._ui.totp.token.label.pack(pady=4)
        self._ui.totp.progress = ttk.Progressbar(self._ui.totp.frame, maximum=100)
        self._ui.totp.progress.pack(fill=tk.X, padx=8, pady=4)
        #self._ui.totp.progress.start(interval=100)

        self._ui.list.frame = tk.Frame(self)
        self._ui.list.frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._ui.list.labels = []

        self.event_subscribe(Event.TOTP_LIST, self.set_totp_list)
        self.event_subscribe(Event.TOTP_UPDATE, self.update_totp)
        self.event_subscribe(Event.TIMER_UPDATE, self.update_timer)

    def set_totp_list(self, totps: List) -> None:
        self.totps = totps
        for l in self._ui.list.labels:
            l.destroy()
        for name in totps:
            l = ttk.Label(self._ui.list.frame, font=('TkDefaultFont', 16), cursor='hand2', text=name)
            l.bind('<Button-1>', partial(self._totp_clicked, name))
            l.pack(fill=tk.X)
            self._ui.list.labels.append(l)
        self.select_totp(first(totps))

    def select_totp(self, name: str) -> None:
        for l in self._ui.list.labels:
            l['background'] = ''
            if l['text'] == name:
                l['background'] = self.SELECTED_BG

    def update_totp(self, totp: Tuple[str, TOTP]) -> None:
        self._ui.totp.name.label['text'] = totp[0]
        self._ui.totp.token.label['text'] = totp[1]

    def update_timer(self, percent: float) -> None:
        self._ui.totp.progress['value'] = percent * 100.0

    def _totp_clicked(self, name: str, event: tk.Event) -> None:
        self.select_totp(name)
        self.event_publish(Event.TOTP_SELECTED, name)

    def show(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self) -> None:
        self.pack_forget()

if __name__ == "__main__":
    print('starting up')
    app = Application()
    app.start()

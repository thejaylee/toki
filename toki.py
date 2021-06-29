from contextlib import suppress
from functools import partial
#from enum import Enum

import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from typing import Any, Callable, Dict, List, Union

from toki.prop_helpers import NestedPropertiesDict
from toki.keyfile import CanNotDecrypt, KeyFile
from toki.ui import RootEvents
from toki.util import first

DEFAULT_KEYFILE = './.otp.keys'

class TkEvent:
    PASSWORD = '<<Password>>'
    TOTP_SELECTED = '<<Totp_Selected>>'

    class MENU:
        class FILE:
            TEST = '<<MENU_FILE_ADD_TOTP>>'
            EXIT = '<<MENU_FILE_EXIT>>'

ListTotpsFunc = Callable[[Any, str], List]
TotpFunc = Callable[[Any, str], str]

class Application:
    def __init__(self):
        self.totps = []

        self._ui = UI()
        self._ui.title(f"Toki")
        self._ui.geometry("256x384")
        self._ui.set_list_totps_func(self.read_totps_file)
        self._ui.set_totp_func(self.get_totp_secret)

    def start(self):
        self._ui.mainloop()

    def read_totps_file(self, password: str) -> List:
        keyfile = KeyFile(DEFAULT_KEYFILE, password, create_file=False)
        try:
            totps = keyfile.read_keys()
            self.totps = totps
            return totps.keys()
        except CanNotDecrypt:
            return False

    def get_totp_secret(self, name: str) -> str:
        return self.totps.get(name, None)

class UI(tk.Tk):
    class _MenuBar(tk.Menu, RootEvents):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            print('creating menus')
            filemenu = tk.Menu(self, tearoff=0)
            filemenu.add_command(label="Add TOTP", command=self.event_generate_func(TkEvent.MENU.FILE.TEST))
            filemenu.add_separator()
            filemenu.add_command(label="Exit", command=self.event_generate_func(TkEvent.MENU.FILE.EXIT))
            self.add_cascade(label="File", menu=filemenu)

        def event_generate_func(self, event_name):
            return lambda: self.root_event_generate(event_name, when='tail')

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
        self.bind(TkEvent.MENU.FILE.EXIT, lambda e: self.destroy())

    def _init_frames(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self._ui.container = container
        self._ui.frame.password = PasswordFrame(container)
        self._ui.frame.totps = TotpsFrame(container)
        self._ui.var.password = StringVar()
        #self._ui.var.password.trace('w', self._onPassword)
        self._ui.frame.password.set_password_var(self._ui.var.password)
        self._show_frame(self._ui.frame.password)

    def _init_events(self):
        self.bind(TkEvent.PASSWORD, self._on_password)
        self.bind(TkEvent.TOTP_SELECTED, self._on_totp_selected)

    def set_list_totps_func(self, func: ListTotpsFunc) -> None:
        self._func.list_totps = func

    def set_totp_func(self, func: TotpFunc) -> None:
        self._func.totp = func

    def _on_password(self, *args, **kwargs):
        if not callable(self._func.list_totps):
            return

        names = self._func.list_totps(self._ui.var.password.get())
        if names:
            self._show_frame(self._ui.frame.totps)
            self._ui.frame.totps.set_totps(names)

    def _on_totp_selected(self, *args, **kwargs):
        name = self._ui.frame.totps.get_selected_totp_name()
        print(name)

    def _show_frame(self, frame:ttk.Frame):
        for f in self._ui.frame.values():
            f.hide()
        frame.show()

    def set_totps(self, otps:List):
        self._totps = totps
        self._show_frame(self._ui.frame.totps)

    def menu(self, *args, **kwargs):
        print(args, kwargs)

class PasswordFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ui = NestedPropertiesDict()
        self._ui.password.label = ttk.Label(self, font=('TkDefaultFont', 20), text="Unlock")
        self._ui.password.label.pack(pady=8)
        self._ui.password.entry = ttk.Entry(self, font=('TkDefaultFont', 20), justify=tk.CENTER, show="*", width=12)
        self._ui.password.entry.bind('<Return>', lambda e: self.event_generate(TkEvent.PASSWORD, when='tail'))
        self._ui.password.entry.pack(padx=8, pady=8)
        self._ui.password.entry.focus_set()

    def set_password_var(self, var: tk.StringVar) -> None:
        self._ui.password.entry['textvariable'] = var

    def show(self):
        self.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

    def hide(self):
        self.place_forget()

class TotpsFrame(tk.Frame, RootEvents):
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
        self._ui.totp.progress = ttk.Progressbar(self._ui.totp.frame, maximum=300)
        self._ui.totp.progress.pack(fill=tk.X, padx=8, pady=4)
        #self._ui.totp.progress.start(interval=100)

        self._ui.list.frame = tk.Frame(self)
        self._ui.list.frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._ui.list.labels = []

    def set_totps(self, totps: List) -> None:
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

    def get_selected_totp_name(self):
        return first([w for w in self._ui.list.labels if str(w['background']) == self.SELECTED_BG])['text']

    def _totp_clicked(self, name: str, event: tk.Event) -> None:
        self.select_totp(name)
        self.event_generate(TkEvent.TOTP_SELECTED, when='tail')

    def show(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self) -> None:
        self.pack_forget()

if __name__ == "__main__":
    print('starting up')
    app = Application()
    app.start()

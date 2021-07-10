from functools import partial
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from typing import List, Tuple

from pyotp import TOTP

from toki.events import Event, GlobalEvents
from toki.prop_helpers import NestedPropertiesDict
from toki.util import first

class UI(tk.Tk):
    def __init__(self, *args, **kwargs):
        print('creating main window')
        super().__init__(*args, **kwargs)
        self.events = GlobalEvents.get_event_system()
        self._ui = NestedPropertiesDict()
        self._init_menus()
        self._init_frames()
        self._init_events()
        self._func = NestedPropertiesDict()

    def _init_menus(self):
        self._ui.menu = _MenuBar(self)
        self.config(menu=self._ui.menu)

    def _init_frames(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self._ui.container = container
        self._ui.frame.password = _PasswordFrame(container)
        self._ui.frame.add_totp = _AddTotpFrame(container)
        self._ui.frame.totps = _TotpsFrame(container)
        self.show_frame(self._ui.frame.password)

    def _init_events(self):
        self.events.subscribe(Event.TOTP_LIST, self.handle_totp_list)
        self.events.subscribe(Event.MENU_ADD_TOTP, self.handle_add_totp)
        self.events.subscribe(Event.SHOW_TOTP_FRAME, self.handle_show_totp_frame)

    def handle_totp_list(self, *args, **kwargs):
        self.show_frame(self._ui.frame.totps)

    def handle_add_totp(self, *args, **kwargs):
        self.show_frame(self._ui.frame.add_totp)

    def handle_show_totp_frame(self, *args, **kwargs):
        self.show_frame(self._ui.frame.totps)

    def show_frame(self, frame:ttk.Frame):
        for f in self._ui.frame.values():
            f.hide()
        frame.show()

    def set_totps(self, otps:List):
        self._totps = totps
        self.show_frame(self._ui.frame.totps)

class _MenuBar(tk.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('creating menus')
        self.events = GlobalEvents.get_event_system()
        self.menu = NestedPropertiesDict()
        self.menu.file = tk.Menu(self, tearoff=0)
        self.menu.file.add_command(label="Exit", command=lambda: self.events.publish(Event.MENU_EXIT))
        self.menu.totp = tk.Menu(self, tearoff=0)
        self.menu.totp.add_command(label="Add", command=lambda: self.events.publish(Event.MENU_ADD_TOTP))
        self.menu.totp.entryconfig("Add", state=tk.DISABLED)
        self.menu.totp.add_command(label="Show", command=lambda: self.events.publish(Event.MENU_SHOW_TOTP))
        self.menu.totp.entryconfig("Show", state=tk.DISABLED)
        self.menu.totp.add_command(label="Remove", command=lambda: self.events.publish(Event.MENU_REMOVE_TOTP))
        self.menu.totp.entryconfig("Remove", state=tk.DISABLED)
        self.add_cascade(label="File", menu=self.menu.file)
        self.add_cascade(label="TOTP", menu=self.menu.totp)
        self.events.subscribe(Event.TOTP_LIST, lambda e: self.menu.totp.entryconfig("Add", state=tk.NORMAL))
        self.events.subscribe(Event.TOTP_LIST, lambda e: self.menu.totp.entryconfig("Show", state=tk.NORMAL))
        self.events.subscribe(Event.TOTP_LIST, lambda e: self.menu.totp.entryconfig("Remove", state=tk.NORMAL))


class _PasswordFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = GlobalEvents.get_event_system()
        self._ui = NestedPropertiesDict()
        self._ui.var.password = StringVar()
        self._ui.password.label = ttk.Label(self, font=('TkDefaultFont', 20), text="Unlock")
        self._ui.password.label.pack(pady=8)
        self._ui.password.entry = ttk.Entry(self, font=('TkDefaultFont', 20), justify=tk.CENTER, show="*", width=12, textvariable=self._ui.var.password)
        self._ui.password.entry.bind('<Return>', lambda e: self.events.publish(Event.PASSWORD, self._ui.var.password.get()))
        self._ui.password.entry.pack(padx=8, pady=8)
        self._ui.password.entry.focus_set()

    def show(self):
        self.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

    def hide(self):
        self.place_forget()

class _TotpsFrame(tk.Frame):
    SELECTED_BG = '#aaffaa'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = GlobalEvents.get_event_system()
        self._ui = NestedPropertiesDict()
        self._ui.totp.frame = tk.Frame(self)
        self._ui.totp.frame.pack(fill=tk.X, expand=False)
        self._ui.totp.name.label = ttk.Label(self._ui.totp.frame, font=('TkDefaultFont', 22), text="None")
        self._ui.totp.name.label.pack(pady=8, anchor=tk.CENTER)
        self._ui.totp.token.label = ttk.Label(self._ui.totp.frame, font=('Courier', 48, 'bold'), cursor='hand2', text="######")
        self._ui.totp.token.label.pack(pady=4)
        self._ui.totp.token.label.bind('<Button-1>', lambda e: self.events.publish(Event.COPY_TOTP))
        self._ui.totp.progress = ttk.Progressbar(self._ui.totp.frame, maximum=100)
        self._ui.totp.progress.pack(fill=tk.X, padx=8, pady=4)

        self._ui.list.frame = tk.Frame(self)
        self._ui.list.frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._ui.list.labels = []

        self.events.subscribe(Event.TOTP_LIST, self.set_totp_list)
        self.events.subscribe(Event.TOTP_UPDATE, self.update_totp)
        self.events.subscribe(Event.TIMER_UPDATE, self.update_timer)
        self.events.subscribe(Event.MENU_REMOVE_TOTP, self.handle_menu_remove_totp)
        self.events.subscribe(Event.SHOW_TOTP, self.handle_show_totp)

    def set_totp_list(self, totps: List) -> None:
        self.totps = totps
        for l in self._ui.list.labels:
            l.destroy()
        self._ui.list.labels = []
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

    def handle_menu_remove_totp(self, *args, **kwargs) -> None:
        totp_name = first([w['text'] for w in self._ui.list.labels if str(w['background']) == self.SELECTED_BG])
        if messagebox.askyesno(title="Delete TOTP", message=f'Delete "{totp_name}", are you sure? This can not be undone!'):
            self.events.publish(Event.REMOVE_TOTP, totp_name)

    def handle_show_totp(self, totp: Tuple[str, str], *args, **kwargs) -> None:
        messagebox.showinfo(title=f"{totp[0]}", message=totp[1])

    def _totp_clicked(self, name: str, event: tk.Event) -> None:
        self.select_totp(name)
        self.events.publish(Event.TOTP_SELECTED, name)

    def show(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self) -> None:
        self.pack_forget()

class _AddTotpFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = GlobalEvents.get_event_system()
        self._ui = NestedPropertiesDict()
        self._ui.var.name = StringVar()
        self._ui.var.secret = StringVar()
        self._ui.name.label = ttk.Label(self, text="Name")
        self._ui.name.label.pack(pady=4)
        self._ui.name.entry = ttk.Entry(self, justify=tk.CENTER, textvariable=self._ui.var.name)
        self._ui.name.entry.pack(padx=8, pady=4, fill=tk.X)
        self._ui.secret.label = ttk.Label(self, text="Secret")
        self._ui.secret.label.pack(pady=4)
        self._ui.secret.entry = ttk.Entry(self, justify=tk.CENTER, textvariable=self._ui.var.secret)
        self._ui.secret.entry.pack(padx=8, pady=4, fill=tk.X)
        self._ui.add_totp.button = tk.Button(self, text="Add", command=self.do_add_totp)
        self._ui.add_totp.button.pack()
        self._ui.cancel.button = tk.Button(self, text="Cancel", command=self.cancel)
        self._ui.cancel.button.pack()

    def do_add_totp(self):
        self.events.publish(Event.ADD_TOTP, (self._ui.var.name.get(), self._ui.var.secret.get()))

    def cancel(self):
        for v in self._ui.var:
            getattr(self._ui.var, v).set('')
        self.events.publish(Event.SHOW_TOTP_FRAME)

    def show(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

    def hide(self) -> None:
        self.pack_forget()

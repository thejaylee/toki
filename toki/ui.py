from abc import ABC
import tkinter as tk
from tkinter import ttk, messagebox

class VarsFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vars = {}

    def init_var(self, name: str):
        self._vars[name] = tk.StringVar()

    def get_var(self, name: str):
        return self._vars[name] if name in self._vars else None

class RootEvents(ABC):
    def root_event_generate(self, *args, **kwargs):
        self._nametowidget('.').event_generate(*args, **kwargs)

    def root_bind(self, *args, **kwargs):
        self._nametowidget('.').bind(*args, **kwargs)

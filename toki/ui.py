import tkinter as tk
from tkinter import ttk, messagebox

from dotted_dict import DottedProperties

class VarsFrame(tk.Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._vars = {}

	def initVar(self, name: str):
		self._vars[name] = tk.StringVar()

	def getVar(self, name: str):
		return self._vars[name] if name in self._vars else None

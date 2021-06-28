import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk, messagebox
from functools import partial
from enum import Enum

from typing import Any, Callable

from lib.ui import VarsFrame

class Application:
	def __init__(self):
		self._ui = UI()
		self._ui.title(f"OTP")
		self._ui.geometry("400x500")

	def start(self):
		self._ui.mainloop()

	def doPassword(password:str):
		self._ui.setOtps()

class UI(tk.Tk):
	class _Frame(Enum):
		PASSWORD = 'password'
		OTPS = 'otps'

	class _MenuBar(tk.Menu):
		def __init__(self, *args, **kwargs):
			print('creating menus', args, kwargs)
			super().__init__(*args, **kwargs)

		def _initMenus(self, func):
			self.add_command(label="test", command=partial(args[0].menu, command=''))

	def __init__(self, *args, **kwargs):
		print('creating main window')
		super().__init__(*args, **kwargs)
		self.config(menu=__class__._MenuBar(self))
		self._initFrames()

	def _initFrames(self):
		container = tk.Frame(self)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)
		container.pack(fill=tk.BOTH, expand=1)

		self._container = container # this holds all other frames
		self._frames = {
			__class__._Frame.PASSWORD: PasswordFrame(container),
			__class__._Frame.OTPS: OtpsFrame(container)
		}
		pwFrame = self._frames[__class__._Frame.PASSWORD]
		pwFrame.getVar('password').trace('w', partial(self._onPassword, pwFrame.getVar('password')))
		self._showFrame(__class__._Frame.PASSWORD)

	def _onPassword(self, var,  *args, **kwargs):
		if var.get() == '123123':
			print('unlocked')
			self._showFrame(__class__._Frame.OTPS)

	def _showFrame(self, frame:str):
		for f in self._frames.values():
			f.pack_forget()
		self._frames[frame].grid(row=0, column=0)

	def setOtps(self, otps:list):
		self._otps = otps;
		self._showFrame(__class__._Frame.OTPS)

	def menu(self, *args, **kwargs):
		print(args, kwargs)

class PasswordFrame(VarsFrame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.initVar('password')
		self.pwLabel = ttk.Label(self, font=('TkDefaultFont', 20), text="Unlock")
		self.pwLabel.pack()
		self.pwEntry = ttk.Entry(self, font=('TkDefaultFont', 20), justify=tk.CENTER, show="*")
		#self.pwEntry.bind('<Return>', self.onSubmit)
		self.pwEntry.bind('<Return>', lambda e: self.event_generate(TkEvent.PASSWORD, when='tail'))
		self.pwEntry.pack()
		self.pwEntry.focus_set()
		self.pwEntry['textvariable'] = self.getVar('password')

	def onSubmit(self, *args, **kwargs):
		print(TkEvent.PASSWORD)
		self.event_generate(TkEvent.PASSWORD, when='tail', data=self.pwEntry)

class OtpsFrame(tk.Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.nameLabel = ttk.Label(self, font=('TkDefaultFont', 12), text="Name")
		self.nameLabel.pack()
		self.tokenLabel = ttk.Label(self, font=('TkDefaultFont', 20), text="123456")
		self.tokenLabel.pack()

if __name__ == "__main__":
	print('starting up')
	app = Application()
	app.start()

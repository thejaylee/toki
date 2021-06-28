import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk, messagebox

from typing import Optional, TypeVar
from dotted_dict import DottedDict

T = TypeVar('T')

class PropertyExistsError(Exception):
	pass

class PropertyManaged(ABC):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._property = {}

	def setProperty(self, namespace: str, value: T):
		prop = self._property
		names = namespace.split('.')
		for i, name in enumerate(names, start=1):
			if i == len(names):
				prop[name] = value
			else:
				if name not in prop:
					prop[name] = {}
				prop = prop[name]

	def getProperty(self, namespace: str):
		try:
			prop = self._property
			for name in namespace.split('.'):
				prop = prop[name]
			return prop
		except KeyError:
			return None

	def delProperty(self, namespace: str):
		try:
			prop = self._property
			names = namespace.split('.')
			for i, name in enumerate(names, start=1):
				if i == len(names):
					prop.pop(name, None)
		except KeyError:
			return None

	def property(self, namespace: str, *args, **kwargs):
		if args:
			if args[0] is None:
				self.delProperty(namespace)
			else:
				self.setProperty(namespace, args[0])
		else:
			return self.getProperty(namespace)

	def prop(self, *args, **kwargs):
		return self.property(*args, **kwargs)


class VarsFrame(tk.Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._vars = {}

	def initVar(self, name: str):
		self._vars[name] = tk.StringVar()

	def getVar(self, name: str):
		return self._vars[name] if name in self._vars else None

if __name__ == '__main__':
	class Test(PropertyManaged):
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)

	o = Test()
	o.property('this.is.a.test', 'something')
	o.property('this.is.a.foo', 'bar')
	o.property('root', 'abaga')
	print(o.prop('root'))
	print(o._property)

from abc import ABC, abstractmethod

class DottedDict(dict):
	def __setitem__(self, key, item, *args, **kwargs):
		if '.' in key[1:-1]:
			names = key.split('.')
			d = self
			for i, name in enumerate(names, start=1):
				if i == len(names):
					d.__setitem__(name, item, *args, **kwargs)
				else:
					if name not in d:
						d.__setitem__(name, DottedDict())
					d = d[name]
		else:
			super().__setitem__(key, item, *args, **kwargs)

		return item

	def __getitem__(self, key, *args, **kwargs):
		if '.' in key[1:-1]:
			names = key.split('.')
			d = self
			for i, name in enumerate(names, start=1):
				d = d.__getitem__(name, *args, **kwargs)
			return d
		else:
			return super().__getitem__(key, *args, **kwargs)

	def __delitem__(self, key, *args, **kwargs):
		if '.' in key[1:-1]:
			names = key.split('.')
			d = self
			for i, name in enumerate(names, start=1):
				if i == len(names):
					del d[name]
				else:
					d = d[name]
		else:
			return super().__delitem__(key, *args, **kwargs)

	def get(self, key, *args, **kwargs):
		if '.' in key[1:-1]:
			names = key.split('.')
			d = self
			for i, name in enumerate(names, start=1):
				d = d.get(name, *args, **kwargs)
			return d
		else:
			return super().__getitem__(key, *args, **kwargs)

class DottedProperties(ABC):
	def __init__(self, *args, **kwargs):
		self._ddict = DottedDict()
		super().__init__(*args, **kwargs)

	def property(self, namespace: str, *args, **kwargs):
		if args:
			if args[0] is None:
				del self._ddict[namespace]
			else:
				self._ddict[namespace] = args[0]
		else:
			return self._ddict[namespace]

	def prop(self, *args, **kwargs):
		return self.property(*args, **kwargs)

from abc import ABC, abstractmethod

class DottedDict(dict):
    def __init__(self, overwriteExisting = False, createOnAccess = False):
        self.overwriteExisting = overwriteExisting
        self.createOnAccess = createOnAccess

    def __setitem__(self, key, item, *args, **kwargs):
        if '.' in key[1:-1]:
            names = key.split('.')
            d = self
            for i, name in enumerate(names, start=1):
                if i == len(names):
                    d.__setitem__(name, item, *args, **kwargs)
                else:
                    if name not in d or (not isinstance(d[name], __class__) and self.overwriteExisting):
                        d.__setitem__(name, DottedDict(self.overwriteExisting, self.createOnAccess))
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

    def __missing__(self, key):
        if self.createOnAccess:
            self[key] = DottedDict(self.overwriteExisting, self.createOnAccess)
            return self[key]
        else:
            return super().__missing__(key)

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

class AbstractDottedProperties(ABC):
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

    def _p(self, *args, **kwargs):
        return self.property(*args, **kwargs)

# these nested prop classes work, but will leave dangling properties: __delattr__ will cause __getattr__
class NestedProperties:
    def __setattr__(self, name, value):
        #print('setattr:', self, name, value)
        return super().__setattr__(name, value)

    def __getattribute__(self, name):
        #print('getattribute:', name)
        return super().__getattribute__(name)

    def __getattr__(self, name):
        #print('getattr:', name)
        prop = NestedProperties()
        setattr(self, name, prop)
        return prop

    def __delattr__(self, name):
        #print('delattr', name)
        super().__delattr__(name)

# same API as NestedProperties but uses a DottedDict internally
class NestedPropertiesDict:
    def __init__(self):
        self._dict = {}

    def __getattr__(self, name):
        #print('getattr', type(self), name)
        if name not in self._dict:
            self._dict[name] = NestedPropertiesDict()
        return self._dict[name]

    def __setattr__(self, name, value):
        #print('__setattr__', name, value)
        if name == '_dict':
            super().__setattr__(name, value)
        else:
            self._dict[name] = value

    def __iter__(self):
        return iter(self._dict)

    def items(self, *args, **kwargs):
        return self._dict.items(*args, **kwargs)

    def values(self, *args, **kwargs):
        return self._dict.values(*args, **kwargs)

if __name__ == '__main__':
    #d = DottedDict(overwriteExisting = True, createOnAccess = True)
    #d['a.b.c.d'] = 'foo'
    #print(d)
    #d['a']['b']['c']['d'] = 'bar'
    #print(d)
    #d['x.y'] = 'asdf'
    #d['x.y.z'] = 'qwerty'
    #print(d)
    #d['yoo.hoo']
    #print(d)
    #d['yoo.hoo'] = 'boo'
    #print(d)

    p = NestedPropertiesDict()
    p.a.b.c = 'asdf'
    print(p.a.b.c)
    print(p.a.b._dict)

from functools import wraps

class Deco:
    funcs = []

    @classmethod
    def deco_arg(cls, name):
        def decorator(func):
            print(f'deocrating {func} with {name}')
            cls.funcs.append(func)
            return func
        return decorator

    @classmethod
    def call_funcs(cls):
        for f in cls.funcs:
            f()

class C:
    @Deco.deco_arg('test')
    def foo(self):
        print('foo', self)

c = C()
c.foo()
Deco.call_funcs()

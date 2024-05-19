from typing import Any

def constant_hash(func): 
    return ConstantHash(func)

class ConstantHash:
    def __init__(self, f, id = None):
        self.f = f
        if not id:
            id = f.__name__
        self.id = id

    def __call__(self, *args, **kwargs):
        return self.f(*args, **kwargs)

    def __reduce__(self) -> str | tuple[Any, ...]:
        return (self.__class__, (self.id,))

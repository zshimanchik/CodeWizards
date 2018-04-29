
def cached_property(func):
    @property
    def wrapper(self):
        storage = self.__dict__.setdefault('__cached_properties', dict())
        if func.__name__ not in storage:
            storage[func.__name__] = func(self)
        return storage[func.__name__]
    return wrapper


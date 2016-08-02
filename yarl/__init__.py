__version__ = '0.0.1'


# Why not furl?
# Because I pretty sure URL class should be immutable
# but furl is a mutable class.


class URL:
    # don't derive from str
    # follow pathlib.Path design
    # probably URL will not suffer from pathlib problems:
    # it's intended for libraries like aiohttp,
    # not to be passed into standard library functions like os.open etc.
    def __init__(self, val):
        self._val = val

    def __str__(self):
        return self._val

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, str(self))

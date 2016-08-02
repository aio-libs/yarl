__version__ = '0.0.1'

from multidict import MultiDict, MultiDictProxy
from urllib.parse import urlsplit, urlunsplit, parse_qsl


# Why not furl?
# Because I pretty sure URL class should be immutable
# but furl is a mutable class.


DEFAULT_PORTS = {
    'http': 80,
    'https': 443,
    'ws': 80,
    'wss': 443,
}


class URL:
    # don't derive from str
    # follow pathlib.Path design
    # probably URL will not suffer from pathlib problems:
    # it's intended for libraries like aiohttp,
    # not to be passed into standard library functions like os.open etc.
    def __init__(self, val):
        self._val = urlsplit(val)
        self._query = None

    def __str__(self):
        return urlunsplit(self._val)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, str(self))

    @property
    def host(self):
        # Use host instead of hostname for sake of shortness
        # May add .hostname prop later
        return self._val.hostname

    @property
    def port(self):
        return self._val.port or DEFAULT_PORTS.get(self._val.scheme)

    @property
    def scheme(self):
        return self._val.scheme

    @property
    def path(self):
        return self._val.path or '/'

    @property
    def user(self):
        # not .username
        return self._val.username

    @property
    def password(self):
        return self._val.password

    @property
    def query(self):
        if self._query is None:
            self._query = MultiDict(parse_qsl(self._val.query))
        return MultiDictProxy(self._query)

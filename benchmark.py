import timeit


cython_setup = """\
from yarl.quoting import _Quoter as Quoter
from yarl.quoting import _Unquoter as Unquoter
"""

python_setup = """\
from yarl.quoting import _PyQuoter as Quoter
from yarl.quoting import _PyUnquoter as Unquoter
"""


print("Cython quote ascii: {:.3f} sec".format(
    timeit.timeit("q(s)",
                  cython_setup+"s='/path/to';q=Quoter(safe='/')")))


print("Python quote ascii: {:.3f} sec".format(
    timeit.timeit("q(s)",
                  python_setup+"s='/path/to';q=Quoter(safe='/')")))


print("Cython quote PCT: {:.3f} sec".format(
    timeit.timeit("q(s)",
                  cython_setup+"s='abc%0a';q=Quoter()")))


print("Python quote PCT: {:.3f} sec".format(
    timeit.timeit("q(s)",
                  python_setup+"s='abc%0a';q=Quoter()")))


print("Cython quote: {:.3f} sec".format(
    timeit.timeit("q(s)",
                  cython_setup+"s='/путь/файл';q=Quoter()")))


print("Python quote: {:.3f} sec".format(
    timeit.timeit("q(s)",
                  python_setup+"s='/путь/файл';q=Quoter()")))


print("Cython unquote: {:.3f} sec".format(
    timeit.timeit("u(s)",
                  cython_setup+"s='/path/to';u=Unquoter()")))


print("Python unquote: {:.3f} sec".format(
    timeit.timeit("u(s)",
                  python_setup+"s='/path/to';u=Unquoter()")))

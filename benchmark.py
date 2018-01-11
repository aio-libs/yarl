import timeit


cython_setup = """\
from yarl.quoting import _quote as quote
from yarl.quoting import _unquote as unquote
"""

python_setup = """\
from yarl.quoting import _py_quote as quote
from yarl.quoting import _py_unquote as unquote
"""


print("Cython quote ascii: {:.3f} sec".format(
    timeit.timeit("quote(s, safe='/')", cython_setup+"s='/path/to'")))


print("Python quote ascii: {:.3f} sec".format(
    timeit.timeit("quote(s, safe='/')", python_setup+"s='/path/to'")))


print("Cython quote PCT: {:.3f} sec".format(
    timeit.timeit("quote(s)", cython_setup+"s='abc%0a'")))


print("Python quote PCT: {:.3f} sec".format(
    timeit.timeit("quote(s)", python_setup+"s='abc%0a'")))


print("Cython quote: {:.3f} sec".format(
    timeit.timeit("quote(s)", cython_setup+"s='/путь/файл'")))


print("Python quote: {:.3f} sec".format(
    timeit.timeit("quote(s)", python_setup+"s='/путь/файл'")))


print("Cython unquote: {:.3f} sec".format(
    timeit.timeit("unquote(s)", cython_setup+"s='/path/to'")))


print("Python unquote: {:.3f} sec".format(
    timeit.timeit("unquote(s)", python_setup+"s='/path/to'")))

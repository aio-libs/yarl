import timeit

from yarl import URL

print(
    "Build URL with host and path: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://localhost:1234/req')", globals={"URL": URL}, number=100000
        )
    )
)

print(
    "Build URL with IP Address and path: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://127.0.0.1:1234/req')", globals={"URL": URL}, number=100000
        )
    )
)

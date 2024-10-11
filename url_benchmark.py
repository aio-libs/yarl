import timeit

from yarl import URL

print(
    "Build URL with host and path and port: {:.3f} sec".format(
        timeit.timeit(
            "URL.build(host='localhost', path='/req', port=1234)",
            globals={"URL": URL},
            number=100000,
        )
    )
)

print(
    "Build URL with host: {:.3f} sec".format(
        timeit.timeit(
            "URL.build(host='localhost')", globals={"URL": URL}, number=100000
        )
    )
)

print(
    "Build URL with host and port: {:.3f} sec".format(
        timeit.timeit(
            "URL.build(host='localhost', port=1234)",
            globals={"URL": URL},
            number=100000,
        )
    )
)

print(
    "Make URL with host and path and port: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://localhost:1234/req')", globals={"URL": URL}, number=100000
        )
    )
)

print(
    "Make URL with host and path: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://localhost/req')", globals={"URL": URL}, number=100000
        )
    )
)


print(
    "Make URL with IPv4 Address and path and port: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://127.0.0.1:1234/req')", globals={"URL": URL}, number=100000
        )
    )
)


print(
    "Make URL with IPv4 Address and path: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://127.0.0.1/req')", globals={"URL": URL}, number=100000
        )
    )
)


print(
    "Make URL with IPv6 Address and path and port: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://[::1]:1234/req')", globals={"URL": URL}, number=100000
        )
    )
)


print(
    "Make URL with IPv6 Address and path: {:.3f} sec".format(
        timeit.timeit("URL('http://[::1]/req')", globals={"URL": URL}, number=100000)
    )
)

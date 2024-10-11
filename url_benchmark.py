import timeit

from yarl import URL

MANY_HOSTS = [f"localhost.{i}" for i in range(10000)]
MANY_URLS = [f"https://localhost.{i}" for i in range(10000)]

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
    "Build encoded URL with host and path and port: {:.3f} sec".format(
        timeit.timeit(
            "URL.build(host='localhost', path='/req', port=1234, encoded=True)",
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
    "Build URL with different hosts: {:.3f} sec".format(
        timeit.timeit(
            "for host in hosts: URL.build(host=host)",
            globals={"URL": URL, "hosts": MANY_HOSTS},
            number=10,
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
    "Make encoded URL with host and path and port: {:.3f} sec".format(
        timeit.timeit(
            "URL('http://localhost:1234/req', encoded=True)",
            globals={"URL": URL},
            number=100000,
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
    "Make URL with many hosts: {:.3f} sec".format(
        timeit.timeit(
            "for url in urls: URL(url)",
            globals={"URL": URL, "urls": MANY_URLS},
            number=10,
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

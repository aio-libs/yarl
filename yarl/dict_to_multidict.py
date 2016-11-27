from collections import Sequence

from multidict import MultiDict


def dict_to_multidict(data):
    """Convert dict into multidict."""
    data_tuples = []
    for key, value in data.items():
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                data_tuples.append((key, item))
        else:
            data_tuples.append((key, value))
    return MultiDict(data_tuples)

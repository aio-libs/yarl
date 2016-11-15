import pytest
from yarl.dict_to_multidict import dict_to_multidict


@pytest.fixture
def dict_data():
    return {
        'string': 'some text',
        'integer': 42,
        'list': [1, 2, 3, 4],
        'tuple': (1, 2, 3, 4),
    }


def test_dict_to_multidict(dict_data):
    result = dict_to_multidict(dict_data)
    expected_data = [('string', 'some text'), ('integer', 42), ('list', 1),
                     ('list', 2), ('list', 3), ('list', 4), ('tuple', 1),
                     ('tuple', 2), ('tuple', 3), ('tuple', 4)]
    assert sorted(result.items()) == sorted(expected_data)

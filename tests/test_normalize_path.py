from yarl import URL

np = URL._normalize_path


def test_no_dots():
    assert np('path/to') == 'path/to'


def test_skip_dots():
    assert np('path/./to') == 'path/to'


def test_dot_at_end():
    assert np('path/to/.') == 'path/to/'


def test_double_dots():
    assert np('path/../to') == 'to'


def test_extra_double_dots():
    assert np('path/../../to') == 'to'

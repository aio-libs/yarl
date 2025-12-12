import pytest
from pydantic import BaseModel, ValidationError

from yarl import URL


class TstModel(BaseModel):
    url: URL


def test_dump() -> None:
    url = URL("https://example.com")
    m = TstModel(url=url)
    dct = m.model_dump()
    assert dct == {"url": str(url)}
    assert isinstance(dct["url"], str)


def test_validate_valid() -> None:
    url = URL("https://example.com")
    dct = {"url": str(url)}
    m = TstModel.model_validate(dct)
    assert m == TstModel(url=url)
    assert isinstance(m.url, URL)


def test_validate_invalid() -> None:
    dct = {"url": 123}
    with pytest.raises(ValidationError, match="url"):
        TstModel.model_validate(dct)


def test_get_schema() -> None:
    schema = TstModel.model_json_schema()
    assert schema == {
        "properties": {"url": {"format": "uri", "title": "Url", "type": "string"}},
        "required": ["url"],
        "title": "TstModel",
        "type": "object",
    }

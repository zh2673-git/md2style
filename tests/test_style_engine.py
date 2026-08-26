import pytest
from md2style.engines import StyleEngine
from md2style.core.errors import StyleValidationError


def test_resolve_default():
    se = StyleEngine("styles")
    s = se.resolve("", {})
    assert s["headings"]["h1"]["size"] == 22  # 兜底


def test_resolve_yaml_override():
    se = StyleEngine("styles")
    s = se.resolve("paper", {})
    assert s["headings"]["h1"]["font"] == "黑体"


def test_cli_override_wins():
    se = StyleEngine("styles")
    s = se.resolve("paper", {"headings": {"h1": {"color": "#FF0000"}}})
    assert s["headings"]["h1"]["color"] == "#FF0000"


def test_validate_bad_color():
    se = StyleEngine("styles")
    with pytest.raises(StyleValidationError):
        se.validate({"headings": {"h1": {"color": "red"}}})


def test_validate_bad_size():
    se = StyleEngine("styles")
    with pytest.raises(StyleValidationError):
        se.validate({"headings": {"h1": {"size": 200}}})

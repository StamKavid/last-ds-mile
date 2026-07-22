import pytest
from helpers import parse_frontmatter


def test_parse_frontmatter_well_formed(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("---\nname: foo\ndescription: bar\n---\nBody text here.\n", encoding="utf-8")
    frontmatter, body = parse_frontmatter(path)
    assert frontmatter == {"name": "foo", "description": "bar"}
    assert body == "Body text here.\n"


def test_parse_frontmatter_crlf(tmp_path):
    path = tmp_path / "test.md"
    path.write_bytes(b"---\r\nname: foo\r\n---\r\nBody.\r\n")
    frontmatter, body = parse_frontmatter(path)
    assert frontmatter == {"name": "foo"}


def test_parse_frontmatter_no_trailing_newline_after_close(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("---\nname: foo\n---", encoding="utf-8")
    with pytest.raises(AssertionError):
        parse_frontmatter(path)


def test_parse_frontmatter_missing_frontmatter(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("Just plain text, no frontmatter.\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        parse_frontmatter(path)

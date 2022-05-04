from html.parser import HTMLParser
from pathlib import Path
import pytest

import big5web as _


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        (b"", ""),
        (b"hello world!", "hello world!"),
        (b"hello \xa5\x40\xac\xc9!", "hello 世界!"),
    ],
)
def test_big5web_decode_good(encoded: bytes, expected: str):
    assert encoded.decode("big5web") == expected


@pytest.mark.parametrize(
    ("encoded", "error", "instead"),
    [
        (b"aaa\x81", "incomplete multibyte sequence", "aaa"),
        (b"aaa\x80", "invalid start byte", "aaa"),
        (b"aaa\x80bbb", "invalid start byte", "aaabbb"),
        (b"aaa\xffbbb", "invalid start byte", "aaabbb"),
        (b"aaa\x81\xffbbb", "illegal multibyte sequence", "aaabbb"),
        (b"aaa\x81bbb", "illegal multibyte sequence", "aaabbb"),
    ],
)
def test_big5web_decode_error(encoded: bytes, error: str, instead: str):
    with pytest.raises(UnicodeDecodeError, match=error):
        encoded.decode("big5web")
    assert encoded.decode("big5web", "ignore") == instead


class WptDecodeTestParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_span = False
        self.span_attrs = None
        self.span_data = None
        self.data: list[tuple[str, bytes, str]] = []

    def _parse_attrs(self, attrs):
        # <span data-cp="25B" data-bytes="C8 F7">
        codepoint = None
        undecoded = None
        for attr, value in attrs:
            if attr == "data-cp":
                codepoint = chr(int(value, 16))
            elif attr == "data-bytes":
                undecoded = bytes.fromhex(value)
        assert codepoint is not None
        assert undecoded is not None
        return codepoint, undecoded

    def handle_starttag(self, tag, attrs):
        if tag == "span":
            assert not self.in_span, "wpt test file is not as expected"
            self.in_span = True
            self.span_attrs = self._parse_attrs(attrs)
            self.span_data = []

    def handle_endtag(self, tag):
        if self.in_span:
            assert tag == "span", "wpt test file is not as expected"
            assert self.span_data is not None
            assert self.span_attrs is not None
            decoded = "".join(self.span_data)
            codepoint, undecoded = self.span_attrs
            self.data.append((codepoint, undecoded, decoded))
            self.in_span = False
            self.span_data = None
            self.span_attrs = None

    def handle_data(self, data):
        if self.in_span:
            assert self.span_data is not None
            self.span_data.append(data)


def test_WptDecodeTestParser():
    """Test that the test parser is actually parsing as expected"""
    parser = WptDecodeTestParser()
    parser.feed("<body></body>")
    assert len(parser.data) == 0

    parser = WptDecodeTestParser()
    parser.feed(
        """
    <span data-cp="25B" data-bytes="C8 F7">\u025b</span>
    """
    )
    assert len(parser.data) == 1
    assert parser.data[0] == ("\u025b", b"\xC8\xF7", "\u025b")

    parser = WptDecodeTestParser()
    parser.feed(
        """
    <!doctype html>
    <html>
        <head><meta charset="big5"><title>big5 characters</title></head>
        <body>
            <span data-cp="A7" data-bytes="A1 B1">\u00a7</span>
            <span data-cp="A8" data-bytes="C6 D8">\u00a8</span>
            <span data-cp="AF" data-bytes="A1 C2">\u00af</span>
            <span data-cp="B0" data-bytes="A2 58">\u00b0</span>
            <span data-cp="B1" data-bytes="A1 D3">\u00b1</span>
            <span data-cp="B7" data-bytes="A1 50">\u00b7</span>
            <span data-cp="D7" data-bytes="A1 D1">\u00d7</span>
            <span data-cp="F7" data-bytes="A1 D2">\u00f7</span>
            <span data-cp="F8" data-bytes="C8 FB">\u00f8</span>
            <span data-cp="14B" data-bytes="C8 FC">\u014b</span>
            <span data-cp="153" data-bytes="C8 FA">\u0153</span>
            <span data-cp="250" data-bytes="C8 F6">\u0250</span>
            <span data-cp="254" data-bytes="C8 F8">\u0254</span>
            <span data-cp="25B" data-bytes="C8 F7">\u025b</span>
            <span data-cp="26A" data-bytes="C8 FE">\u026a</span>
            <span data-cp="275" data-bytes="C8 F9">\u0275</span>
            <span data-cp="283" data-bytes="C8 F5">\u0283</span>
            <span data-cp="28A" data-bytes="C8 FD">\u028a</span>
        </body>
    </html>
    """
    )
    assert len(parser.data) == 18
    assert parser.data[0] == ("\u00a7", b"\xA1\xB1", "\u00a7")
    assert parser.data[17] == ("\u028a", b"\xC8\xFD", "\u028a")


class TestWptDecode:
    """Tests based on web-platform-tests"""

    def test_wpt_decode_stream(self, wpt_path: Path):
        """Test that the IO can use the decoder"""
        wpt_path.read_text("big5web")

    def test_wpt_decode_file(self, wpt_decoded: str):
        """Test that the resource is decoded with no errors"""
        pass

    def test_wpt_parse(self, wpt_decoded: str):
        """Test that the resource can be parsed as HTML"""

        parser = WptDecodeTestParser()
        parser.feed(wpt_decoded)
        assert len(parser.data) > 0

        for codepoint, undecoded, decoded in parser.data:
            assert codepoint == decoded
            assert undecoded.decode("big5web") == decoded

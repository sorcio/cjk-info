# pyright: strict
import codecs
from io import StringIO
from pathlib import Path

ENCODING = "big5web"

DOUBLE_CHAR_TABLE = {
    1133: "\u00CA\u0304",  # Ê̄ (LATIN CAPITAL LETTER E WITH CIRCUMFLEX AND MACRON)
    1135: "\u00CA\u030C",  # Ê̌ (LATIN CAPITAL LETTER E WITH CIRCUMFLEX AND CARON)
    1164: "\u00EA\u0304",  # ê̄ (LATIN SMALL LETTER E WITH CIRCUMFLEX AND MACRON)
    1166: "\u00EA\u030C",  # ê̌ (LATIN SMALL LETTER E WITH CIRCUMFLEX AND CARON)
}


def load_big5_index() -> dict[int, str]:
    # https://encoding.spec.whatwg.org/index-big5.txt
    index: dict[int, str] = {}
    index_path = Path(__file__).parent / "index-big5.txt"
    with open(index_path, "rt") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) >= 2:
                big5_s, cp_s, *_ = parts
                big5 = int(big5_s)
                cp = int(cp_s, 16)
                index[big5] = chr(cp)
    return index


BIG5_INDEX = load_big5_index()


def decode(input: bytes, errors: str = "strict"):
    # print("big5web decode", bytes(input), errors)
    error_handler = codecs.lookup_error(errors)
    outfile = StringIO()
    write = outfile.write
    pos = 0
    length = len(input)

    def getbyte():
        nonlocal pos
        if pos < length:
            b = input[pos]
            # print("consumed:", hex(b), chr(b), pos)
            pos = pos + 1
            return b
        else:
            return None

    def error(reason: str = ""):
        nonlocal pos
        exc = UnicodeDecodeError(ENCODING, input, pos - 1, pos, reason)
        # print(exc)
        replacement, newpos = error_handler(exc)
        if isinstance(replacement, bytes):
            replacement = replacement.decode("ascii")
        # print(f"replacing input[{pos}] with {replacement!r}")
        # print(f"skipping to {newpos}")
        write(replacement)
        pos = newpos

    # breakpoint()
    big5_lead = 0x00
    while True:
        b = getbyte()
        if b is None:
            if big5_lead != 0x00:
                big5_lead = 0x00
                error("incomplete multibyte sequence")
            else:
                # finished
                break
        else:
            if big5_lead != 0x00:
                lead = big5_lead
                pointer = None
                big5_lead = 0x00
                offset = 0x40 if b < 0x7F else 0x62
                # If byte is in the range 0x40 to 0x7E, inclusive, or 0xA1 to 0xFE,
                # inclusive, set pointer to (lead − 0x81) × 157 + (byte − offset).
                if (0x40 <= b <= 0x7E) or (0xA1 <= b <= 0xFE):
                    pointer = (lead - 0x81) * 157 + (b - offset)
                try:
                    result = DOUBLE_CHAR_TABLE[pointer]  # type: ignore
                except KeyError:
                    pass
                else:
                    write(result)
                    del result
                    continue
                if pointer is not None:
                    code_point = BIG5_INDEX.get(pointer)
                else:
                    code_point = None
                if code_point:
                    write(code_point)
                    del code_point
                    continue
                error("illegal multibyte sequence")
                if b < 0x80:
                    # > If byte is an ASCII byte, prepend byte to ioQueue.
                    # This means to "unread" the byte:
                    pos -= 1
            elif b < 0x80:
                # If byte is an ASCII byte, return a code point whose value is byte.
                write(chr(b))
            elif 0x81 <= b <= 0xFE:
                big5_lead = b
            else:
                error("invalid start byte")
    return (outfile.getvalue(), pos)


def encode(input: str, errors: str = "strict"):
    assert False


# XXX: BufferedIncrementalDecoder is undocumented, but it's convenient, so is it ok to
# use here?
class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, input: bytes, errors: str, final: bool):
        return decode(input, errors)


def getregentry():
    return codecs.CodecInfo(
        name=ENCODING,
        encode=encode,
        decode=decode,
        incrementaldecoder=IncrementalDecoder,
    )


def search_function(name: str):
    if name == ENCODING:
        return getregentry()


codecs.register(search_function)

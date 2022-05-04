import json
from pathlib import Path

from genmap_support import *


def load_unicode_mappings(search_field: str):
    # https://www.unicode.org/reports/tr38/
    #
    # The grouping of fields into categories, and of their data into files, is based on
    # both principled and practical considerations, and it changes over time. For
    # mechanical parsing of Unihan data, it should not be assumed that the data for a
    # particular property is in a particular file. One approach to parsing data for
    # certain properties is to concatenate all of the Unihan*.txt files together (or act
    # as if they were) and extract the desired properties from the whole (for example,
    # using “grep”). This avoids the need to track which file has a given property
    # across Unicode versions, and therefore avoids the need to adjust parsing code.
    #
    # Each file uses the same structure. Blank lines may be ignored. Lines beginning
    # with # are comment lines used to provide the header and footer. Each of the
    # remaining lines is one entry, with three, tab-separated fields: the Unicode Scalar
    # Value, the database field name, and the value for the database field for the given
    # Unicode Scalar Value. For most of the fields, if multiple values are possible, the
    # values are separated by spaces. No character may have more than one instance of a
    # given field associated with it, and no empty fields are included in any of the
    # files archived inside Unihan.zip.
    #
    # There is no formal limit on the lengths of any of the field values. Any Unicode
    # characters may be used in the field values except for double quotes and control
    # characters (especially tab, newline, and carriage return). Most fields have a more
    # restricted syntax, such as the kKangXi field which consists of multiple,
    # space-separated entries, with each entry consisting of four digits 0 through 9,
    # followed by a period, followed by three more digits.
    #
    # The data lines are sorted by Unicode Scalar Value and field-type as primary and
    # secondary keys, respectively.
    root = Path("Unihan")
    files = [*root.glob("*.txt")]
    table: dict[int, str] = {}
    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line[0] == "#":
                    continue
                u_scalar, field, value = line.split("\t")
                if field == search_field:
                    scalar = int(u_scalar.removeprefix("U+"), 16)
                    if scalar in table:
                        print("Warning: duplicated entry for", u_scalar)
                    table[scalar] = value
    return table

def bh2s(code):
    return ((code >> 8) - 0x87) * (0xfe - 0x40 + 1) + ((code & 0xff) - 0x40)


def load_hkscs_map(table: dict[int, int]):
    decmap = {}
    encmap_bmp, encmap_nonbmp = {}, {}
    isbmpmap = {}
    for scalar, hkscs in table.items():
        decmap.setdefault(hkscs >> 8, {})
        if scalar > 0xffff:
            encmap = encmap_nonbmp
            isbmpmap[bh2s(hkscs)] = 1
            scalar &= 0xffff
        else:
            encmap = encmap_bmp
        decmap[hkscs >> 8][hkscs & 0xff] = scalar
        encmap.setdefault(scalar >> 8, {})
        encmap[scalar >> 8][scalar & 0xff] = hkscs

    return decmap, encmap_bmp, encmap_nonbmp, isbmpmap


def old_loadhkscsmap(fo):
    import re
    print("Loading from", fo)
    fo.seek(0, 0)
    decmap = {}
    encmap_bmp, encmap_nonbmp = {}, {}
    isbmpmap = {}
    lineparse = re.compile(
        r'^([0-9A-F]{4})\s*([0-9A-F]{4})\s*([0-9A-F]{4})\s*(2?[0-9A-F]{4})$')
    for line in fo:
        data = lineparse.findall(line)
        if not data:
            continue
        hkscs, u1993, ubmp, u2001 = [int(x, 16) for x in data[0]]
        decmap.setdefault(hkscs >> 8, {})
        if u2001 > 0xffff:
            encmap = encmap_nonbmp
            isbmpmap[bh2s(hkscs)] = 1
            u2001 &= 0xffff
        else:
            encmap = encmap_bmp
        decmap[hkscs >> 8][hkscs & 0xff] = u2001
        encmap.setdefault(u2001 >> 8, {})
        encmap[u2001 >> 8][u2001 & 0xff] = hkscs

    return decmap, encmap_bmp, encmap_nonbmp, isbmpmap


# https://www.ogcio.gov.hk/tc/our_work/business/tech_promotion/ccli/hkscs/doc/HKSCS2016.json
def load_ccli_json():
    with open("HKSCS2016.json", "rb") as f:
        data = json.load(f)
    # JSON document is a list of objects like:
    #   {
    #     'codepoint': '00A8',
    #     'char': '¨',
    #     'hkscs-ver': 1999,
    #     'cangjie': '',
    #     'cantonese': '',
    #     'H-Source': 'H-C6D8'
    #   }
    # When H-Source is H-xxxx, xxxx is the Big5 mapping.
    table = {
        int(entry["codepoint"], 16): int(entry["H-Source"][2:], 16)
        for entry in data
        if entry["H-Source"].startswith("H-")
    }
    return table

def main_hkscs():
    # raw_table = load_unicode_mappings("kHKSCS")
    # table = {scalar: int(value, 16) for scalar, value in raw_table.items()}
    c1_lower, c1_upper = BIG5HKSCS_C1 = (0x87, 0xfe)
    c2_lower, c2_upper = BIG5HKSCS_C2 = (0x40, 0xfe)
    table = load_ccli_json()
    assert all(c1_lower <= (c >> 8) <= c1_upper for c in table.values())
    assert all(c2_lower <= (c & 0xff) <= c2_upper for c in table.values())
    hkscsdecmap, hkscsencmap_bmp, hkscsencmap_nonbmp, isbmpmap = load_hkscs_map(table)
    with open('mappings_hk.h', 'w') as fp:
        print("Generating BIG5HKSCS decode map...")
        writer = DecodeMapWriter(fp, "big5hkscs", hkscsdecmap)
        writer.update_decode_map(BIG5HKSCS_C1, BIG5HKSCS_C2)
        writer.generate()

        print("Generating BIG5HKSCS decode map Unicode plane hints...")
        filler = BufferedFiller()
        def fillhints(hintfrom, hintto):
            fp.write(f"static const unsigned char big5hkscs_phint_{hintfrom}[] = {{\n")
            for msbcode in range(hintfrom, hintto+1, 8):
                v = 0
                for c in range(msbcode, msbcode+8):
                    v |= isbmpmap.get(c, 0) << (c - msbcode)
                filler.write('%d,' % v)
            filler.printout(fp)
            fp.write("};\n\n")
        fillhints(bh2s(0x8740), bh2s(0xa0fe))
        fillhints(bh2s(0xc6a1), bh2s(0xc8fe))
        fillhints(bh2s(0xf9d6), bh2s(0xfefe))

        print("Generating BIG5HKSCS encode map (BMP)...")
        writer = EncodeMapWriter(fp, "big5hkscs_bmp", hkscsencmap_bmp)
        writer.generate()

        print("Generating BIG5HKSCS encode map (non-BMP)...")
        writer = EncodeMapWriter(fp, "big5hkscs_nonbmp", hkscsencmap_nonbmp)
        writer.generate()


if __name__ == "__main__":
    main_hkscs()
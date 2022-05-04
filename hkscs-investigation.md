
# What is the canonical source of HKSCS Big-5 encodings?

Notes from my investigation.

## Background

### Big-5 character encoding

In 1984, the Institute for Information Industry of Taiwan specified **Big-5**
([Wikipedia](https://en.wikipedia.org/wiki/Big5)) as a Chinese character encoding method
for Traditional Chinese characters.

It is now considered legacy, but when it was released it quickly become popular and
de-facto standard in Taiwan, Hong Kong, and Macau, and later on was adopted officially
as a government standard in Taiwan. Therefore it gained widespread software support,
which still persists in some form.

Big-5 defines a [double-byte character set (DBCS)](https://en.wikipedia.org/wiki/DBCS)
which originally included more than 13000 characters. Usually Big-5 text is mixed with a
single-byte character set (technically unspecified; Python, and presumably most users,
use ASCII).

Sidenote: [CNS 11643](https://en.wikipedia.org/wiki/CNS_11643) is the Taiwan official
standard that incorporated Big-5. It's still an active standard (last update was in
2021), and I suppose it has users. But I don't understand its adoption, and how much of
it has become part of Unicode. Notably, its inclusion in Python [was
rejected](https://github.com/python/cpython/issues/46342). It's not going to be a part
of this investigation.

### Hong Kong Supplementary Character Set (HKSCS)

Big-5 was extended by the Hong Kong government to include additional characters. The
extension was formalized in 1999 in the **[HKSCS]** specification, adding 4,702 characters
that were not in the original Big-5 character set.

[HKSCS]: <https://en.wikipedia.org/wiki/Hong_Kong_Supplementary_Character_Set>

The extended encoding is sometimes called Big5-HKSCS. It's not the only extension to
Big-5 (but it's the only one I've researched until now, and as far as I know the only
one to have a Python implementation).

The standard was revised through the years:

| Revision     | # chars | Publish date |
| ------------ | ------: | -----------: |
| [HKSCS-1999] |   4,702 |      09/1999 |
| [HKSCS-2001] |   4,818 |      12/2001 |
| [HKSCS-2004] |   4,941 |      05/2005 |
| [HKSCS-2008] |   5,009 |      12/2009 |
| [HKSCS-2016] |   5,033 |      05/2017 |


(Source for specs is https://www.ccli.gov.hk/)

[HKSCS-2016]: https://www.ccli.gov.hk/doc/e_hkscs_2016.pdf
[HKSCS-2008]: https://www.ccli.gov.hk/doc/e_hkscs_2008.pdf
[HKSCS-2004]: https://www.ccli.gov.hk/doc/e_hkscs_2004.pdf
[HKSCS-2001]: https://www.ccli.gov.hk/doc/e_hkscs_2001.pdf
[HKSCS-1999]: https://www.ccli.gov.hk/doc/e_hkscs_1999.pdf

HKSCS is not strictly tied to Big-5. In fact, for each version of the specification, all
characters defined in HKSCS have allocations for ISO 10646 and Unicode.

Before HKSCS-1999, a 1995 standard called GCCS existed which is largely a predecessor to
HKSCS. It was exclusively meant to be encoded as Big-5 double-byte characters, but it's
not fully compatible with the newer standard. It never got support in Python.

### Relationship with Unicode

Uhh ok this is more confusing to me, which is also the reason why I had to investigate
this. Bear with me, and feel free to suggest corrections.

First of all, the byte encoding defined by Big-5 is considered legacy. Basically all new
software uses Unicode. But the characters added by Big-5 and its extensions (including
HKSCS) are an important part of Unicode.

Big-5 predates both ISO 10646 and Unicode by a few years. Additionally, when Unicode was
first formalized (Unicode 1.0.0, October 1991) it had no Han characters.

In occasion of the merger of the ISO 10646 and Unicode standards in June 1992, the
Unicode Consortium published an intermediate version, [Unicode 1.0.1]. This version was
the first one to include the U+4E00..U+9FFF block (now called [CJK Unified Ideographs]),
which included 20,902 characters.

[Unicode 1.0.1]: https://www.unicode.org/versions/Unicode1.0.0/Notice.pdf
[CJK Unified Ideographs]: <https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)>

This block was the first result of an effort known as [Han unification] to have a single
character set that can represent characters from Chinese, Japanese, Korean (CJK). The
[Ideographic Research Group] (IRG), established at the time, is responsible for
maintaining the [set of unified Han characters] in ISO 10646 and Unicode. IRG
coordinates with national bodies, which brings us to the relevant bit of this history.

[Han unification]: https://unicode.org/versions/Unicode4.0.0/appA.pdf
[Ideographic Research Group]: https://en.wikipedia.org/wiki/Ideographic_Research_Group
[set of unified Han characters]: https://en.wikipedia.org/wiki/CJK_Unified_Ideographs

When HKSCS was first specified in 1999, the Hong Kong government had been cooperating
with ISO. As a result, the character set had a well-defined mapping to Unicode since its
inception. The full set of characters introduced by HKSCS-1999 was included in Unicode
3.1. The administration was deeply invested in an international standard. By 2008, HKSCS
required that only characters approved by ISO would be added; HKSCS 2016 recommended
that all users "upgrade their systems" to use Unicode.

While this sounds peachy, standards are complicated (or, at least, they are to me), and
there are a few details that make software support of these standards a bit painful.
More about that later.

### Python support

Python has two codecs for Big5-encoded text:

* `big5`: Big-5 support
* `big5hkscs`: Big-5 support with HKSCS

Both were originally provided as part of the [CJK Codecs] package maintained by Hye-Shik Chang
(2003-2004). Version 1.1 was included in Python 2.4 (commit [2bb146f2f4]).

[CJK Codecs]: https://github.com/BackupTheBerlios/cjkpython
[2bb146f2f4]: https://github.com/python/cpython/commit/2bb146f2f4fd52b03cfa7ae739adb35d2b9f5421

I've haven't been able yet to determine which version of HKSCS was used in the original
merge. It would require a tiny bit of reverse engineering. Presumably it was the latest
available at the time, HKSCS 2001. From the commit history, we can determine that it has
since been updated only once to HKSCS 2004 in Python 2.6 (commit [01612e7dec], SVN
r60671, merge [77c02ebf38]).

[01612e7dec]: https://github.com/python/cpython/commit/01612e7dec9fcbd0733137aa90f0f21cfa49299f
[77c02ebf38]: https://github.com/python/cpython/commit/77c02ebf3821c381883c9bc2675bafddbe0fff09

The codecs are implemented in C and have been maintained through the years to work with
later Python versions. The mappings themeselves were not updated after that time. One of
the limitations was probably that the scripts that translate the mapping files into a C
header were not added to the Python repo when CJK Codecs was merged.

More recently (Apr 2020), [Dong-hee Na] undertook the effort to port the scripts to
modern Python ([gh-84508]) and added them to the repo. With one notable exception: the ones that
generate the mappings for Big-5 based codecs.

[Dong-hee Na]: https://github.com/corona10
[gh-84508]: https://github.com/python/cpython/issues/84508

## Why care about Big-5 codecs in Python in 2022?

That's a great question and I'm not sure anyone actually cares. I, for one, was
blissfully unaware of anything around this matter for the longest time. And I can
probably forget about all this with little consequence.

I happened upon this because I was looking at [`html.parser`], the HTML parser included
in Python standard library. While this is an effective (and *fast*, for a pure Python
implementtion) parser that can take most HTML you throw at it, it's not compliant with
the [HTML 5 specification for parsing] in a few subtle ways.

[`html.parser`]: https://docs.python.org/3/library/html.parser.html
[HTML 5 specification for parsing]: https://html.spec.whatwg.org/multipage/parsing.html

One of the idiosincracies is that it completely forgoes the part about character
encodings and it just assumes that the input stream is text. By constrast, [html5lib]
works according to standard and accepts a byte stream as input (in addition to
already-decoded text). html5lib relies on [webencodings] for its codecs support, which
in turn relies on codecs built into Python.

[html5lib]: https://github.com/html5lib/html5lib-python
[webencodings]: https://github.com/gsnedders/python-webencodings

When it comes to legacy CJK encodings, this turns out to be slightly wrong for two
related reasons:

* The labels used by WHATWG are [not the same codec names] used internally by Python,
  and this causes some mismatch. In our case, note that the [Big-5 charset defined by
  WHATWG] explicitly includes HKSCS, but it's mapped to Python `big5` instead of
  `big5hkscs`.
* Even when switching to `big5hkscs`, the official [web-platform-tests] conformance suite
  for legacy encodings still has some cases that are not decoded correctly.

[not the same codec names]: https://github.com/gsnedders/python-webencodings/issues/26
[Big-5 charset defined by WHATWG]: https://encoding.spec.whatwg.org/#index-big5
[web-platform-tests]: https://github.com/web-platform-tests/wpt/tree/master/encoding/legacy-mb-tchinese/big5

Ironically, html5lib includes some of the [failing cases] from the conformance suite, but
only for performance testing, so it does not perform any validation. It's possible that
nobody noticed the mismatch, because Big-5 is so rarely used these days (and I guess its
users are not new to the occasional encoding mishap).

[failing cases]: https://github.com/html5lib/html5lib-python/blob/master/benchmarks/data/wpt/weighted/big5_chars_extra.html

That is, until I tried to use the same benchmarks for `html.parser`. Since I need to
decode text before feeding it into the parser state, I found the hard way that Python
cannot handle some of the test data. My web browser had no problem with the same file,
so I suspected the problem might be with Python. Indeed:

```python
>>> bytes([0x87, 0xDA]).decode('big5hkscs')
Traceback (most recent call last):
  ...
UnicodeDecodeError: 'big5hkscs' codec can't decode byte 0x87 in position 0: illegal multibyte sequence

```

Since support for Big-5 is required by WHATWG, and Python has the codecs built in, I
decided that it might be worth to have a compliant implementation. What I did not know
is what "compliant" meant.

## Updating `big5hkscs`

The first thing I tried to do was to rebuild the mappings for the `big5hkscs` codec.

There are a few files:

* `Modules/cjkcodecs/_codecs_hk.c`: the codec logic itself
* `Modules/cjkcodecs/mappings_tw.h`: the mapping data used by the big5 codec
* `Modules/cjkcodecs/mappings_hk.h`: more mapping data for big5hkscs
* `Lib/encodings/big5hkscs.py`: registers the codec, mostly uninteresting

The .c file is kinda straightforward (once you get used to the heavy macro usage). What
is a bit concerning is that it uses some magic numbers and hard-coded definitions that
seem to depend on the standard version. I decided to be bold and hope for the best and
fix things later if needed.

The .h files are not made to be read by humans. It's a data file that contains the
mapping tables from HKSCS codes to Unicode codepoints and vice versa. The format is not
obvious to me, but it's clearly made for the machine to use. The macros in the codec
file refer to these tables.

There are a few tools in `Tools/unicode` that generate files of this kind, but the one
for `mappings_tw.h` and `mappings_hk.h` is missing. It existed in the original CJK
Codecs package, a copy of which is on GitHub, as [`genmap_tchinese.py`]. This script is
not modern Python and was not ported together with the others. So maybe it was a good
occasion to do it (thanks Enrico for the initial help!) and close [gh-84508].

[`genmap_tchinese.py`]: https://github.com/BackupTheBerlios/cjkpython/blob/master/cjkcodecs/tools/genmap_tchinese.py

### Finding the data files

Modernizing the script is not hard, thanks to the work [Dong-hee Na] had already done on
the other files. But in order to run it, one would need the source data.

The source of Big5-HKSCS to Unicode mappings used to live at this URL:

http://www.info.gov.hk/digital21/eng/hkscs/download/big5-iso.txt

Unfortunately the file is not available anymore. It's probably not that big a deal,
because it was data for an older version of the standard. But at the beginning I
couldn't find an updated version either.

What I gathered from the code is that this file used to have tabular data in four columns
which the script calls: *hkscs*, *u1993*, *ubmp*, *u2001*. Each column is made of four
hexadecimal digits, with the exception of *u2001* which could have five digits if it
started with two. So that number was undoubtedly the Unicode 3.1 codepoint (2001 comes
from the revision of the ISO/IEC 10646-2:2001 standard). *hkscs* with some luck refers
to the two-byte Big-5 representation of the character. The other two columns were
unused but probably were the Unicode 1.0.1 codepoint (ISO/IEC 10646-1:1993) and uh
something about the Basic Multilingual Plane?

At this time I was missing most of the background that I acquired later, but it occurred
to be that Unicode might be a source to the data I needed. Indeed, the [Unihan] database
(part of the Unicode standard) includes a field called *kHKSCS* which has a very
promising definition:

>  	Mappings to the Big Five extended code points used for the Hong Kong Supplementary
>  	Character Set-2008 (HKSCS-2008).

[Unihan]: https://www.unicode.org/reports/tr38/

So I set to see what I can do with this.

## Unihan

The Unihan database is made of easy to parse TSV files. I included a
[unihan.py](./unihan.py) script which parses the database, and provides a simple CLI for
querying it, just for the sake of learning. Any actual application would probably need
to translate the data in a better suited form.

Each entry in the database defines a property for one character in the set of CJK
unified ideographs. Properties have a field name, and a value for that character. So

```
U+352E<TAB>kDefinition<TAB>a kind of animal which looks like a rat
```

tells us that the character U+352E (&#x352E;) has a *kDefinition* of "a kind of animal
which looks like a rat". Cute!

The *kHKSCS* field is defined for many characters and its value is a sequence of 4 hex
digits, corresponding to the 2 bytes of the Big-5 encoding:

```
U+3440<TAB>kHKSCS<TAB>96DF
U+344A<TAB>kHKSCS<TAB>8CF4
U+344C<TAB>kHKSCS<TAB>89D5
```

Just as a basic check, there must be at least one example which works with the current
Python codec:

```python
>>> "\u3440" == bytes.fromhex("96DF").decode("big5hkscs")
True

```

So far, so good. Does this cover the whole set of HKSCS characters?

```shell
$ python unihan.py -f kHKSCS | wc -l
    4579
```

*Ouch*. No! We are expecting 5,009 characters from HKSCS-2008 (the ones added in the
2016 version have no Big-5 encoding). I could imagine that a few special cases might
needs to be hardcoded or something. I still hadn't figured all the pieces of the puzzle.
But with almost five hundred missing, the idea that something was wrong was more than a
suspicion.

This is the point where I will lose most genuinely interested readers, because instead
of being disciplined and reading the standards, or asking an expert, or reading the code
more patiently, I decided to rebuild the `mappings_hk.h` file with just this data and
see what would happen.

I don't have the outcome anymore, but the decode table was a lot smaller, which was a
sign that I lost some information. I took some test data from web-platform-tests and
found a failing case very quickly. The same case worked with the old codec:

```python
>>> "\u31C0" == bytes.fromhex("8840").decode("big5hkscs")
True

```

So, the sequence 8840 must be decoded as U+31C0 (&#x31C0;). This is where I learned
something new that I should have learned a lot earlier.

Unihan is an amazing database *for unified CJK characters*. It's the result of Han
unification. It's not a collection of all signs used in East Asian languages or anything
like that. U+31C0 is not part of Unihan, because it's not an "unified ideograph".

```python
>>> >>> unicodedata.name("\u31C0")
'CJK STROKE T'

```

U+31C0 belongs to the [CJK Strokes] block (U+31C0..U+31EF), which was added in [Unicode
4.1]. The block only contains 36 assigned characters

[CJK Strokes]: https://en.wikipedia.org/wiki/CJK_Strokes_(Unicode_block)
[Unicode 4.1]: https://www.unicode.org/versions/Unicode4.1.0/

The characters in HKSCS are not only only CJK unified ideographs. After the fact, it
seems obvious that a charset might want to encode more than ideographs, e.g. symbols of
various nature, or the strokes that I had just encountered.

Since Unihan does not cover these cases, I needed to look for a database that does.

## Intermezzo: web encodings for Big5

The reasonable thing to do at this point would be to find an official source for HKSCS.
I did not do the reasonable thing. I couldn't find the source, but I found something
that looked authoritative enough, and I decided to take a look at it.

As mentioned before, the [Encoding Standard] from WHATWG defines a Big5 encoding that
explicitly includes HKSCS characters. The standard specifies how an encoder and decoder
should map Big5-encoded text to and from Unicode text.

[Encoding Standard]: https://encoding.spec.whatwg.org/#encodings

This looked promising, but it turned out to be inadequate for a few reasons:

- The "Big5" encoding by WHATWG uses a mapping that "matches the Big5 standard in
  combination with the Hong Kong Supplementary Character Set and other common
  extensions". It *includes* HKSCS as well as other extensions. So the character set
  is larger than the one targeted by `big5hkscs`.

- Even if we wanted to use the extended character set, there is no 1-1 mapping, because
  a single Unicode code point can correspond to more than one Big5 sequence, each from a
  different source (Big5 or any of the extensions). E.g. the Unicode codepoint U+5EF4
  (&#x5EF4;) is mapped to two different Big5 sequences: `fbfd` (from HKSCS-1999), and
  `c6cf` (from Big5-Plus).

  - This repository includes a Python script to [show all duplicates] from the WHATWG
    mappings. It just loads the WHATWG data and shows the matching Big5 sequences. It
    does not show any other information, and in particular it does not show where a
    given Big5 sequence comes from.

  - [HarJIT] compiled some very useful and very comprehensive [charts with Big5
    characters from various extensions] that I used to track down the codes. The amount
    of work behind this looks incredible, especially given the scarcity of sources
    accessible to English speakers, so a big thanks to them.

  - It's unclear to me which sources WHATWG decided to include in their Big5 definition
    and why. I tracked some of the public history in [appendix B] to these notes.

  - Note that the opposite is not true: one Big5 sequence is mapped to exactly one
    Unicode codepoint.

- As a consequence to the above, there is no way to build a general encoder from Unicode
  to Big5, because there is no unique mapping. The encoder defined by the web platform
  Encoding Standard solves this problem by excluding part of the mappings at encoding
  time. Specifically, a note says:

  > Avoid returning Hong Kong Supplementary Character Set extensions literally.




[HarJIT]: https://github.com/harjitmoe
[show all duplicates]: ./whatwg-duplicates.py
[charts with Big5 characters from various extensions]: https://harjit.moe/cns-conc.html
[appendix B]: <#appendix-b-whatwg-merging-of-big5-variants>

There are encoders but no actual encoding API; only hacking A element:
https://github.com/web-platform-tests/wpt/blob/master/encoding/big5-encoder.html


<!--
  HKSCS leads:

  [*range(0x87, 0xa0 + 1), *range(0xc6, 0xc8 + 1), *range(0xf9, 0xfe + 1)]

  87..a0
  c6..c8
  f9..fe
 -->

## Using HKSCS-2016 data from CCLI

Entry for codepoint 270F0 in HKSCS-2016 json file provided by in HK government (CCLI):

```json
{"codepoint":"270F0","char":"䕫","hkscs-ver":1999,"cangjie":"TYUE","cantonese":"kwai4","H-Source":"H-8FA8"}
```
> [Source](https://www.ogcio.gov.hk/tc/our_work/business/tech_promotion/ccli/hkscs/doc/HKSCS2016.json)

```python
>>> import json
>>> entry = json.loads("""{"codepoint":"270F0","char":"䕫","hkscs-ver":1999,"cangjie":"TYUE","cantonese":"kwai4","H-Source":"H-8FA8"}""")

```

But codepoint and char are mismatched:

```python
>>> entry["char"]
'䕫'
>>> ord(entry["char"]) == 0x2f9b2 != 0x270f0
True

```

Also, 2F9B2 is actually normalized into yet another codepoint:

```python
>>> import unicodedata

>>> unicodedata.decomposition("\U0002f9b2")
'456B'
>>> unicodedata.normalize("NFC", "\U0002f9b2")
'䕫'
>>> unicodedata.normalize("NFC", "\U0002f9b2") == "\u456B"
True

```

What else do we know about these characters?

```python

>>> unicodedata.name("\U000270f0")
'CJK UNIFIED IDEOGRAPH-270F0'
>>> unicodedata.name("\U0002f9b2")
'CJK COMPATIBILITY IDEOGRAPH-2F9B2'
>>> unicodedata.name("\u456b")
'CJK UNIFIED IDEOGRAPH-456B'


>>> def isnorm(c, forms=("NFC", "NFD", "NFKC", "NFKD")):
...    if isinstance(c, int):
...        c = chr(c)
...    return {form: unicodedata.is_normalized(form, c) for form in forms}

>>> isnorm(0x270f0)
{'NFC': True, 'NFD': True, 'NFKC': True, 'NFKD': True}
>>> isnorm(0x2f9b2)
{'NFC': False, 'NFD': False, 'NFKC': False, 'NFKD': False}
>>> isnorm(0x456b)
{'NFC': True, 'NFD': True, 'NFKC': True, 'NFKD': True}

```

We learn that 2F9B2 is a "compatibility" character. It belongs to block [CJK
Compatibility Ideographs
Supplement](https://en.wikipedia.org/wiki/CJK_Compatibility_Ideographs_Supplement)
(U+2F800..U+2FA1F).

This block was introduced in Unicode 3.1 (in 2001):

> ### CJK Compatibility Ideographs Supplement: U+2F800-U+2FA1D
> This block consists of additional compatibility ideographs required for round-trip
> compatibility with CNS 11643-1992, planes 3, 4, 5, 6, 7, and 15. They should not be
> used for any other purpose and, in particular, may not be used in Ideographic
> Description Sequences.
>
> The names for the compatibility ideographs are also algorithmic. Thus, the name for
> the compatibility ideograph U+2F800 is CJK COMPATIBILITY IDEOGRAPH-2F800.

(https://www.unicode.org/reports/tr27/tr27-4.html)

This matches what we found before:

```python
>>> unicodedata.name("\U0002f9b2")
'CJK COMPATIBILITY IDEOGRAPH-2F9B2'

```

In turn, the block supplements the pre-existing "CJK compatibility ideographs"
(U+F900..U+FA2D) with the same purpose (Unicode 1.0.1, 1992).

So, why was 2F9B2 in the HKSCS-2016 database provided CCLI? And why was it in the
entry for the different codepoint 270F0? I'm not sure but:
1) The standard docs for HKSCS don't mention 270F0:
   - HKSCS-2016 https://www.ccli.gov.hk/doc/e_hkscs_2016.pdf
   - HKSCS-2008 https://www.ccli.gov.hk/doc/e_hkscs_2008.pdf
   - HKSCS-2004 https://www.ccli.gov.hk/doc/e_hkscs_2004.pdf
   - HKSCS-2001 https://www.ccli.gov.hk/doc/e_hkscs_2001.pdf
2) 27070 belongs to "CJK Ideograph Extension B":
   https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_Extension_B

   This is a block for "rare and historic CJK ideographs for Chinese, Japanese,
   Korean, and Vietnamese". It has "has dozens of variation sequences defined for
   standardized variants". It also has "thousands of ideographic variation sequences
   registered in the Unicode Ideographic Variation Database (IVD). These sequences
   specify the desired glyph variant for a given Unicode character."


> The CLIAC approved the mapping amendment of the HKSCS character "character H-8FA8"
> (H-8FA8) from the CJK Compatibility Ideographs Supplement code point 2F9B2 to the CJK
> Unified Ideographs Extension B code point 270F0 at its 25th meeting held on 11 January
> 2018.

https://www.ccli.gov.hk/en/hkscs/what_is_hkscs.html
https://ccjktype.fonts.adobe.com/2017/09/houston-u2f9b2.html
https://appsrv.cse.cuhk.edu.hk/~irg/irg/irg49/IRGN2268-%20HKSARG%20Re-mapping.pdf


### ...random notes (WIP)...

> Unihan (UAX #38) >> Ideally, there would be no pairs of z-variants in the Unicode
> Standard; however, the need to provide for round-trip compatibility with earlier
> standards, and some out-and-out mistakes along the way, mean that there are some.
> These are marked using the kZVariant field.


> 456B https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_Extension_A


## Appendix A: are CJK strokes "unified characters"?

This is completely irrelevant, but at some point I got curious about why U+31C0 was not
included in the unified Han repertoire. Of course the argument that this is not an
ideograph (nor a logograph, which appears to be the more correct term of the broader
category, because only some Han characters are ideographs) makes some sense:

> Characters in the CJK Strokes block are single-stroke components of CJK ideographs.
> The first characters assigned to this block were 16 HKSCS-2001 PUA characters that had
> been excluded from CJK Unified Ideograph Extension B on the grounds that *they were
> not true ideographs*. CJK strokes are used with highly specific semantics (primarily
> to index ideographs), but *they lack the monosyllabic pronunciations and logographic
> functions typically associated with independent ideographs*. The encoded characters in
> this block are single strokes of well-defined types; these constitute the basic
> elements of all CJK ideographs. Any traditionally defined stroke type attested in the
> representative forms appearing in the Unicode CJK ideograph code charts or attested in
> pre-unification source glyphs is a candidate for future inclusion in this block.

Although the CJK strokes block was added in Unicode 4.1, this description of the CJK
Strokes was first seen in the [Unicode 5.0 core specs] (emphasis mine). This confirms
that some characters defined in other sources (like the HKSCS case that we are
considering) received a different treatment according to their categorirzation, and that
not all CJK characters are subject to the unification process.

[Unicode 5.0 core specs]: https://www.unicode.org/versions/Unicode5.0.0/ch12.pdf

The first point of confusion comes when you learn that some of the characters in [CJK
Strokes] have an *[Equivalent_Unified_Ideograph]* property in Unicode Data, but not all.
The property "maps most CJK radicals and CJK strokes to the most reasonably equivalent
CJK unified ideograph". This is the case for example of U+31CF (&#x31CF;) whose
"equivalent ideograph" is U+4E40 (&#x4E40;). On the other hand, U+31C0 does not have an
equivalent ideograph (at least in the current standard).

[Equivalent_Unified_Ideograph]: https://www.unicode.org/reports/tr44/#Equivalent_Unified_Ideograph

It seems that this property was [proposed at a later
point](https://www.unicode.org/review/pri344/) and
[approved](https://www.unicode.org/L2/L2017/17103.htm#151-C20) for addition in Unicode
11 (June 2018). This revises the previous paragraph to add:

> […] on the grounds that they were not true ideographs. Further additions consist of
> traditionally defined stroke types attested in the representative forms appearing in
> the Unicode CJK ideograph code charts or occurring in pre-unification source glyphs.
> See the Equivalent_Unified_Ideograph property in the Unicode Character Database for
> mappings of most CJK strokes to equivalent CJK unified ideographs. […]

I don't have the background to understand this. I imagine that the "representative
forms" we are talking about here have their own standing as true ideographs (or
logographs). U+4E40 for example is listed as one of the possible variants of [Kangxi
radical] 4 while U+31C0 is only a "basic stroke" and not a radical. I cannot say if
explanation makes any sense.

[Kangxi radical]: https://en.wikipedia.org/wiki/Kangxi_radical

Both strokes and radicals can be used as building blocks of an Ideographic Description
Sequence (IDS), which I understand as a language that can be used to compose ideographs
from basic components. So, for example U+5803 (&#x5803;) can be described with the IDS
sequence U+2ff1 U+2ff0 U+65b9 U+65b9 U+571f (&#x2ff1;&#x2ff0;&#x65b9;&#x65b9;&#x571f;),
where the first two characters are [Ideographic Description Characters].

[Ideographic Description Characters]: https://en.wikipedia.org/wiki/Ideographic_Description_Characters_(Unicode_block)

Interestingly, before Unicode 8.0 (2015) the chapter on IDS did not allow CJK Strokes to
be part of IDS. Digging through the drafts and the commentary, I found that the
inclusion of CJK Strokes as an ideographic description component received some
resistance from Japan. The given reasons included: visual confusion between CJK Strokes
and the equivalent unified ideographs; excess of detail; and something that might or
might not be related to my initial question:

> The characters on CJK STROKES are originated from the stroke symbols on HKSCS. It
> should be carefully considered whether these HKSCS unique stroke symbols are
> appropriate to be used as DC.

Is the origin in HKSCS in itself reason for skepticism? I thought that CJK Strokes were
meant to be of general use. Could this resistance be part of the reason the strokes from
HKSCS were not considered part of the unified set? In any case, the committee rejected
the ballot and commented that some characters can only be described if strokes are
allowed (which was the original rationale for inclusion). To the other points:

> The argument that allowing CJK strokes will introduce ambiguous sequences as some
> strokes are visually the same as some encoded characters is not convincing as already
> *all Kangxi radicals and most CJK radicals supplement characters are visual clones of
> unified ideographs*, and so a process dealing with IDS sequences already needs to deal
> with visual ambiguity.

Interesting! So I imagine that ambiguity is not in itself a reason for exclusion. The
comment goes on suggesting that the strokes are only used sparingly in IDS. And then:

> Finally, despite their names, and because of their generic shapes, these strokes have
> use cases beyond the CJK domain. For example, for Tangut IDS sequences which require
> dot or slanted strokes

Is this an argument for CJK Strokes deserving their own place outside of CJK Unified
Ideographs? It would make sense, i.e. Tangut script is not unified. If this is meant to
address the skepticism about their source in HKSCS (but I'm not sure that's the case)
I would read it to mean that the strokes are in fact more universal than mere regional
usage.

For the record, a few months later Japan national standard body proposed again that the
standard be amended by not allowing CJK strokes. This time no mention of the HKSCS
source was made. The disposistion was again a rejection, reiterating similar reasons.


### WIP (random notes after this point)

https://www.unicode.org/L2/L2015/15125-n4664-pdam2-doc.pdf

https://www.unicode.org/L2/L2015/15263-n4435-disp-cmt-amd2.pdf

&#x2FF1;&#x4E95;&#x86D9;

&#x2FF0;&#x6C35;&#x2FF1;&#x2FF0;&#x4FDD;&#x53BD;&#x571F;


GB/T 16500-1998
GB16500-95

Original name in N2808 (June 17): CJK UNIFIED BASIC STROKE T

Name in N2808R (June 21): CJK BASIC STROKE T

Approved name (https://www.unicode.org/L2/L2005/05058-wg2-consent.txt): CJK STROKE T

Meeting minutes https://www.unicode.org/wg2/docs/n2753.pdf

Mr. Yasuhiro Anan: If we take a decision on a new block, the name Unified may not be appropriate.

Dr. Ken Whistler: CJK Basic Strokes – would be a better name.


## Appendix B: WHATWG merging of Big5 variants

It's unclear to me which sources WHATWG decided to include in their Big5 definition. I
don't know the history and I haven't done much digging. I suspect they might have just
built upon the status quo of what web browsers from different vendors supported at the
time. Some of this history seems to be documented in a March/April 2012 thread from the
WHATWG public mailing list with subject [Encoding: big5 and big5-hkscs].

[Encoding: big5 and big5-hkscs]: https://lists.w3.org/Archives/Public/public-whatwg-archive/2012Mar/0259.html
https://lists.w3.org/Archives/Public/public-whatwg-archive/2012Apr/0082.html
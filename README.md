cjk-info
========

This repository includes some information and tools that I collected while looking into
support for old CJK codecs (especially Traditional Chinese) in modern Python.

Some of these might be useful for the public, some are included just for fun.

## HKSCS data files

Check the [hk_data](./hk_data/README.md) directory for a copy of the official data files
from the Government of Hong Kong which document HKSCS-2016 and HKSCS-2008, including
Big5-HKSCS mappings.

## Big5 web codec for Python

A very simple (and slow) implementation of a codec compatible with Big5 as defined by
WHATWG, which is not 100% compatible with either `big5` or `big5hkscs` as included in
Python.

Usage:

```python
import big5web  # need to import before the codec is available

decoded_text = big5_encoded_bytes.decode("big5web")
```

Encoding is not supported (yet). The main purpose is to demonstrate the differences
between various Big-5 codecs and the part of the space they support.

## Unihan lookup tool

A very simple tool to lookup code point properties in the Unihan database. Mostly useful
to get familiar with the content of the databse.

Lookup specific code point:

```shell
$ python unihan.py -c U+456b  
U+456B kHanYu = 53331.130
U+456B kIRGHanyuDaZidian = 53331.130
U+456B kIRGKangXi = 1067.220
U+456B kMeyerWempe = 1384a
U+456B kCangjie = TCHE
U+456B kIRG_GSource = GKX-1067.22
U+456B kIRG_JSource = JA-264E
U+456B kIRG_TSource = T7-5468
U+456B kRSUnicode = 140.16
U+456B kTotalStrokes = 22
U+456B kCantonese = kwai4
U+456B kDefinition = (corrupted form of U+5914 夔) a one-legged monster; a walrus, name of a court musician in the reign of Emperor Shun (2255 B.C.)
U+456B kMandarin = kuí
```

Lookup specific properties:

```shell
$ python unihan.py -f kDefinition
U+3400 kDefinition = (same as U+4E18 丘) hillock or mound
U+3401 kDefinition = to lick; to taste, a mat, bamboo bark
U+3402 kDefinition = (J) non-standard form of U+559C 喜, to like, love, enjoy; a joyful thing
...
U+30EDE kDefinition = biangbiang noodles
U+31076 kDefinition = swing
U+31317 kDefinition = steam
```

Options can be combined in any number:

```shell
$ python unihan.py -c U+456b U+3400 -f kDefinition kTotalStrokes
U+3400 kTotalStrokes = 5
U+456B kTotalStrokes = 22
U+3400 kDefinition = (same as U+4E18 丘) hillock or mound
U+456B kDefinition = (corrupted form of U+5914 夔) a one-legged monster; a walrus, name of a court musician in the reign of Emperor Shun (2255 B.C.)
```

First time, it can be useful to download the Unihan database in the current directory:

```shell
$ python unihan.py -c U+456b --download-database 
...
```

## My experience with finding the correct sources

The [story behind this repo](hkscs-investigation.md) and the many mistakes I made while
trying to find out how to rebuild the mappings for Big5-HKSCS in Python.

(Currently WIP)

## Other tools

(Currently WIP)

# License

Files from external sources have their own copyright and licensing terms. Everything
else is available with the MIT License as specified in the [LICENSE](LICENSE) file.

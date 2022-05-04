Data files from HKSARG
======================

This directory collects data files provided by the *Hong Kong Special Administrative
Region Government* (*HKSARG*).

The [Hong Kong Supplementary Character Set] (HKSCS) is published by the HKSARG. At the
time of writing, the latest version is HKSCS-2016, and three amendements were decided
since.

[Hong Kong Supplementary Character Set]: https://www.ccli.gov.hk/en/hkscs/what_is_hkscs.html

Since I found that most links on the web are outdated, and the data is not always easy
to find, I decided to publish a copy of the data in this repository. Please read
carefully the [notes about distributing](#can-i-use-these-files) this files.

HKSCS-2016
----------

The [HKSCS-2016 Document](e_hkscs_2016.pdf) ([Terms of Use](terms01.md)) is a PDF which
describes the latest published version of HKSCS.

Since the publication date (May 2017) some amendments were made which are not included
in the PDF:

<details>
<summary>Amendments to HKSCS-2016</summary>

1) Character H-8FA8 changed code point from U+2F9B2 to U+270F0 "&#x270F0;" (January 11,
   2018)
   - U+270F0 has been part of Unicode block *CJK Unified Ideographs Extension B* since
      Unicode 3.1 (2001).
   - The change to H-8FA8 was reflected in Unicode 11.0 (June 5, 2018) and ISO/IEC
      10646:2017/Amd 1:2019 (January 2019).

2) Character HD-5C83 (U+5C83 "&#x5C83;") was included (January 14, 2019)
   - U+5C83 was already part of the original set of *CJK Unified Ideographs*.
   - The addition of HD-5C83 was reflected in Unicode 12.0 (March 5, 2019) and ISO/IEC
      10646:2017/Amd 2:2019 (June 2019).

3) Character HD-2D25D (U+2D25D "&#x2D25D;") was included (February 3, 2021)
   - U+2D25D was already in Unicode 3.1 (see above).
   - The addition of HD-2D25D was first reflected in Unicode 14.0 (September 14,
      2021) and it's still not reflected in ISO 10646.

4) Character HD-2BB37 (U+2BB37 "&#x2BB37;") was included (February 3, 2021)
   - Same as 3.

5) The glyph for character H-8ACB (U+22ACF "&#x22ACF;") was changed (February 3, 2021)
   - This is a reference glyph change. No character mappings were changed.
   - The change is still not reflected in Unicode nor ISO 10646.
</details>

The [HKSCS related information (JSON format)](HKSCS2016.json) ([Terms of Use]()) file is a machine-readable
version of the same information included in the standard. It's not the authoritative
source, but it can be used as a dataset for mappings. It's updated more often than the
PDF, and it already reflects the amendments.


HKSCS-2008
----------

The mapping tables for HKSCS versions prior to 2016 proved to be a bit harder to find
through search engines, but they are still provided by the HKSARG through the CCLI
website. I collected them for convenience.

The license for the files is more restrictive, so they are provided in this repository
for as long as legally permitted (see [notes](#can-i-use-these-files) below).

The 2008 tables are still useful for compatibility with Unicode documents encoded with
characters from the Private Use Area. The newest versions of the standard don't map
characters in the PUA, and HKSCS-2016 does not document the old mappings anymore.

It's also the latest version that explicitly maps to the Big-5 space. This is generally
not an issue because H-xxxx codes correspond to the Big-5 mapping, but this is not
officially documented anymore.


Sources
-------

### CCLI

The [*Common Chinese Language Interface*](https://www.ccli.gov.hk/en/index/) (CCLI)
website makes information available for public reference.

The source of this information is the [*Chinese Language Interface Advisory
Committee*](https://www.ogcio.gov.hk/en/our_work/business/tech_promotion/ccli/cliac/)
(CLIAC). 

The CLIAC operates within the Office of the Government Chief Information Officer (OGCIO)
of the HKSARG.

### DATA.GOV.HK

[DATA.GOV.HK](https://data.gov.hk/en/) is a website and API that provides access to
open source data from various sources within the HKSARG.

In the case of data mentioned in this document, the source is the Office of the
Government Chief Information Officer (OGCIO).

The system implements a [CKAN](https://ckan.org/) API.

Can I use these files? 
----------------------

The files are protected by copyright and licensed by the Government of the Hong Kong
Special Administrative Region (HKSARG). For each of the files, license terms apply and
restrict what can be done with the documents.

They are distributed in this repository under the understanding that, at the time of
publication, this is allowed. Read the licensing terms for each file carefully, and look
for updated versions on the website.

In particular, in the case of files with a "CCLI" source, the terms allows it as long as
the original terms of use are attached, and the files are made available in unmodified
form, and not for financial gain; but the same terms contain a problematic clause:

> By using the Software and Document, you irrevocably agree that the HKSARG may from
> time to time vary this Terms of Use without further notice to you and you also
> irrevocably agree to be bound by the most updated version of the Terms of Use. 

I'm not a lawyer, but I would recommend against including files with a "CCLI" source as
part of any software distribution, including of free and open source software. The
license is not free in that sense that it restricts allowed use in a way that I believe
is incompatible with FOSS licenses. And the above-mentioned clause looks like a
dealbreaker to me.

This also applies to this repository, which might need to be updated to remove the files
if licensing terms change.

### List of files and sources

Here is a complete list of the files and their attached Terms of Use:

<!-- THIS LIST IS GENERATED AUTOMATICALLY
     Run download.py to update it -->

1) [ISO/IEC 10646-1:1993 compatibility table](1993cmp_2008.txt) ([Terms of
   Use](terms_1993cmp_2008.md))

   Source: `https://www.ccli.gov.hk/doc/1993cmp_2008.txt` (CCLI)

2) [Hong Kong Supplementary Character Set-2016 (HKSCS-2016)
   Document](e_hkscs_2016.pdf) ([Terms of Use](terms01.md))

   Source: `https://www.ccli.gov.hk/doc/e_hkscs_2016.pdf` (CCLI)

3) [Mapping Table](hkscs-2008-big5-iso.txt) ([Terms of
   Use](terms_hkscs2008_big5_iso.md))

   Source: `https://www.ccli.gov.hk/doc/hkscs-2008-big5-iso.txt` (CCLI)

4) [ISO/IEC 10646-1:2000 compatibility table](2000cmp_2008.txt) ([Terms of
   Use](terms_2000cmp_2008.md))

   Source: `https://www.ccli.gov.hk/doc/2000cmp_2008.txt` (CCLI)

5) [ISO/IEC 10646:2003 and its Amendments 1 to 6 compatibility
   table](New2003cmp_2008.txt) ([Terms of Use](terms_New2003cmp_2008.md))

   Source: `https://www.ccli.gov.hk/doc/New2003cmp_2008.txt` (CCLI)

6) [ISO/IEC 10646:2003 and its Amendment 1 compatibility
   table](2003cmp_2008.txt) ([Terms of Use](terms_2003cmp_2008.md))

   Source: `https://www.ccli.gov.hk/doc/2003cmp_2008.txt` (CCLI)

7) [Big-5 compatibility table](big5cmp.txt) ([Terms of Use](terms_big5cmp.md))

   Source: `https://www.ccli.gov.hk/doc/big5cmp.txt` (CCLI)

8) [Hong Kong Supplementary Character Set related information](HKSCS2016.json)
   ([Terms of Use](data_gov_hk_terms.md))

   Source:
   `https://www.ogcio.gov.hk/tc/our_work/business/tech_promotion/ccli/hkscs/doc/HKSCS2016.json`
   (DATA.GOV.HK)


<!-- END OF GENERATED LIST -->

Updating the files
------------------

The `download.py` script attempts to download documents from the [sources](#sources).

Usage:

```shell
$ python download.py
... follow the instructions and accept/reject the license terms ...
```

The script was tested on Python 3.10 and Requests 2.27.1.

The files to download are listed in `sources.py`, which is loaded by the download
script. You will find two sections.

* `CCLI_TERMS_URLS` is just a list of newline-separated urls for the "terms of use" page
  on the CCLI website for each of the documents to download. The downloader makes a lot
  of assumptions about the format of this page so it will probably break by the time of
  the next update. But the URL is presented as canonical, and I choose to believe this
  is going to be true.

* `CKAN_DATASETS` references the CKAN API dataset id (or package id/name) for
  DATA.GOV.HK datasets. It can optionally encode an expectation of a latest known
  filename (`last_known_filename`) and timestamp (`last_known_date`).

  The timestamp is important because the download script will complain in case the
  specified version is not available anymore (the historical API is *not* used). Since
  updates can happen frequently, this is expected to happen soon. You can decide to
  follow the instructions to download a different version, or update the entry in the
  sources file.

At the end of the process, the script invites you to update the list in this `README.md`
file at the marked section, which can be useful to keep this information fresh.

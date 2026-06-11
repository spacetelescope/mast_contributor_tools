#!/usr/bin/env python3

import argparse
from astropy.io import fits


def search_all_headers(fits_file, keyword):
    keyword = keyword.upper()
    found_any = False

    # Will Scan through each extension in the fits file
    for idx, hdu in enumerate(fits_file):
        hdr = hdu.header
        extname = hdr.get("EXTNAME", "PRIMARY")

        # Looks for exact matches to the input provided
        exact_matches = {k: hdr[k] for k in hdr if k == keyword}

        # Prefix matches (for example CDELT would return whatever is prefixed with that input so you would get CDELT1, CDELT2, etc)
        prefix_matches = {
            k: hdr[k] for k in hdr if k.startswith(keyword) and k != keyword
        }

        # Prints the location of the Keyword in the HDU and returns if it was an exact or a keyword match
        if exact_matches or prefix_matches:
            print(f"> [FOUND] Ext {idx} ({extname})")

            for k, v in exact_matches.items():
                print(f"    EXACT   {k} = {v}")

            for k, v in prefix_matches.items():
                print(f"    PREFIX  {k} = {v}")

            found_any = True
        else:
            print(f"> [NOT FOUND] Ext {idx} ({extname})")

    if not found_any:
        print(f"\nKeyword '{keyword}' was not found in any extension.")


def main():
    parser = argparse.ArgumentParser(
        description="Search all FITS header extensions for a keyword or close match"
    )
    parser.add_argument("filename", help="Path to FITS file")
    parser.add_argument(
        "-k", "--keyword", required=True,
        help="Header keyword to search for (e.g. CDELT)"
    )

    args = parser.parse_args()

    with fits.open(args.filename) as hdul:
        search_all_headers(hdul, args.keyword)


if __name__ == "__main__":
    main()
    # /ifs/archive/test/mast/public/hlsp/pie/data/field01/hlsp_pie_hst_wfc3_field01_f336w_v1_drz.fits

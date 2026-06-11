from astropy.io import fits
import json

def keyword_finder(fits_file, hlsp_type, verbose=True):
    """
    helper function to search a fits file for common metadata + metadata of specific hlsp types (currently only supports image, spectral). Will return exact and partial matches

    Parameters:
    ------------
    fits_file:
        Path to a .fits file
    hlsp_type:
        image or spectra (currently) will search metadata keywords for that type
    verbose:
        Default TRUE, will output the value of matched keywords


    """

    print(f"Finding Keyword Matches for HLSP TYPE: {hlsp_type}")
    
    with open("metadata_keywords.json", "r") as f:
        data = json.load(f)

        if hlsp_type not in data:
            raise ValueError(f"Invalid hlsp_type: '{hlsp_type}' please use one of the following: {[k for k in data.keys() if k != 'common']}")
        keywords = data.get("common", []) + data.get(f"{hlsp_type}", [])
        keywords.sort()
    
    keywords = [k.upper() for k in keywords]
    found_any_global = False
    
    with fits.open(fits_file) as fits_file:
        for idx, hdu in enumerate(fits_file):
            hdr = hdu.header
            extname = hdr.get("EXTNAME", "PRIMARY")

            print(f"\n--- Ext {idx} ({extname}) ---")

            found_in_this_hdu = False

            for keyword in keywords:
                exact_matches = {k: hdr[k] for k in hdr if k == keyword}

                prefix_matches = {
                    k: hdr[k]
                    for k in hdr
                    if k.startswith(keyword) and k != keyword
                }
                
                if exact_matches or prefix_matches:
                    print(f"> {keyword} [Success]")

                    if verbose:
                        for k, v in exact_matches.items():
                            print(f"    > Exact Match: {k} = {v}")

                        for k, v in prefix_matches.items():
                            print(f"    > Prefix Match: {k} = {v}")

                    found_any_global = True
                    found_in_this_hdu = True

                else:
                    print(f"> {keyword} [fail]")

            if not found_in_this_hdu:
                print(" No Matched found in this extension")

    if not found_any_global:
        print("\nNone of the keywords were found in any extension.")


keyword_finder(fits_file="/home/areedy/scratch/kronos/hlsp_kronos_jwst_niriss_v1298tauc_exotedrf_v1_uncalstellarspec.fits", hlsp_type="spectral")
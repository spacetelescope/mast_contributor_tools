
from astropy.io import fits
import json
import pandas as pd
import re


def keyword_finder(fits_file, meta_types=None, verbose=False):

    with open("metadata_keywords.json") as f:
        metadata = json.load(f)

    categories = ["common"]

    if meta_types:
        if isinstance(meta_types, str):
            categories.append(meta_types)
        else:
            categories.extend(meta_types)

    categories = list(dict.fromkeys(categories))
    results = []

    with fits.open(fits_file) as hdul:

        for category in categories:
            if category not in metadata:
                continue

            for rule in metadata[category]:
                keyword = rule["keyword"]
                match_type = rule.get("match_type", "exact")
                pattern = rule.get("pattern")
                condition = rule.get("condition", "")

                found_extensions = []
                matches = []

                for ext_num, hdu in enumerate(hdul):

                    hdr = hdu.header

                    # If json entry for this keyword is marked as exact it will try to match the keyword 
                    if match_type == "exact":
                        if keyword in hdr:
                            found_extensions.append(ext_num)
                            matches.append({
                                "extension": ext_num,
                                "keyword": keyword,
                                "value": hdr[keyword]
                            })

                    # if the json entry is marked as regex and and a regex pattern exists it will look for that pattern
                    elif match_type == "regex":

                        for k in hdr:
                            if re.match(pattern, k):
                                found_extensions.append(ext_num)
                                matches.append({
                                    "extension": ext_num,
                                    "keyword": k,
                                    "value": hdr[k]
                                })

                found_extensions = sorted(set(found_extensions))

                results.append({
                    "KEYWORD": keyword,
                    "CATAGORY": category,
                    "RULE": rule["rule"],
                    "FOUND": "SUCCESS" if matches else "FAIL",
                    #"MATCH COUNT": len(matches),
                    "EXT FOUND": found_extensions,
                    #"MATCHES": [m["keyword"] for m in matches],
                    "VALUE": list(set(m["value"] for m in matches)),
                    "IGNORE_COND": condition,
                })

    df = pd.DataFrame(results)

    

    if verbose:
        print(df)

    return df
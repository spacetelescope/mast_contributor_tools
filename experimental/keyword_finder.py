
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
    print(f"Checking Metadata Keywords for: {fits_file}")
    with fits.open(fits_file) as hdul:

        for category in categories:
            if category not in metadata:
                continue

            for rule in metadata[category]:
                keyword = rule["keyword"]
                match_type = rule.get("match_type", "exact")
                pattern = rule.get("pattern")
                ignore_keyword = rule.get("ignore_keyword", "")
                ignore_keyword_value = rule.get("ignore_keyword_value", "")

                found_extensions = []
                matches = []

                # Goes through each extension in the header and searches for keywords
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
                    "EXT EXPECT": rule['extension'],
                    #"MATCH COUNT": len(matches),
                    "EXT FOUND": found_extensions,
                    #"MATCHES": [m["keyword"] for m in matches],
                    "VALUE": list(set(m["value"] for m in matches)),
                    "IGNORE_KEYWORD": f"{ignore_keyword}",
                    "IGNORE_VALUE": f"{ignore_keyword_value}"
                })

    df = pd.DataFrame(results)

    # Collects all the abopve information and provides a summary of keyword match results
    summary_rows = []

    for level in ["required", "recommended", "suggested"]:

        level_df = df[df["RULE"].str.lower() == level]

        total = len(level_df)
        found = (level_df["FOUND"] == "SUCCESS").sum()

        summary_rows.append({
            "CATEGORY": level,
            "FOUND": found,
            "TOTAL": total,
            "PERCENT": round(100 * found / total, 1) if total else 0,
            "MISSING": level_df.loc[
                level_df["FOUND"] == "FAIL",
                "KEYWORD"
            ].tolist()
        })

    summary_df = pd.DataFrame(summary_rows)
    
    if verbose:
        print(df)
        print(f"\nSUMMARY")
        print(summary_df)

    return df
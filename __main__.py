import argparse
from pathlib import Path

from hlsp_filename import HlspFileName


def main(inFile, hlspName):
    """HLSP filename module CLI driver.

    Parameters
    ----------
    inFile : str
        Name of example HLSP product
    hlspName : str
        Name of example HLSP collection
    """
    fp = Path(inFile)
    hfn = HlspFileName(fp, hlspName)
    hfn.partition()
    hfn.create_fields()
    elements = hfn.evaluate_fields()
    file_rec = hfn.evaluate_filename()

    # Display results
    print("Filename parameters:")
    for p, v in file_rec.items():
        print(f"  {p}: {v}")

    print("Field parameters:")
    for e in elements:
        for p, v in e.items():
            print(f"  {p}: {v}")


if __name__ == "__main__":
    """HLSP filename module entry point.
    """
    descr_text = "Validate a specific name of an HLSP science product"
    parser = argparse.ArgumentParser(description=descr_text)
    parser.add_argument("in_file", type=str, help="Name of an HLSP product")
    parser.add_argument("hlsp_name", type=str, help="Name of HLSP collection")
    args = parser.parse_args()

    main(args.in_file, args.hlsp_name)

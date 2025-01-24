import argparse

from fc_app import check_single_filename

if __name__ == "__main__":
    """HLSP filename module entry point.
    """
    descr_text = "Validate a specific name of an HLSP science product"
    parser = argparse.ArgumentParser(description=descr_text)
    parser.add_argument("hlsp_name", type=str, help="Name of HLSP collection")
    parser.add_argument("in_file", type=str, help="Name of an HLSP product")
    args = parser.parse_args()
    check_single_filename(args.in_file, args.hlsp_name)

"""
Simple metadata validator for HLSP FITS files.

Provides:
- MetadataValidator: class to check required keywords, simple format/value rules,
  and produce a per-key and overall verdict.
- validate_fits_file(path, hlsp_name=None): convenience wrapper returning a dict report.

Notes:
- Requires astropy (astropy.io.fits). If not installed, raises ImportError with guidance.
- Uses package logger. Minimal, easy-to-extend ruleset.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

try:
    from astropy.io import fits
except Exception as e:  # pragma: no cover - runtime environment may not have astropy
    raise ImportError("astropy is required for metadata validation (pip install astropy)") from e

from mast_contributor_tools.utils.logger_config import setup_logger
from mast_contributor_tools.filename_check.hlsp_filename import MISSIONS  # type: ignore

logger = setup_logger(__name__)

# --- Load authoritative keyword lists from YAML (one-time embedded extraction of MAST pages) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORD_YAML = os.path.join(BASE_DIR, "metadata_keywords.yaml")
KNOWN_MISSIONS = set([m.lower() for m in MISSIONS])

# Remove fallback definitions — require the YAML to exist and be valid
try:
    with open(KEYWORD_YAML, "r") as yf:
        _kw = yaml.safe_load(yf)
except Exception as e:
    raise FileNotFoundError(f"Required metadata keyword YAML not found or unreadable at '{KEYWORD_YAML}': {e}")

# Validate YAML structure
if not isinstance(_kw, dict) or ("Common" not in _kw) or ("Image" not in _kw):
    raise ValueError(f"Invalid metadata keyword YAML structure in '{KEYWORD_YAML}'. Expected top-level keys 'Common' and 'Image'.")

COMMON_KEYWORDS = _kw["Common"]
IMAGE_KEYWORDS = _kw["Image"]

logger.info("Loaded metadata keyword lists from %s", KEYWORD_YAML)

# Verdict helpers
PASS = "PASS"
NEEDS_REVIEW = "NEEDS REVIEW"
FAIL = "FAIL"


@dataclass
class KeyReport:
    key: str
    present: bool = False
    value: Any = None
    verdict: str = FAIL
    message: str = ""


@dataclass
class MetadataReport:
    filepath: str
    hlsp_name: Optional[str] = None
    key_reports: List[KeyReport] = field(default_factory=list)
    overall_verdict: str = FAIL

    def summary(self) -> Dict[str, Any]:
        return {
            "filepath": self.filepath,
            "hlsp_name": self.hlsp_name,
            "overall_verdict": self.overall_verdict,
            "keys": [{kr.key: {"value": kr.value, "verdict": kr.verdict, "message": kr.message}} for kr in self.key_reports],
        }


class MetadataValidator:
    """
    Validate FITS header metadata against a small HLSP rule set.

    Basic checks performed:
      - presence of required keywords
      - non-empty string values where expected
      - DATE-OBS ISO 8601 parse
      - VERSION/HLSP version formatting (starts with 'v')
      - TELESCOP matched against known missions (if available) otherwise flagged 'NEEDS REVIEW'
      - simple filename / header cross-check (hlsp_name in header vs provided hlsp_name)

    Usage:
      v = MetadataValidator()
      report = v.validate(path_to_fits, hlsp_name='my-hlsp')
    """

    # Minimal required keywords for HLSP packages (customize as needed).
    REQUIRED_KEYWORDS = [
        "TELESCOP",
        "INSTRUME",
        "OBJECT",
        "DATE-OBS",
        "AUTHOR",
        "VERSION",
        # optional team-provided HLSP name key if present in headers by convention
        "HLSPNAME",
    ]

    VERSION_RE = re.compile(r"^v[0-9]+([.p][0-9a-zA-Z]+)*$")  # loose but enforces leading 'v'

    def __init__(self) -> None:
        # simple mapping of rules per-key; functions return (verdict, message)
        self._rules = {
            "TELESCOP": self._check_telescop,
            "INSTRUME": self._check_nonempty_string,
            "OBJECT": self._check_nonempty_string,
            "DATE-OBS": self._check_date_obs,
            "AUTHOR": self._check_nonempty_string,
            "VERSION": self._check_version,
            "HLSPNAME": self._check_hlspname,
        }
        # Use the runtime-loaded lists (from metadata_keywords.yaml), with safe copy
        self.common_keywords = {
            "required": list(COMMON_KEYWORDS.get("required", [])),
            "recommended": list(COMMON_KEYWORDS.get("recommended", [])),
            "suggested": list(COMMON_KEYWORDS.get("suggested", [])),
        }
        self.image_keywords = {
            "required": list(IMAGE_KEYWORDS.get("required", [])),
            "recommended": list(IMAGE_KEYWORDS.get("recommended", [])),
            "suggested": list(IMAGE_KEYWORDS.get("suggested", [])),
        }

    # --- New: helper to apply checks for keyword categories ---
    def _apply_keyword_checks(self, hdr, category_name: str, keywords: list[str], severity: str, report: MetadataReport, seen_keys: set[str]) -> None:
        """
        Check a list of keywords in hdr and append KeyReport entries to report.
        severity: 'required' -> missing FAIL, 'recommended'/'suggested' -> missing NEEDS_REVIEW
        """
        for key in keywords:
            if key in seen_keys:
                # avoid duplicate reports for same keyword
                continue
            present = key in hdr
            val = hdr.get(key, None)
            if severity == "required":
                if present:
                    verdict = PASS
                    message = "Present (required)."
                else:
                    verdict = FAIL
                    message = "Required keyword missing."
            else:  # recommended / suggested
                if present:
                    verdict = PASS
                    message = f"Present ({severity})."
                else:
                    verdict = NEEDS_REVIEW
                    message = f"{severity.capitalize()} keyword missing (recommend review)."
            kr = KeyReport(key=key, present=present, value=val, verdict=verdict, message=message)
            report.key_reports.append(kr)
            seen_keys.add(key)
            logger.debug(
                "Metadata keyword category check - Category: %s | Key: %s | Present: %s | Value: %r | Verdict: %s | Message: %s",
                category_name,
                key,
                present,
                val,
                verdict,
                message,
            )

    # --- individual key checks ---
    def _check_nonempty_string(self, value: Any) -> (str, str):
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return FAIL, "Required string is empty or missing."
        if isinstance(value, str) and not value.islower():
            # HLSP metadata strings often prefer lowercase identifiers; mark as review
            return NEEDS_REVIEW, "Value present but not lowercase; consider standardizing to lowercase."
        return PASS, "OK"

    def _check_date_obs(self, value: Any) -> (str, str):
        if value is None:
            return FAIL, "DATE-OBS missing."
        # Accept a few common ISO-like formats
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
            try:
                if isinstance(value, str):
                    datetime.strptime(value, fmt)
                    return PASS, "DATE-OBS parsed as ISO-like date."
                # astropy may provide Time objects or similar; accept non-strings
                return PASS, "DATE-OBS present (non-string) — accepted."
            except Exception:
                continue
        return NEEDS_REVIEW, "DATE-OBS not in ISO-like format (expected YYYY-MM-DD[T]HH:MM:SS[.f])."

    def _check_version(self, value: Any) -> (str, str):
        if value is None:
            return FAIL, "VERSION missing."
        if isinstance(value, str) and self.VERSION_RE.match(value):
            return PASS, "Version format looks correct (starts with 'v')."
        return NEEDS_REVIEW, "Version does not match expected pattern (should start with 'v', e.g., 'v1' or 'v1.0')."

    def _check_telescop(self, value: Any) -> (str, str):
        if value is None:
            return FAIL, "TELESCOP missing."
        if isinstance(value, str):
            val = value.lower()
            if val in KNOWN_MISSIONS:
                return PASS, "TELESCOP matches known mission list."
            # if we don't have mission list, or value not found, mark for review
            if KNOWN_MISSIONS:
                return NEEDS_REVIEW, "TELESCOP not recognized among known missions."
            else:
                return NEEDS_REVIEW, "TELESCOP present but mission list unavailable for validation."
        return NEEDS_REVIEW, "TELESCOP value type unexpected."

    def _check_hlspname(self, value: Any) -> (str, str):
        if value is None:
            return NEEDS_REVIEW, "HLSPNAME not present in header; this is optional but useful."
        if isinstance(value, str):
            # basic format: lowercase, hyphen allowed, <=20 chars (consistent with filename policy)
            if not value.islower():
                return NEEDS_REVIEW, "HLSP name in header is not lowercase."
            if len(value) > 20:
                return NEEDS_REVIEW, "HLSP name too long (should be <=20 characters)."
            return PASS, "HLSP name looks OK."
        return NEEDS_REVIEW, "HLSPNAME value type unexpected."

    # --- main validate method ---
    def validate(self, fits_path: Path | str, hlsp_name: Optional[str] = None) -> MetadataReport:
        """
        Validate a FITS file header and return a MetadataReport.

        Parameters
        ----------
        fits_path: Path or str - path to FITS file
        hlsp_name: Optional[str] - expected HLSP name (used for cross-check if HLSPNAME header exists)

        Returns
        -------
        MetadataReport
        """
        p = Path(fits_path)
        report = MetadataReport(filepath=str(p), hlsp_name=hlsp_name)

        logger.debug("Starting metadata validation for FITS file: %s", p)

        if not p.exists():
            logger.error("FITS file not found: %s", p)
            report.overall_verdict = FAIL
            report.key_reports.append(KeyReport(key="FILE", present=False, value=None, verdict=FAIL, message="File not found"))
            return report

        # Open header (first header of primary HDU)
        try:
            with fits.open(p, memmap=False) as hdul:
                hdr = hdul[0].header
        except Exception as e:
            logger.exception("Error reading FITS file %s", p)
            report.overall_verdict = FAIL
            report.key_reports.append(KeyReport(key="FILE_READ", present=False, value=None, verdict=FAIL, message=str(e)))
            return report

        # Log a brief summary of header keys (trimmed to first 50 keys to avoid excessive output)
        try:
            header_keys = list(hdr.keys())
            short_keys = header_keys[:50]
            logger.debug("Header contains %d keys. Example keys: %s%s", len(header_keys), short_keys, (" (truncated)" if len(header_keys) > 50 else ""))
        except Exception:
            logger.debug("Unable to enumerate header keys for logging.")

        # Evaluate required keys
        seen_keys = set()
        for key in self.REQUIRED_KEYWORDS:
            present = key in hdr
            val = hdr.get(key, None)
            if key in self._rules:
                verdict, message = self._rules[key](val)
            else:
                verdict, message = self._check_nonempty_string(val)
            kr = KeyReport(key=key, present=present, value=val, verdict=verdict, message=message)
            report.key_reports.append(kr)
            seen_keys.add(key)
            logger.debug(
                "Metadata key check - Key: %s | Present: %s | Value: %r | Verdict: %s | Message: %s",
                key,
                present,
                val,
                verdict,
                message,
            )

        # --- New: run Common and Image category checks ---
        # Common (required / recommended / suggested)
        try:
            self._apply_keyword_checks(hdr, "Common", self.common_keywords.get("required", []), "required", report, seen_keys)
            self._apply_keyword_checks(hdr, "Common", self.common_keywords.get("recommended", []), "recommended", report, seen_keys)
            self._apply_keyword_checks(hdr, "Common", self.common_keywords.get("suggested", []), "suggested", report, seen_keys)
        except Exception as e:
            logger.debug("Error while applying Common keyword checks: %s", e)

        # Image (required / recommended / suggested)
        try:
            self._apply_keyword_checks(hdr, "Image", self.image_keywords.get("required", []), "required", report, seen_keys)
            self._apply_keyword_checks(hdr, "Image", self.image_keywords.get("recommended", []), "recommended", report, seen_keys)
            self._apply_keyword_checks(hdr, "Image", self.image_keywords.get("suggested", []), "suggested", report, seen_keys)
        except Exception as e:
            logger.debug("Error while applying Image keyword checks: %s", e)

        # Cross-check hlsp_name if both provided (existing logic)
        if hlsp_name:
            header_hlsp = hdr.get("HLSPNAME") or hdr.get("HLSP_NAME") or hdr.get("HLSP")
            if header_hlsp:
                if str(header_hlsp).lower() != hlsp_name.lower():
                    report.key_reports.append(
                        KeyReport(
                            key="HLSPNAME_CONSISTENCY",
                            present=True,
                            value=f"header='{header_hlsp}' vs provided='{hlsp_name}'",
                            verdict=NEEDS_REVIEW,
                            message="HLSP name in header does not match provided hlsp_name argument.",
                        )
                    )
                    logger.debug(
                        "HLSPNAME_CONSISTENCY - header: %r | provided: %r | Verdict: %s",
                        header_hlsp,
                        hlsp_name,
                        NEEDS_REVIEW,
                    )
                else:
                    report.key_reports.append(
                        KeyReport(
                            key="HLSPNAME_CONSISTENCY",
                            present=True,
                            value=header_hlsp,
                            verdict=PASS,
                            message="HLSP name in header matches provided hlsp_name.",
                        )
                    )
                    logger.debug(
                        "HLSPNAME_CONSISTENCY - header: %r | provided: %r | Verdict: %s",
                        header_hlsp,
                        hlsp_name,
                        PASS,
                    )
            else:
                report.key_reports.append(
                    KeyReport(
                        key="HLSPNAME_CONSISTENCY",
                        present=False,
                        value=None,
                        verdict=NEEDS_REVIEW,
                        message="HLSP name not found in header to compare against provided hlsp_name.",
                    )
                )
                logger.debug("HLSPNAME_CONSISTENCY - header: None | provided: %r | Verdict: %s", hlsp_name, NEEDS_REVIEW)

        # Derive overall verdict: any FAIL -> FAIL, else any NEEDS_REVIEW -> NEEDS_REVIEW, else PASS
        verdicts = [kr.verdict for kr in report.key_reports]
        if FAIL in verdicts:
            report.overall_verdict = FAIL
        elif NEEDS_REVIEW in verdicts:
            report.overall_verdict = NEEDS_REVIEW
        else:
            report.overall_verdict = PASS

        logger.info("Completed metadata validation for %s: %s", p, report.overall_verdict)

        return report


# Convenience wrapper
def validate_fits_file(fits_path: Path | str, hlsp_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate a FITS file and return a serializable dict report.

    Example:
        summary = validate_fits_file("hlsp_my-hlsp_hst_wfc3_vega_f160w_v1_img.fits", hlsp_name="my-hlsp")
    """
    v = MetadataValidator()
    rep = v.validate(fits_path, hlsp_name=hlsp_name)
    return rep.summary()

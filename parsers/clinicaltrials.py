"""
Shared module for ClinicalTrials.gov API v2 integration.

Maps clinical trials to the same data contract as the clearing parsers:
  {"course": str, "entry_req": str}

  course    = brief trial title (NCT ID appended for uniqueness)
  entry_req = Status + eligibility criteria (full descriptive text)

When a trial changes status, amends eligibility, or disappears from
RECRUITING, the change detector picks it up exactly like a clearing change.
"""

import requests
import sys
import logging

log = logging.getLogger(__name__)

_API_URL = "https://clinicaltrials.gov/api/v2/studies"
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "ClearingMonitor/1.0 (educational research tool)",
}


def fetch_trials(condition: str, max_results: int = 8) -> list[dict]:
    """
    Returns up to max_results UK-based RECRUITING trials for the given
    condition, formatted as clearing parser output.
    """
    params = {
        "query.cond": condition,
        "query.locn": "United Kingdom",
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING",
        "format": "json",
        "pageSize": str(max_results),
        "sort": "LastUpdatePostDate:desc",
    }

    try:
        r = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        log.error("ClinicalTrials API error for '%s': %s", condition, exc)
        return []

    results = []
    for study in data.get("studies", []):
        try:
            proto   = study["protocolSection"]
            id_mod  = proto["identificationModule"]
            st_mod  = proto["statusModule"]
            el_mod  = proto.get("eligibilityModule", {})

            nct_id   = id_mod.get("nctId", "")
            title    = id_mod.get("briefTitle", "Unknown Study")
            status   = st_mod.get("overallStatus", "UNKNOWN")
            criteria = el_mod.get("eligibilityCriteria", "No eligibility criteria available.")
            min_age  = el_mod.get("minimumAge", "Not specified")
            max_age  = el_mod.get("maximumAge", "Not specified")
            sex      = el_mod.get("sex", "ALL").title()

            # Format like a clearing entry requirement – descriptive and structured
            entry_req = (
                f"Status: {status}  |  Age: {min_age} – {max_age}  |  {sex}\n\n"
                f"{criteria}"
            )

            # Course name: title + NCT ID so courses are always unique
            course = f"{title} [{nct_id}]"

            results.append({"course": course, "entry_req": entry_req})

        except (KeyError, TypeError) as exc:
            log.warning("Skipping malformed study: %s", exc)
            continue

    log.info("ClinicalTrials '%s': %d studies returned", condition, len(results))
    return results

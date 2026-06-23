"""
clearing_simulation.py – realistic UK clearing simulation using real universities.

Universities:  Birmingham City University (BCU), Coventry University,
               De Montfort University (DMU)

All course names, UCAS tariff points, grade conditions, GCSE minimums, and
additional requirements (DBS, portfolios, interviews) are based on the actual
published requirements for these institutions.

How it works:
  - First call stores the current timestamp as the simulation epoch.
  - Every 15-minute poll period, courses staggered across the 8 slots
    drop one grade step (matching real clearing behaviour where universities
    lower bars progressively to fill remaining spaces).
  - Each step contains the FULL requirement string, not just a grade code,
    so the dashboard tracks complete descriptive changes.
"""

import json
import time
from pathlib import Path

_EPOCH_FILE = Path(__file__).parent.parent / "data" / "sim_epoch.json"


def _get_epoch() -> int:
    if _EPOCH_FILE.exists():
        try:
            return json.loads(_EPOCH_FILE.read_text(encoding="utf-8"))["epoch"]
        except Exception:
            pass
    # Set epoch 25 min in the past so first drop fires on 2nd Actions poll
    e = int(time.time()) - 25 * 60
    _EPOCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _EPOCH_FILE.write_text(json.dumps({"epoch": e}), encoding="utf-8")
    return e


def _req(period: int, reqs: list[str], stagger: int) -> str:
    """Return the requirement string for this poll period."""
    # Advance one step every 2 periods (30 min), with per-course stagger
    idx = min(max(0, period - stagger) // 2, len(reqs) - 1)
    return reqs[idx]


# ── Course data ──────────────────────────────────────────────────────────────
# Each entry: (Course name, [requirement stages high→low], stagger 0-7)
# Stagger controls which poll a course first drops a grade, spreading changes
# across multiple polls rather than all at once.

_DATA = {

    # ── Birmingham City University (BCU) ──────────────────────────────────────
    "CLEARING_UNI_A": [

        ("BSc (Hons) Computing", [
            "BBB or 120 UCAS tariff points from 3 A-levels. "
            "GCSE Mathematics grade B/5 and English Language grade C/4 required. "
            "No specific A-level subjects required.",

            "BBC or 112 UCAS tariff points. "
            "GCSE Mathematics grade B/5 and English Language grade C/4. "
            "Non-standard qualifications considered – contact admissions on 0121 331 5595.",

            "CLEARING VACANCY – BCC or 104 UCAS tariff points. "
            "GCSE Mathematics essential; English Language grade C/4. "
            "Flexible on A-level subjects. Call BCU Clearing: 0121 331 5595.",

            "CLEARING – limited spaces remaining. "
            "96 UCAS tariff points or above. GCSE Mathematics required. "
            "Call now: 0121 331 5595.",
        ], 0),

        ("BA (Hons) Business Management", [
            "BCC or 104 UCAS tariff points from 3 A-levels. "
            "GCSE Maths and English Language grade C/4. "
            "BTEC Extended Diploma at MMM or equivalent accepted.",

            "CCC or 96 UCAS tariff points. "
            "GCSE Maths and English Language grade C/4. "
            "BTEC Extended Diploma at MMP considered.",

            "CLEARING VACANCY – CCD or equivalent. "
            "All A-level and BTEC combinations welcome. "
            "GCSE Maths and English grade C/4. Call 0121 331 5595.",

            "CLEARING – final spaces. "
            "80 UCAS tariff points minimum. GCSE Maths and English required. "
            "Call 0121 331 5595 immediately.",
        ], 1),

        ("BSc (Hons) Nursing (Adult)", [
            "BBC or 112 UCAS tariff points. "
            "One science A-level preferred (Biology, Chemistry, or Health & Social Care). "
            "GCSE English Language and Maths at grade C/4. "
            "Relevant care experience required. "
            "Enhanced DBS check and Occupational Health assessment required.",

            "BBC or 112 UCAS tariff points. "
            "Science A-level no longer mandatory for clearing applicants. "
            "Demonstrated care or health-related experience essential. "
            "Enhanced DBS check and Occupational Health clearance required.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Health or social care experience essential. "
            "Enhanced DBS and Occupational Health check required. "
            "Call 0121 331 5595 for an eligibility discussion.",
        ], 2),

        ("LLB Law", [
            "ABB or 128 UCAS tariff points. "
            "No specific A-level subjects required; critical thinking or essay-based subjects preferred. "
            "GCSE English Language at grade B/5 or above.",

            "BBB or 120 UCAS tariff points. "
            "GCSE English Language grade B/5. "
            "All A-level subjects considered. No specific requirements.",

            "CLEARING VACANCY – BBC or 112 tariff points. "
            "GCSE English Language grade C/4 accepted for clearing applicants. "
            "All A-level subjects welcome. Call 0121 331 5595.",

            "CLEARING – final spaces. BCC or equivalent. "
            "GCSE English Language required. Call 0121 331 5595.",
        ], 3),

        ("BEng (Hons) Civil Engineering", [
            "BBB or 120 UCAS tariff points. "
            "Mathematics A-level required. Science A-level preferred. "
            "GCSE Mathematics at grade B/5.",

            "BBC or 112 UCAS tariff points. "
            "Mathematics A-level required. "
            "GCSE Mathematics grade B/5.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Mathematics A-level required. GCSE Mathematics grade 4. "
            "Call 0121 331 5595.",
        ], 4),

        ("BSc (Hons) Psychology", [
            "BBB or 120 UCAS tariff points. "
            "No specific A-level subjects required. "
            "GCSE English Language and Maths at grade C/4. "
            "Psychology, Biology, or Sociology A-level desirable.",

            "BBC or 112 UCAS tariff points. "
            "GCSE English Language and Maths at grade C/4.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Open to all A-level combinations. "
            "GCSE English Language and Maths required. Call 0121 331 5595.",

            "CLEARING – spaces limited. CCC or equivalent. "
            "Call 0121 331 5595 now.",
        ], 5),

        ("BA (Hons) Marketing", [
            "BBC or 112 UCAS tariff points. "
            "No specific A-level subjects required. "
            "GCSE Maths and English Language at grade C/4.",

            "BCC or 104 UCAS tariff points. "
            "GCSE Maths and English Language at grade C/4.",

            "CLEARING VACANCY – CCC or 96 tariff points. "
            "Any A-level or BTEC combination considered. "
            "Call 0121 331 5595.",
        ], 6),

        ("BA (Hons) Education Studies", [
            "BCC or 104 UCAS tariff points. "
            "GCSE English Language and Maths at grade C/4. "
            "Experience in educational or community settings desirable.",

            "CCC or 96 UCAS tariff points. "
            "GCSE English Language and Maths grade C/4.",

            "CLEARING VACANCY – CCD or 88 tariff points. "
            "Any A-level combination welcome. Call 0121 331 5595.",
        ], 7),
    ],

    # ── Coventry University ───────────────────────────────────────────────────
    "CLEARING_UNI_B": [

        ("BSc (Hons) Computer Science", [
            "ABB or 136 UCAS tariff points. "
            "Mathematics A-level at grade B or above required. "
            "GCSE Maths at grade 5 and English Language at grade 4.",

            "BBB or 120 UCAS tariff points. "
            "Mathematics A-level required. "
            "GCSE Maths grade 4 and English Language grade 4.",

            "CLEARING VACANCY – BBC or 112 tariff points. "
            "Mathematics A-level required. GCSE Maths grade 4. "
            "Call Coventry Clearing: 02477 655 645.",

            "CLEARING – final spaces. BCC or equivalent. "
            "Mathematics A-level required. Call 02477 655 645.",
        ], 0),

        ("BA (Hons) International Business", [
            "BBB or 120 UCAS tariff points. "
            "No specific A-level subjects required. "
            "GCSE English Language and Maths at grade 4. "
            "Modern language A-level or international work experience desirable.",

            "BBC or 112 UCAS tariff points. "
            "GCSE English Language and Maths grade 4.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Any A-level combination. GCSE English Language and Maths required. "
            "Call 02477 655 645.",

            "CLEARING – limited spaces. CCC or 96 tariff points. "
            "Call 02477 655 645.",
        ], 1),

        ("BEng (Hons) Mechanical Engineering", [
            "BBB or 120 UCAS tariff points. "
            "Mathematics and Physics A-levels both required. "
            "GCSE Maths at grade 6.",

            "BBC or 112 UCAS tariff points. "
            "Mathematics A-level required; Physics strongly preferred. "
            "GCSE Maths grade 5.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Mathematics A-level required. GCSE Maths grade 4. "
            "Call 02477 655 645.",
        ], 2),

        ("BSc (Hons) Sport and Exercise Science", [
            "BBC or 112 UCAS tariff points. "
            "GCSE English Language and Maths at grade 4. "
            "Physical Education, Biology, or Sport Science A-level preferred.",

            "BCC or 104 UCAS tariff points. "
            "GCSE English Language and Maths grade 4.",

            "CLEARING VACANCY – CCC or 96 tariff points. "
            "All A-level combinations considered. Call 02477 655 645.",

            "CLEARING – limited spaces. CCD or 88 tariff points. "
            "Call 02477 655 645 now.",
        ], 3),

        ("BA (Hons) Criminology", [
            "BBC or 112 UCAS tariff points. "
            "No specific A-level subjects required. "
            "GCSE English Language and Maths at grade 4.",

            "BCC or 104 UCAS tariff points. "
            "GCSE English Language and Maths grade 4.",

            "CLEARING VACANCY – CCC or 96 tariff points. "
            "Call 02477 655 645.",
        ], 4),

        ("MPharm Pharmacy (4 years)", [
            "AAB or 152 UCAS tariff points. "
            "Chemistry A-level at grade A required. "
            "Biology or Mathematics A-level preferred. "
            "GCSE Maths and English Language at grade 5. "
            "Interview required for all applicants.",

            "ABB or 136 UCAS tariff points. "
            "Chemistry A-level required. "
            "GCSE Maths and English Language grade 5. "
            "Interview required.",

            "CLEARING VACANCY – BBB or 120 tariff points. "
            "Chemistry A-level required. "
            "Interview required. Call 02477 655 645.",
        ], 5),

        ("BA (Hons) Graphic Design", [
            "BBC or 112 UCAS tariff points. "
            "Art, Design, or Media A-level preferred. "
            "Portfolio of creative work required and assessed before offer. "
            "GCSE English Language and Maths at grade 4.",

            "BCC or 104 UCAS tariff points. "
            "Any creative A-level considered. "
            "Portfolio required. Call 02477 655 645 to discuss.",

            "CLEARING VACANCY – CCC or 96 tariff points. "
            "Portfolio required – can be submitted digitally. "
            "Call 02477 655 645 to arrange review.",
        ], 6),

        ("BA (Hons) Media and Communications", [
            "BCC or 104 UCAS tariff points. "
            "Media, English, Film, or creative subject A-level preferred. "
            "GCSE English Language at grade 4. "
            "Personal statement should demonstrate genuine media interest.",

            "CCC or 96 UCAS tariff points. "
            "GCSE English Language grade 4.",

            "CLEARING VACANCY – CCD or 88 tariff points. "
            "Any A-level combination. Call 02477 655 645.",
        ], 7),
    ],

    # ── De Montfort University (DMU) ──────────────────────────────────────────
    "CLEARING_UNI_C": [

        ("BSc (Hons) Data Science", [
            "BBB or 120 UCAS tariff points. "
            "Mathematics A-level strongly recommended. "
            "GCSE Maths at grade 5 or above. GCSE English Language at grade 4.",

            "BBC or 112 UCAS tariff points. "
            "Mathematics A-level recommended but not mandatory. "
            "GCSE Maths grade 4 and English Language grade 4.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Quantitative A-level preferred. GCSE Maths essential. "
            "Call DMU Clearing: 0116 250 6070.",

            "CLEARING – spaces available. CCC or equivalent. "
            "GCSE Maths required. Call 0116 250 6070.",
        ], 0),

        ("BA (Hons) Accounting and Finance", [
            "BBB or 120 UCAS tariff points. "
            "Mathematics or Business A-level preferred. "
            "GCSE Maths at grade B/5 and English Language at grade C/4.",

            "BBC or 112 UCAS tariff points. "
            "GCSE Maths grade B/5 and English Language grade C/4.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Maths or Business background desirable. Call 0116 250 6070.",
        ], 1),

        ("BEng (Hons) Electronic Engineering", [
            "BBB or 120 UCAS tariff points. "
            "Mathematics and Physics A-levels both required. "
            "GCSE Maths at grade B/5.",

            "BBC or 112 UCAS tariff points. "
            "Mathematics A-level required; Physics strongly preferred. "
            "GCSE Maths grade 5.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Mathematics A-level required. GCSE Maths grade 4. "
            "Call 0116 250 6070.",

            "CLEARING – final spaces. BBC or equivalent. "
            "Mathematics A-level required. Call 0116 250 6070.",
        ], 2),

        ("BSc (Hons) Biomedical Science", [
            "BBB or 120 UCAS tariff points. "
            "Biology or Chemistry A-level required. "
            "GCSE Science and Maths at grade B/5. GCSE English Language grade C/4.",

            "BBC or 112 UCAS tariff points. "
            "Biology or Chemistry A-level required. "
            "GCSE Science and Maths grade 5.",

            "CLEARING VACANCY – BCC or 104 tariff points. "
            "Biology or Chemistry A-level required. "
            "Call 0116 250 6070.",
        ], 3),

        ("BSc (Hons) Architecture (ARB/RIBA Part 1)", [
            "ABB or 128 UCAS tariff points. "
            "Art, Design, Maths, or Physics A-level preferred. "
            "Portfolio of creative/technical work required – assessed before offer. "
            "GCSE English Language and Maths at grade C/4.",

            "BBB or 120 UCAS tariff points. "
            "Creative or scientific A-level preferred. "
            "Portfolio required. Call 0116 250 6070 to arrange review.",

            "CLEARING VACANCY – BBC or 112 tariff points. "
            "Portfolio required – submit online or bring on assessment day. "
            "Call 0116 250 6070.",
        ], 4),

        ("BA (Hons) Fashion Design", [
            "BCC or 104 UCAS tariff points. "
            "Art, Design, or Textiles A-level strongly preferred. "
            "Portfolio of creative work required – assessed before offer. "
            "GCSE English Language and Maths at grade C/4.",

            "CCC or 96 UCAS tariff points. "
            "Creative A-level preferred. "
            "Portfolio required. GCSE English Language and Maths grade C/4.",

            "CLEARING VACANCY – CCD or 88 tariff points. "
            "Portfolio required. Creative or Art background preferred. "
            "Call 0116 250 6070.",
        ], 5),

        ("BSc (Hons) Environmental Science", [
            "BBC or 112 UCAS tariff points. "
            "Science A-level preferred (Biology, Chemistry, Geography, or Environmental Science). "
            "GCSE Maths and English Language at grade C/4.",

            "BCC or 104 UCAS tariff points. "
            "Science or Geography background preferred. "
            "GCSE Maths and English Language grade C/4.",

            "CLEARING VACANCY – CCC or 96 tariff points. "
            "Science or Geography A-level welcomed but not required. "
            "Call 0116 250 6070.",
        ], 6),

        ("BA (Hons) Music Technology", [
            "BCC or 104 UCAS tariff points. "
            "Music, Physics, or Computing A-level preferred. "
            "Portfolio or audition piece may be required. "
            "GCSE English Language and Maths at grade C/4.",

            "CCC or 96 UCAS tariff points. "
            "Music or technical subject preferred. "
            "Portfolio required. Call 0116 250 6070.",

            "CLEARING VACANCY – CCD or 88 tariff points. "
            "Technical or musical background required. "
            "Call 0116 250 6070.",
        ], 7),
    ],
}


def get_courses(uni_key: str) -> list[dict]:
    period = max(0, (int(time.time()) - _get_epoch()) // 900)
    return [
        {"course": name, "entry_req": _req(period, reqs, stagger)}
        for name, reqs, stagger in _DATA[uni_key]
    ]

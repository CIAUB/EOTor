#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════════
#  EOTor Engine — Enterprise Multi-Location SOCKS5 Routing Manager
#  (includes EZ-Panel: 3X-UI / PasarGuard integration)
# ══════════════════════════════════════════════════════════════════════════════
#  Developer  : CIAUB
#  Maintainer : CIAUB
#  Contact    : https://t.me/CIAUB  |  Channel: https://t.me/CIAUB_CH
#  GitHub     : https://github.com/CIAUB/EOTor
#  License    : MIT
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys
import json
import time
import re
import copy
import shutil
import hashlib
import secrets
import sqlite3
import unicodedata
import urllib.request
import subprocess
import concurrent.futures
import threading
import itertools
from datetime import datetime
from collections import OrderedDict

__author__    = "CIAUB"
__maintainer__ = "CIAUB"
__license__   = "MIT"

# ══════════════════════════════════════════════════════════════════════════════
#  THEME — truecolor palette with 256-color / 16-color / no-color fallbacks
# ══════════════════════════════════════════════════════════════════════════════
def _detect_color_mode():
    if os.environ.get("NO_COLOR"):
        return None
    if not (os.environ.get("FORCE_COLOR") or sys.stdout.isatty()):
        return None
    colorterm = os.environ.get("COLORTERM", "").lower()
    if "truecolor" in colorterm or "24bit" in colorterm or os.environ.get("FORCE_COLOR") == "truecolor":
        return "true"
    if "256" in os.environ.get("TERM", ""):
        return "256"
    return "16"

_COLOR_MODE = _detect_color_mode()

def _to_256(r, g, b):
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)

def _fg(rgb, basic, bold=False):
    if _COLOR_MODE is None:
        return ""
    if _COLOR_MODE == "true":
        return "\033[%s38;2;%d;%d;%dm" % ("1;" if bold else "", *rgb)
    if _COLOR_MODE == "256":
        return "\033[%s38;5;%dm" % ("1;" if bold else "", _to_256(*rgb))
    return "\033[%sm" % basic

def _esc(code):
    return "" if _COLOR_MODE is None else code

class C:
    ACCENT = _fg((230, 57, 70), "1;31", bold=True)     # brand crimson: borders, titles
    RED    = _fg((255, 107, 107), "1;31")              # errors
    GREEN  = _fg((74, 222, 128), "1;32")               # success / active
    YELLOW = _fg((251, 191, 36), "1;33")               # prompts / warnings
    BLUE   = _fg((96, 165, 250), "1;34")               # info
    PURPLE = _fg((192, 132, 252), "1;35")              # labels
    TEAL   = _fg((45, 212, 191), "1;36")               # IPs, ports, numbers
    WHITE  = _fg((241, 245, 249), "1;37")              # primary text
    DIM    = _fg((120, 128, 145), "2;37")              # muted text
    BOLD   = _esc("\033[1m")
    RESET  = _esc("\033[0m")
    CYAN   = ACCENT                                    # legacy alias used by older call sites

def _gradient(i, n):
    """Crimson → deep red gradient for the logo, i in [0, n)."""
    t = i / max(n - 1, 1)
    rgb = (int(250 - 60 * t), int(70 - 40 * t), int(80 - 40 * t))
    return _fg(rgb, "1;31", bold=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BRANDING
# ══════════════════════════════════════════════════════════════════════════════
BRAND_NAME       = "EOTor Engine"
BRAND_VERSION    = "v4.0.0"
BRAND_TAGLINE    = "Enterprise Multi-Location Routing Manager"
BRAND_DEVELOPER  = "CIAUB"
BRAND_CONTACT    = "https://t.me/CIAUB"
BRAND_CHANNEL    = "https://t.me/CIAUB_CH"
BRAND_GITHUB     = "https://github.com/CIAUB/EOTor"

# ── Filesystem path mapping (internal paths stay unchanged; only display changes) ──
# Internal paths used by the underlying runtime:
_INTERNAL_INSTANCE_DIR  = "/etc/tor/instances"
_INTERNAL_VARLIB_DIR    = "/var/lib/tor-instances"
# Display aliases shown to the user:
_DISPLAY_INSTANCE_DIR   = "/etc/eotor/instances"
_DISPLAY_VARLIB_DIR     = "/var/lib/eotor"
_DISPLAY_CONF_NAME      = "eotor.conf"
_DISPLAY_PID_NAME       = "eotor.pid"
_DISPLAY_LOG_DIR        = "/var/log/eotor"
_DISPLAY_OPT_DIR        = "/opt/eotor"
_DISPLAY_LOCAL_DIR      = "/usr/local/eotor"

# ── Country flag emoji map ────────────────────────────────────────────────────
_FLAG_MAP = {
    "af": "🇦🇫", "al": "🇦🇱", "dz": "🇩🇿", "ad": "🇦🇩", "ao": "🇦🇴",
    "ag": "🇦🇬", "am": "🇦🇲", "aw": "🇦🇼", "ax": "🇦🇽", "bs": "🇧🇸",
    "bh": "🇧🇭", "bd": "🇧🇩", "bb": "🇧🇧", "by": "🇧🇾", "bz": "🇧🇿",
    "bj": "🇧🇯", "bm": "🇧🇲", "bt": "🇧🇹", "bo": "🇧🇴", "ba": "🇧🇦",
    "bw": "🇧🇼", "br": "🇧🇷", "bn": "🇧🇳", "kh": "🇰🇭", "cm": "🇨🇲",
    "cv": "🇨🇻", "ky": "🇰🇾", "cf": "🇨🇫", "td": "🇹🇩", "cn": "🇨🇳",
    "co": "🇨🇴", "km": "🇰🇲", "cg": "🇨🇬", "cd": "🇨🇩", "cu": "🇨🇺",
    "ci": "🇨🇮", "dj": "🇩🇯", "dm": "🇩🇲", "do": "🇩🇴", "ec": "🇪🇨",
    "eg": "🇪🇬", "sv": "🇸🇻", "gq": "🇬🇶", "er": "🇪🇷", "ee": "🇪🇪",
    "et": "🇪🇹", "fk": "🇫🇰", "fo": "🇫🇴", "fj": "🇫🇯", "gf": "🇬🇫",
    "pf": "🇵🇫", "ga": "🇬🇦", "gm": "🇬🇲", "ge": "🇬🇪", "gh": "🇬🇭",
    "gi": "🇬🇮", "gp": "🇬🇵", "gu": "🇬🇺", "gt": "🇬🇹", "gg": "🇬🇬",
    "gn": "🇬🇳", "gw": "🇬🇼", "gy": "🇬🇾", "ht": "🇭🇹", "hn": "🇭🇳",
    "ir": "🇮🇷", "iq": "🇮🇶", "im": "🇮🇲", "jm": "🇯🇲", "jo": "🇯🇴",
    "kz": "🇰🇿", "ke": "🇰🇪", "ki": "🇰🇮", "kw": "🇰🇼", "kg": "🇰🇬",
    "la": "🇱🇦", "lv": "🇱🇻", "lb": "🇱🇧", "ls": "🇱🇸", "lr": "🇱🇷",
    "ly": "🇱🇾", "li": "🇱🇮", "lt": "🇱🇹", "mo": "🇲🇴", "mk": "🇲🇰",
    "mg": "🇲🇬", "mw": "🇲🇼", "mv": "🇲🇻", "ml": "🇲🇱", "mt": "🇲🇹",
    "mh": "🇲🇭", "mq": "🇲🇶", "mr": "🇲🇷", "mu": "🇲🇺", "yt": "🇾🇹",
    "fm": "🇫🇲", "mn": "🇲🇳", "me": "🇲🇪", "ma": "🇲🇦", "mz": "🇲🇿",
    "mm": "🇲🇲", "na": "🇳🇦", "nr": "🇳🇷", "np": "🇳🇵", "nc": "🇳🇨",
    "nz": "🇳🇿", "ni": "🇳🇮", "ne": "🇳🇪", "ng": "🇳🇬", "nu": "🇳🇺",
    "nf": "🇳🇫", "mp": "🇲🇵", "om": "🇴🇲", "pk": "🇵🇰", "pw": "🇵🇼",
    "ps": "🇵🇸", "pa": "🇵🇦", "pg": "🇵🇬", "py": "🇵🇾", "pe": "🇵🇪",
    "ph": "🇵🇭", "pn": "🇵🇳", "pr": "🇵🇷", "qa": "🇶🇦", "re": "🇷🇪",
    "rs": "🇷🇸", "sh": "🇸🇭", "kn": "🇰🇳", "lc": "🇱🇨", "pm": "🇵🇲",
    "vc": "🇻🇨", "ws": "🇼🇸", "sm": "🇸🇲", "st": "🇸🇹", "sa": "🇸🇦",
    "sn": "🇸🇳", "sl": "🇸🇱", "sk": "🇸🇰", "si": "🇸🇮", "sb": "🇸🇧",
    "so": "🇸🇴", "ss": "🇸🇸", "lk": "🇱🇰", "sd": "🇸🇩", "sr": "🇸🇷",
    "sz": "🇸🇿", "sy": "🇸🇾", "tj": "🇹🇯", "th": "🇹🇭", "tl": "🇹🇱",
    "tg": "🇹🇬", "tk": "🇹🇰", "to": "🇹🇴", "tt": "🇹🇹", "tm": "🇹🇲",
    "tv": "🇹🇻", "ug": "🇺🇬", "uz": "🇺🇿", "vu": "🇻🇺", "ve": "🇻🇪",
    "ye": "🇾🇪", "zm": "🇿🇲", "zw": "🇿🇼",
    # Main 50
    "de": "🇩🇪", "tr": "🇹🇷", "us": "🇺🇸", "fr": "🇫🇷", "at": "🇦🇹",
    "be": "🇧🇪", "ro": "🇷🇴", "ca": "🇨🇦", "sg": "🇸🇬", "jp": "🇯🇵",
    "ie": "🇮🇪", "fi": "🇫🇮", "es": "🇪🇸", "pl": "🇵🇱", "nl": "🇳🇱",
    "it": "🇮🇹", "ch": "🇨🇭", "se": "🇸🇪", "no": "🇳🇴", "dk": "🇩🇰",
    "is": "🇮🇸", "au": "🇦🇺", "in": "🇮🇳", "hk": "🇭🇰", "ua": "🇺🇦",
    "cz": "🇨🇿", "kr": "🇰🇷", "za": "🇿🇦", "mx": "🇲🇽", "my": "🇲🇾",
    "az": "🇦🇿", "cy": "🇨🇾", "gr": "🇬🇷", "pt": "🇵🇹", "hu": "🇭🇺",
    "lu": "🇱🇺", "gb": "🇬🇧", "ar": "🇦🇷", "tw": "🇹🇼", "bg": "🇧🇬",
    "il": "🇮🇱", "md": "🇲🇩", "ru": "🇷🇺", "cl": "🇨🇱", "cr": "🇨🇷",
    "vn": "🇻🇳", "id": "🇮🇩", "sc": "🇸🇨", "hr": "🇭🇷", "tn": "🇹🇳",
}

def _flag(iso: str) -> str:
    return _FLAG_MAP.get(iso.lower(), "🌐")

def _display_instance_path(iso: str) -> str:
    """Return user-facing path for a location config (alias only)."""
    return f"{_DISPLAY_INSTANCE_DIR}/{iso}/{_DISPLAY_CONF_NAME}"

def _display_node_name(iso: str) -> str:
    """Return EOTor-branded node name, e.g. eotor_de."""
    return f"eotor_{iso.lower()}"

# ══════════════════════════════════════════════════════════════════════════════
#  LOCATIONS — MAIN 50 (ports 9080-9129)
# ══════════════════════════════════════════════════════════════════════════════
LOCATIONS = {
    1:  {"iso": "de", "port": 9080, "name": "Germany"},
    2:  {"iso": "tr", "port": 9081, "name": "Turkey"},
    3:  {"iso": "us", "port": 9082, "name": "United States"},
    4:  {"iso": "fr", "port": 9083, "name": "France"},
    5:  {"iso": "at", "port": 9084, "name": "Austria"},
    6:  {"iso": "be", "port": 9085, "name": "Belgium"},
    7:  {"iso": "ro", "port": 9086, "name": "Romania"},
    8:  {"iso": "ca", "port": 9087, "name": "Canada"},
    9:  {"iso": "sg", "port": 9088, "name": "Singapore"},
    10: {"iso": "jp", "port": 9089, "name": "Japan"},
    11: {"iso": "ie", "port": 9090, "name": "Ireland"},
    12: {"iso": "fi", "port": 9091, "name": "Finland"},
    13: {"iso": "es", "port": 9092, "name": "Spain"},
    14: {"iso": "pl", "port": 9093, "name": "Poland"},
    15: {"iso": "nl", "port": 9094, "name": "Netherlands"},
    16: {"iso": "it", "port": 9095, "name": "Italy"},
    17: {"iso": "ch", "port": 9096, "name": "Switzerland"},
    18: {"iso": "se", "port": 9097, "name": "Sweden"},
    19: {"iso": "no", "port": 9098, "name": "Norway"},
    20: {"iso": "dk", "port": 9099, "name": "Denmark"},
    21: {"iso": "is", "port": 9100, "name": "Iceland"},
    22: {"iso": "au", "port": 9101, "name": "Australia"},
    23: {"iso": "in", "port": 9102, "name": "India"},
    24: {"iso": "hk", "port": 9103, "name": "Hong Kong"},
    25: {"iso": "ua", "port": 9104, "name": "Ukraine"},
    26: {"iso": "cz", "port": 9105, "name": "Czech Republic"},
    27: {"iso": "kr", "port": 9106, "name": "South Korea"},
    28: {"iso": "za", "port": 9107, "name": "South Africa"},
    29: {"iso": "mx", "port": 9108, "name": "Mexico"},
    30: {"iso": "my", "port": 9109, "name": "Malaysia"},
    31: {"iso": "az", "port": 9110, "name": "Azerbaijan"},
    32: {"iso": "cy", "port": 9111, "name": "Cyprus"},
    33: {"iso": "gr", "port": 9112, "name": "Greece"},
    34: {"iso": "pt", "port": 9113, "name": "Portugal"},
    35: {"iso": "hu", "port": 9114, "name": "Hungary"},
    36: {"iso": "lu", "port": 9115, "name": "Luxembourg"},
    37: {"iso": "gb", "port": 9116, "name": "United Kingdom"},
    38: {"iso": "ar", "port": 9117, "name": "Argentina"},
    39: {"iso": "tw", "port": 9118, "name": "Taiwan"},
    40: {"iso": "bg", "port": 9119, "name": "Bulgaria"},
    41: {"iso": "il", "port": 9120, "name": "Israel"},
    42: {"iso": "md", "port": 9121, "name": "Moldova"},
    43: {"iso": "ru", "port": 9122, "name": "Russia"},
    44: {"iso": "cl", "port": 9123, "name": "Chile"},
    45: {"iso": "cr", "port": 9124, "name": "Costa Rica"},
    46: {"iso": "vn", "port": 9125, "name": "Vietnam"},
    47: {"iso": "id", "port": 9126, "name": "Indonesia"},
    48: {"iso": "sc", "port": 9127, "name": "Seychelles"},
    49: {"iso": "hr", "port": 9128, "name": "Croatia"},
    50: {"iso": "tn", "port": 9129, "name": "Tunisia"},
}

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL LOCATIONS (ports 9130+)
# ══════════════════════════════════════════════════════════════════════════════
_GLOBAL_NAMES = [
    ("af", "Afghanistan"), ("al", "Albania"), ("dz", "Algeria"),
    ("ad", "Andorra"), ("ao", "Angola"), ("ag", "Antigua and Barbuda"),
    ("am", "Armenia"), ("aw", "Aruba"), ("ax", "Åland Islands"),
    ("bs", "Bahamas"), ("bh", "Bahrain"), ("bd", "Bangladesh"),
    ("bb", "Barbados"), ("by", "Belarus"), ("bz", "Belize"),
    ("bj", "Benin"), ("bm", "Bermuda"), ("bt", "Bhutan"),
    ("bo", "Bolivia"), ("ba", "Bosnia and Herzegovina"), ("bw", "Botswana"),
    ("br", "Brazil"), ("bn", "Brunei"), ("kh", "Cambodia"),
    ("cm", "Cameroon"), ("cv", "Cape Verde"), ("ky", "Cayman Islands"),
    ("cf", "Central African Republic"), ("td", "Chad"), ("cn", "China"),
    ("co", "Colombia"), ("km", "Comoros"), ("cg", "Congo"),
    ("cd", "Democratic Republic of Congo"), ("cu", "Cuba"),
    ("ci", "Côte d'Ivoire"), ("dj", "Djibouti"), ("dm", "Dominica"),
    ("do", "Dominican Republic"), ("ec", "Ecuador"), ("eg", "Egypt"),
    ("sv", "El Salvador"), ("gq", "Equatorial Guinea"), ("er", "Eritrea"),
    ("ee", "Estonia"), ("et", "Ethiopia"), ("fk", "Falkland Islands"),
    ("fo", "Faroe Islands"), ("fj", "Fiji"), ("gf", "French Guiana"),
    ("pf", "French Polynesia"), ("ga", "Gabon"), ("gm", "Gambia"),
    ("ge", "Georgia"), ("gh", "Ghana"), ("gi", "Gibraltar"),
    ("gp", "Guadeloupe"), ("gu", "Guam"), ("gt", "Guatemala"),
    ("gg", "Guernsey"), ("gn", "Guinea"), ("gw", "Guinea-Bissau"),
    ("gy", "Guyana"), ("ht", "Haiti"), ("hn", "Honduras"),
    ("ir", "Iran"), ("iq", "Iraq"), ("im", "Isle of Man"),
    ("jm", "Jamaica"), ("jo", "Jordan"), ("kz", "Kazakhstan"),
    ("ke", "Kenya"), ("ki", "Kiribati"), ("kw", "Kuwait"),
    ("kg", "Kyrgyzstan"), ("la", "Laos"), ("lv", "Latvia"),
    ("lb", "Lebanon"), ("ls", "Lesotho"), ("lr", "Liberia"),
    ("ly", "Libya"), ("li", "Liechtenstein"), ("lt", "Lithuania"),
    ("mo", "Macao"), ("mk", "North Macedonia"), ("mg", "Madagascar"),
    ("mw", "Malawi"), ("mv", "Maldives"), ("ml", "Mali"),
    ("mt", "Malta"), ("mh", "Marshall Islands"), ("mq", "Martinique"),
    ("mr", "Mauritania"), ("mu", "Mauritius"), ("yt", "Mayotte"),
    ("fm", "Micronesia"), ("mn", "Mongolia"), ("me", "Montenegro"),
    ("ma", "Morocco"), ("mz", "Mozambique"), ("mm", "Myanmar"),
    ("na", "Namibia"), ("nr", "Nauru"), ("np", "Nepal"),
    ("nc", "New Caledonia"), ("nz", "New Zealand"), ("ni", "Nicaragua"),
    ("ne", "Niger"), ("ng", "Nigeria"), ("nu", "Niue"),
    ("nf", "Norfolk Island"), ("mp", "Northern Mariana Islands"),
    ("om", "Oman"), ("pk", "Pakistan"), ("pw", "Palau"),
    ("ps", "Palestine"), ("pa", "Panama"), ("pg", "Papua New Guinea"),
    ("py", "Paraguay"), ("pe", "Peru"), ("ph", "Philippines"),
    ("pn", "Pitcairn Islands"), ("pr", "Puerto Rico"), ("qa", "Qatar"),
    ("re", "Réunion"), ("rs", "Serbia"), ("sh", "Saint Helena"),
    ("kn", "Saint Kitts and Nevis"), ("lc", "Saint Lucia"),
    ("pm", "Saint Pierre and Miquelon"),
    ("vc", "Saint Vincent and the Grenadines"), ("ws", "Samoa"),
    ("sm", "San Marino"), ("st", "São Tomé and Príncipe"),
    ("sa", "Saudi Arabia"), ("sn", "Senegal"), ("sl", "Sierra Leone"),
    ("sk", "Slovakia"), ("si", "Slovenia"), ("sb", "Solomon Islands"),
    ("so", "Somalia"), ("ss", "South Sudan"), ("lk", "Sri Lanka"),
    ("sd", "Sudan"), ("sr", "Suriname"), ("sz", "Eswatini"),
    ("sy", "Syria"), ("tj", "Tajikistan"), ("th", "Thailand"),
    ("tl", "Timor-Leste"), ("tg", "Togo"), ("tk", "Tokelau"),
    ("to", "Tonga"), ("tt", "Trinidad and Tobago"), ("tm", "Turkmenistan"),
    ("tv", "Tuvalu"), ("ug", "Uganda"), ("uz", "Uzbekistan"),
    ("vu", "Vanuatu"), ("ve", "Venezuela"), ("ye", "Yemen"),
    ("zm", "Zambia"), ("zw", "Zimbabwe"),
]

GLOBAL_LOCATIONS = {}
_global_start_port = 9130
for _idx, (_iso, _name) in enumerate(_GLOBAL_NAMES):
    _nid = 51 + _idx
    GLOBAL_LOCATIONS[_nid] = {
        "iso": _iso,
        "port": _global_start_port + _idx,
        "name": _name,
    }

ALL_LOCATIONS = {**LOCATIONS, **GLOBAL_LOCATIONS}

# ══════════════════════════════════════════════════════════════════════════════
#  RUNTIME CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
MIN_EXIT_NODES    = 3
LOW_EXIT_NODES    = 10
TIMEOUT_NORMAL    = 60
TIMEOUT_LOW       = 120
FAST_TIMEOUT      = 3
FAST_TIMEOUT_EXT  = 7
EXTEND_PCT        = 5
MAX_FAST_RETRIES  = 8
STABILITY_CHECKS  = 2
STABILITY_DELAY   = 1.5
PARALLEL_WORKERS  = 5
FINAL_VERIFY_WAIT = 3

_print_lock  = threading.Lock()
_report_lock = threading.Lock()

report_data   = {"SUCCESS": [], "FAILED": [], "SKIPPED": [], "RETRIED": [], "WARNED": []}
SESSION_START = datetime.now()
_exit_cache: dict = {}

_deployment_progress = {
    "total": 0, "completed": 0, "success": 0, "failed": 0, "current_nodes": {}
}
_progress_lock  = threading.Lock()
_display_thread = None
_display_active = False

_ip_cache = OrderedDict()
_ip_lock  = threading.Lock()

# ══════════════════════════════════════════════════════════════════════════════
#  UI PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_spinner_iter   = itertools.cycle(_SPINNER_FRAMES)

def _spin() -> str:
    return next(_spinner_iter)

def _bar_color(percent: int) -> str:
    return C.RED if percent < 40 else (C.YELLOW if percent < 80 else C.GREEN)

def _progress_bar(percent: int, width: int = 26, color: str = None) -> str:
    filled = int(width * percent / 100)
    color  = color or _bar_color(percent)
    return (f"{color}{'━' * filled}{C.DIM}{'╌' * (width - filled)}{C.RESET} "
            f"{color}{percent:>3}%{C.RESET}")

def _install_bar(percent: int, width: int = 30) -> str:
    return f" {_progress_bar(percent, width)}"

def _divider(char="─", width=None, color=None) -> str:
    color = color or C.DIM
    return f"{color}{char * (width or term_width() - 4)}{C.RESET}"

# ── Width-aware layout helpers ────────────────────────────────────────────────
_ANSI_RE = re.compile(r"\033\[[0-9;?]*[A-Za-z]")

def _char_width(ch: str) -> int:
    o = ord(ch)
    if o == 0x200D or 0xFE00 <= o <= 0xFE0F or unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1

def vlen(s: str) -> int:
    """Visible terminal width: ANSI codes are free, wide glyphs count as two cells."""
    return sum(_char_width(ch) for ch in _ANSI_RE.sub("", s))

def pad(s: str, width: int, align: str = "<") -> str:
    gap = max(width - vlen(s), 0)
    if align == ">":
        return " " * gap + s
    if align == "^":
        return " " * (gap // 2) + s + " " * (gap - gap // 2)
    return s + " " * gap

def term_width() -> int:
    cols = shutil.get_terminal_size((100, 24)).columns
    return max(64, min(cols - 4, 100))

def box_lines(title, rows, width=None, color=None):
    """Rounded panel. `rows` items: str, or ('─',) for a divider."""
    w, color = width or term_width(), color or C.ACCENT
    inner = w - 2
    head = f" {title} " if title else ""
    out = [f"{color}╭─{C.RESET}{C.BOLD}{C.WHITE}{head}{C.RESET}"
           f"{color}{'─' * (inner - 1 - vlen(head))}╮{C.RESET}"]
    for row in rows:
        if row == "─":
            out.append(f"{color}├{'─' * inner}┤{C.RESET}")
        else:
            out.append(f"{color}│{C.RESET}{pad(row, inner)}{color}│{C.RESET}")
    out.append(f"{color}╰{'─' * inner}╯{C.RESET}")
    return out

def menu_lines(title, items, width=None, subtitle=None, color=None):
    """items: (key, label[, hint[, style]]) tuples, None for a gap, or a plain str for a section label."""
    rows = []
    if subtitle:
        rows += [f"  {C.DIM}{subtitle}{C.RESET}", ""]
    inner = (width or term_width()) - 2
    for it in items:
        if it is None:
            rows.append("")
            continue
        if isinstance(it, str):
            rows.append(f"  {C.DIM}{it.upper()}{C.RESET}")
            continue
        key, label, *rest = it
        hint  = rest[0] if rest else ""
        style = rest[1] if len(rest) > 1 else ""
        key_col = C.RED if style == "danger" else (C.DIM if key == "0" else C.ACCENT)
        txt_col = C.RED if style == "danger" else (C.DIM if key == "0" else C.WHITE)
        left = f"  {key_col}{C.BOLD}[{key}]{C.RESET}  {txt_col}{label}{C.RESET}"
        if hint:
            room = inner - vlen(left) - 3
            hint = hint if vlen(hint) <= room else hint[:max(room - 1, 0)] + "…"
            left = pad(left, inner - vlen(hint) - 2) + f"{C.DIM}{hint}{C.RESET}"
        rows.append(left)
    return box_lines(title, rows, width, color)

def table_lines(headers, rows, aligns=None, indent="  "):
    aligns = aligns or "<" * len(headers)
    cols = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(vlen(str(c)) for c in col) for col in cols]
    def fmt(cells):
        parts = [pad(str(c), widths[i], aligns[i]) for i, c in enumerate(cells)]
        return indent + "  ".join(parts)
    head = f"{C.DIM}{fmt(headers)}{C.RESET}"
    rule = f"{C.DIM}{indent}{'  '.join('─' * w for w in widths)}{C.RESET}"
    return [head, rule] + [fmt(r) for r in rows]

def fixed_row(cells, widths, aligns=None, indent="  "):
    aligns = aligns or "<" * len(cells)
    return indent + "  ".join(pad(str(c), widths[i], aligns[i]) for i, c in enumerate(cells))

def fixed_rule(widths, indent="  "):
    return f"{C.DIM}{indent}{'  '.join('─' * w for w in widths)}{C.RESET}"

# ── Console helpers ───────────────────────────────────────────────────────────
def clear_screen():
    if sys.stdout.isatty():
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.flush()

def out(*lines, indent=2):
    for line in lines:
        print(" " * indent + line)

def ok(msg):    print(f"  {C.GREEN}✔{C.RESET}  {msg}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")
def fail(msg):  print(f"  {C.RED}✘{C.RESET}  {msg}")
def info(msg):  print(f"  {C.BLUE}ℹ{C.RESET}  {msg}")
def note(msg):  print(f"  {C.DIM}{msg}{C.RESET}")

def ask(label):
    return input(f"\n  {C.ACCENT}❯{C.RESET} {C.YELLOW}{label}:{C.RESET} ").strip()

def pause(msg="Press Enter to continue"):
    input(f"\n  {C.DIM}{msg}…{C.RESET}")

def confirm(prompt="Proceed?"):
    ans = input(f"\n  {C.YELLOW}❓ {prompt}{C.RESET} {C.DIM}[y/N]{C.RESET} ").strip().lower()
    return ans in ("y", "yes")

def screen_title(icon, title, color=None):
    print(f"\n  {color or C.ACCENT}{icon}  {C.BOLD}{title}{C.RESET}\n")

# ══════════════════════════════════════════════════════════════════════════════
#  ASCII LOGO
# ══════════════════════════════════════════════════════════════════════════════
def _print_logo():
    logo_lines = [
        r"███████╗ ██████╗ ████████╗ ██████╗ ██████╗ ",
        r"██╔════╝██╔═══██╗╚══██╔══╝██╔═══██╗██╔══██╗",
        r"█████╗  ██║   ██║   ██║   ██║   ██║██████╔╝",
        r"██╔══╝  ██║   ██║   ██║   ██║   ██║██╔══██╗",
        r"███████╗╚██████╔╝   ██║   ╚██████╔╝██║  ██║",
        r"╚══════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝",
    ]
    print()
    for i, line in enumerate(logo_lines):
        print(f"   {_gradient(i, len(logo_lines))}{line}{C.RESET}")
    print(f"   {C.WHITE}{C.BOLD}E N G I N E{C.RESET}  {C.DIM}·{C.RESET}  "
          f"{C.ACCENT}{BRAND_VERSION}{C.RESET}  {C.DIM}·  {BRAND_TAGLINE}  ·  by {BRAND_DEVELOPER}{C.RESET}")
    print()

# ══════════════════════════════════════════════════════════════════════════════
#  INSTALLER PROGRESS DISPLAY
# ══════════════════════════════════════════════════════════════════════════════
_INSTALL_STEPS = [
    (5,   "Initializing EOTor Engine Runtime"),
    (15,  "Verifying System Prerequisites"),
    (25,  "Configuring Package Sources"),
    (40,  "Installing Core Components"),
    (55,  "Preparing Routing Modules"),
    (70,  "Loading Location Definitions"),
    (80,  "Applying Permissions & Ownership"),
    (90,  "Registering System Service"),
    (100, "Finalizing Installation"),
]

def _print_install_step(step_idx: int, message: str, done: bool = False):
    pct    = _INSTALL_STEPS[step_idx][0]
    icon   = f"{C.GREEN}✔{C.RESET}" if done else f"{C.YELLOW}{_spin()}{C.RESET}"
    bar    = _install_bar(pct)
    status = f"{C.GREEN}Done{C.RESET}" if done else f"{C.YELLOW}Running...{C.RESET}"
    print(f"\r  {icon}  {message:<45} {status}", flush=True)
    if done:
        print(f"    {bar}", flush=True)

def _animate_install_step(message: str, duration: float = 0.6):
    """Show spinner animation for a step, then mark done."""
    frames = _SPINNER_FRAMES
    end_time = time.time() + duration
    idx = 0
    while time.time() < end_time:
        frame = frames[idx % len(frames)]
        print(f"\r  {C.YELLOW}{frame}{C.RESET}  {message:<45} {C.DIM}Running...{C.RESET}",
              end="", flush=True)
        time.sleep(0.07)
        idx += 1
    print(f"\r  {C.GREEN}✔{C.RESET}  {message:<45} {C.GREEN}Done      {C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def run_cmd(cmd):
    return subprocess.run(cmd, shell=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_out(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def check_root():
    if os.geteuid() != 0:
        print(f"\n{C.RED}  ✘  Permission denied — {BRAND_NAME} must be run as root.{C.RESET}\n")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
#  SELF-INSTALL
# ══════════════════════════════════════════════════════════════════════════════
INSTALL_PATH = "/usr/local/bin/eotor"

def self_install():
    try:
        script_path = os.path.abspath(sys.argv[0])
        try:
            os.chmod(script_path, 0o755)
        except Exception:
            pass
        already_installed = (
            os.path.exists(INSTALL_PATH)
            and os.path.exists(script_path)
            and os.path.samefile(script_path, INSTALL_PATH)
        )
        if not already_installed:
            shutil.copy2(script_path, INSTALL_PATH)
            os.chmod(INSTALL_PATH, 0o755)
            print(f"  {C.GREEN}✔{C.RESET}  Registered as a system command. "
                  f"{C.DIM}You can now run:{C.RESET} {C.WHITE}eotor{C.RESET}")
            time.sleep(1.2)
    except Exception:
        pass

def node_is_installed(iso):
    return os.path.exists(f"{_INTERNAL_INSTANCE_DIR}/{iso}/torrc")

def node_is_running(iso):
    return run_out(f"systemctl is-active tor@{iso}").stdout.strip() == "active"

def running_isos() -> set:
    """All active tor@<iso> units in one systemctl call (used for bulk displays)."""
    r = run_out("systemctl list-units 'tor@*.service' --state=active --plain --no-legend --no-pager")
    return {m.group(1) for m in re.finditer(r"^\s*tor@([\w-]+)\.service", r.stdout, re.M)}

# ══════════════════════════════════════════════════════════════════════════════
#  EXIT NODE COUNT
# ══════════════════════════════════════════════════════════════════════════════
def get_exit_node_count(iso: str) -> int:
    if iso in _exit_cache:
        return _exit_cache[iso]
    try:
        url = f"https://onionoo.torproject.org/summary?flag=Exit&country={iso}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            d     = json.loads(r.read().decode())
            count = len(d.get("relays", []))
            _exit_cache[iso] = count
            return count
    except:
        _exit_cache[iso] = -1
        return -1

def fetch_all_exit_counts():
    print(f"\n{C.DIM}  {_spin()}  Fetching location availability data...{C.RESET}",
          flush=True)
    isos = list({d["iso"] for d in ALL_LOCATIONS.values() if d["iso"] not in _exit_cache})
    if not isos:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        list(pool.map(get_exit_node_count, isos))

def _ec_badge(iso: str) -> str:
    n = _exit_cache.get(iso, -1)
    if n < 0:
        s = "  ?"
    elif n == 0:
        s = "  ✘"
    else:
        s = f"{n:>3}"
    if n < 0:
        color = C.DIM
    elif n == 0:
        color = C.RED
    elif n < MIN_EXIT_NODES:
        color = C.RED
    elif n < LOW_EXIT_NODES:
        color = C.YELLOW
    else:
        color = C.GREEN
    return f"{C.DIM}[{C.RESET}{color}{s}{C.RESET}{C.DIM}]{C.RESET}"

# ══════════════════════════════════════════════════════════════════════════════
#  ENGINE — INSTALL / UPDATE / UNINSTALL  (internal logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def engine_install():
    clear_screen()
    _print_logo()
    print(f"{_divider()}")
    print(f"  {C.WHITE}INSTALLING {BRAND_NAME.upper()} CORE{C.RESET}")
    print(f"{_divider()}\n")

    steps = [
        "Initializing EOTor Engine Runtime",
        "Checking System Prerequisites",
        "Refreshing Package Database",
        "Installing Core Components",
        "Disabling Conflicting Services",
        "Verifying Installation Integrity",
    ]

    _animate_install_step(steps[0], 0.4)

    run_cmd("dpkg --configure -a")
    _animate_install_step(steps[1], 0.3)

    run_cmd("apt-get update -qq")
    _animate_install_step(steps[2], 0.4)

    missing = [p for p in ["tor", "tor-geoipdb", "curl"]
               if run_cmd(f"dpkg -s {p}").returncode != 0]
    if missing:
        print(f"\n  {C.YELLOW}⚡  Installing missing components: "
              f"{', '.join(missing)}{C.RESET}")
        run_cmd(f"apt-get install -yq {' '.join(missing)}")
    _animate_install_step(steps[3], 0.5)

    run_cmd("systemctl stop tor.service")
    run_cmd("systemctl disable tor.service")
    _animate_install_step(steps[4], 0.3)

    still_missing = [p for p in ["tor", "tor-geoipdb", "curl"]
                     if run_cmd(f"dpkg -s {p}").returncode != 0]
    _animate_install_step(steps[5], 0.3)

    print()
    print(f"  {_divider('─', 71)}")
    if still_missing:
        print(f"  {C.RED}✘  Some components could not be installed: "
              f"{', '.join(still_missing)}{C.RESET}")
        print(f"  {C.DIM}Check the system package manager for errors.{C.RESET}")
    else:
        print(f"  {C.GREEN}✔  {BRAND_NAME} Core installed successfully.{C.RESET}")
        print(f"  {C.DIM}Default service disabled to prevent port conflicts.{C.RESET}")
    print(f"  {_divider('─', 71)}")
    pause()

def engine_update():
    clear_screen()
    _print_logo()
    print(f"  {C.CYAN}⟳  Updating {BRAND_NAME} Core...{C.RESET}\n")
    _animate_install_step("Refreshing Package Sources", 0.4)
    run_cmd("apt-get update -qq")
    _animate_install_step("Upgrading Core Components", 0.6)
    run_out("apt-get install -yq --only-upgrade tor tor-geoipdb curl")
    _animate_install_step("Verifying Updated Components", 0.3)
    print(f"\n  {C.GREEN}✔  {BRAND_NAME} Core updated successfully.{C.RESET}")
    pause()

def engine_uninstall():
    installed = {nid: d for nid, d in ALL_LOCATIONS.items() if node_is_installed(d["iso"])}
    print(f"\n  {C.RED}⚠   WARNING — This will permanently remove ALL "
          f"{len(installed)} location module(s){C.RESET}")
    print(f"  {C.RED}    and uninstall the {BRAND_NAME} Core from this system.{C.RESET}\n")
    confirm = input(f"  {C.YELLOW}Type 'yes' to confirm: {C.RESET}").strip().lower()
    if confirm != "yes":
        print(f"  {C.DIM}Cancelled.{C.RESET}")
        pause()
        return
    if installed:
        print()
        _remove_targets(installed)
    print(f"\n  {C.YELLOW}⟳  Removing core packages...{C.RESET}")
    run_cmd("apt-get purge -yq tor tor-geoipdb")
    run_cmd("apt-get autoremove -yq")
    print(f"\n  {C.GREEN}✔  {BRAND_NAME} Core and all location modules removed.{C.RESET}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  SERVER INFO
# ══════════════════════════════════════════════════════════════════════════════
_server_info_cache = {"at": 0.0, "value": None}

def get_server_info():
    """(ip, location, isp) — cached for 10 minutes so menu redraws stay instant."""
    if _server_info_cache["value"] and time.time() - _server_info_cache["at"] < 600:
        return _server_info_cache["value"]
    value = _fetch_server_info()
    if value[0] != "Unknown":
        _server_info_cache.update(at=time.time(), value=value)
    return value

def _fetch_server_info():
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            d = json.loads(r.read().decode())
            if d.get("status") == "success":
                return (d.get("query"),
                        f"{d.get('city')}, {d.get('country')}",
                        d.get("isp"))
    except:
        pass
    return "Unknown", "Unknown", "Unknown"

def get_node_exit_ip(port, timeout=15):
    try:
        r = run_out(
            f"curl -s -m {timeout} --socks5-hostname 127.0.0.1:{port} "
            f"http://ip-api.com/json/")
        if r.returncode == 0 and r.stdout.strip():
            d = json.loads(r.stdout.strip())
            if d.get("status") == "success":
                return d.get("query")
    except:
        pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def clip(text: str, width: int) -> str:
    text = str(text)
    if vlen(text) <= width:
        return text
    while text and vlen(text) > width - 1:
        text = text[:-1]
    return text + "…"

def _os_name() -> str:
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME"):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "Linux"

def _led(on: bool) -> str:
    return f"{C.GREEN}●{C.RESET}" if on else f"{C.DIM}○{C.RESET}"

def draw_dashboard():
    clear_screen()
    _print_logo()

    ip, loc, isp = get_server_info()
    all_isos      = {d["iso"] for d in ALL_LOCATIONS.values()}
    inst_count    = sum(1 for iso in all_isos if node_is_installed(iso))
    running_count = len(running_isos() & all_isos)
    total_count   = len(ALL_LOCATIONS)
    guardian_on   = bool(_guardian_thread and _guardian_thread.is_alive())

    w    = term_width()
    half = (w - 2) // 2

    def kv(key, value, room):
        return f"{C.PURPLE}{key:<9}{C.RESET}{clip(value, room - 9)}"

    def two(left, right):
        return "  " + pad(left, half - 2) + right

    panels = "   ".join(f"{name} {_led(found)}" for name, found in detect_panels())
    rows = [
        two(kv("IP", f"{C.TEAL}{ip}{C.RESET}", half), kv("ISP", isp, half)),
        two(kv("Location", loc, half), kv("OS", _os_name(), half)),
        two(kv("Time", datetime.now().strftime("%Y-%m-%d  %H:%M"), half),
            kv("Guardian", f"{_led(guardian_on)} {'ON' if guardian_on else 'OFF'}", half)),
        "─",
        "  " + kv("Modules", f"{C.WHITE}{inst_count}{C.RESET}{C.DIM}/{total_count} deployed{C.RESET}  "
                            f"{_progress_bar(int(inst_count / total_count * 100), 16, C.ACCENT)}", w),
        "  " + kv("Active", f"{C.GREEN if running_count else C.DIM}{running_count}{C.RESET}"
                           f"{C.DIM}/{total_count} running{C.RESET}", w),
        "  " + kv("Panels", panels, w),
    ]
    print("\n".join("  " + l for l in box_lines("SYSTEM", rows, w)))

# ══════════════════════════════════════════════════════════════════════════════
#  LOCATION LIST
# ══════════════════════════════════════════════════════════════════════════════
def show_location_list(loc_dict=None, title=None):
    if loc_dict is None:
        loc_dict = LOCATIONS
    if title is None:
        title = "PRIMARY LOCATION MODULES · ports 9080–9129"

    running = running_isos()
    w       = term_width()
    ncols   = 2 if w >= 96 else 1
    cell_w  = (w - 4) // ncols

    def cell(nid, d):
        iso = d["iso"]
        if iso in running:
            led = f"{C.GREEN}●{C.RESET}"
        elif node_is_installed(iso):
            led = f"{C.YELLOW}●{C.RESET}"
        else:
            led = f"{C.DIM}○{C.RESET}"
        text = (f"{C.ACCENT}{nid:>3}{C.RESET}  {led} {_flag(iso)} "
                f"{C.WHITE}{pad(clip(d['name'], 22), 22)}{C.RESET} "
                f"{C.DIM}:{C.TEAL}{d['port']}{C.RESET} {_ec_badge(iso)}")
        return pad(text, cell_w)

    items = list(loc_dict.items())
    per   = (len(items) + ncols - 1) // ncols
    cols  = [items[i * per:(i + 1) * per] for i in range(ncols)]
    rows  = []
    for r in range(per):
        rows.append(" " + "".join(cell(*col[r]) for col in cols if r < len(col)))
    rows += ["─",
             f" {C.GREEN}●{C.RESET}{C.DIM} running   {C.RESET}{C.YELLOW}●{C.RESET}{C.DIM} stopped   "
             f"{C.RESET}{C.DIM}○ not deployed    relays: {C.RESET}"
             f"{C.GREEN}10+{C.RESET} {C.YELLOW}3–9{C.RESET} {C.RED}<3{C.RESET}"]
    print("\n".join("  " + l for l in box_lines(title, rows, w)))

def show_global_location_list():
    draw_dashboard()
    show_location_list(
        loc_dict=GLOBAL_LOCATIONS,
        title=f"EXTENDED LOCATION MODULES · ports 9130–{9130 + len(GLOBAL_LOCATIONS) - 1}"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  MENUS  (data-driven: one renderer, one loop)
# ══════════════════════════════════════════════════════════════════════════════
def show_menu(title, items, subtitle=None):
    print()
    print("\n".join("  " + l for l in menu_lines(title, items, term_width(), subtitle)))

def run_menu(title, items, handlers, subtitle=None):
    """Draw dashboard + menu, dispatch on the chosen key; '0' goes back."""
    while True:
        draw_dashboard()
        show_menu(title() if callable(title) else title, items, subtitle)
        choice = ask("Select option").lower()
        if choice == "0":
            return
        handler = handlers.get(choice)
        if handler is None:
            fail("Invalid option")
            time.sleep(1)
        else:
            handler()

def _running_locations() -> dict:
    live = running_isos()
    return {nid: d for nid, d in ALL_LOCATIONS.items() if d["iso"] in live}

def _guardian_badge() -> str:
    on = bool(_guardian_thread and _guardian_thread.is_alive())
    return f"{_led(on)} {'ON' if on else 'OFF'}"

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG WRITER (internal logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def write_torrc(iso: str, port: int, strict: bool = True):
    strict_val = "1" if strict else "0"
    try:
        with open(f"{_INTERNAL_INSTANCE_DIR}/{iso}/torrc", "w") as f:
            f.write(
                f"SocksPort 0.0.0.0:{port}\n"
                f"ExitNodes {{{iso}}}\n"
                f"StrictNodes {strict_val}\n"
            )
    except Exception as e:
        print(f"\n  {C.RED}✘  Configuration write error: {e}{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE PROGRESS DISPLAY (parallel deployment)
# ══════════════════════════════════════════════════════════════════════════════
def _live_progress_display():
    global _display_active
    while _display_active:
        with _progress_lock:
            total     = _deployment_progress["total"]
            completed = _deployment_progress["completed"]
            success   = _deployment_progress["success"]
            failed    = _deployment_progress["failed"]
            current   = dict(_deployment_progress["current_nodes"])
        if total == 0:
            time.sleep(0.1)
            continue
        w = term_width()
        stats = (f"  Total {C.WHITE}{total:>3}{C.RESET}   "
                 f"Done {C.GREEN}{success:>3}{C.RESET}   "
                 f"Failed {C.RED}{failed:>3}{C.RESET}   "
                 f"Pending {C.YELLOW}{total - completed:>3}{C.RESET}   "
                 f"{C.ACCENT}{_spin()}{C.RESET}")
        rows = ["", f"  {_progress_bar(int(completed / total * 100), w - 14)}", stats, ""]
        frame = box_lines(f"PARALLEL DEPLOYMENT · {BRAND_NAME}", rows, w)
        frame.append("")
        frame.append(f"{C.ACCENT}Active modules{C.RESET}")
        if current:
            frame += [current[iso] for iso in sorted(current)]
        else:
            frame.append(f"{C.DIM}Waiting for modules to initialize…{C.RESET}")
        text = "\033[H" + "".join(f"  {line}\033[K\n" for line in frame) + "\033[J"
        sys.stdout.write(text)
        sys.stdout.flush()
        time.sleep(0.1)

def _update_node_status(iso: str, status: str):
    with _progress_lock:
        _deployment_progress["current_nodes"][iso] = status

def _mark_node_complete(iso: str, success: bool):
    with _progress_lock:
        _deployment_progress["completed"] += 1
        if success:
            _deployment_progress["success"] += 1
        else:
            _deployment_progress["failed"] += 1
        if iso in _deployment_progress["current_nodes"]:
            del _deployment_progress["current_nodes"][iso]

# ══════════════════════════════════════════════════════════════════════════════
#  BOOTSTRAP WAITER (internal logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def _wait_bootstrap(iso: str, port: int, label: str,
                    timeout: int, attempt: int,
                    extended_timeout: int = None,
                    verbose: bool = True) -> int:
    suffix      = f" {C.DIM}#{attempt}{C.RESET}" if attempt > 1 else ""
    run_cmd(f"systemctl restart tor@{iso}")
    run_cmd(f"systemctl enable tor@{iso}")
    time.sleep(0.3)
    percent     = 0
    elapsed     = 0.0
    step        = 0.15
    max_timeout = timeout
    extended    = False
    while percent < 100 and elapsed < max_timeout:
        time.sleep(step)
        elapsed += step
        log     = run_out(f"journalctl -u tor@{iso} -n 50 --no-pager")
        matches = re.findall(r"Bootstrapped (\d+)%", log.stdout)
        if matches:
            percent = int(matches[-1])
        if (extended_timeout and not extended
                and percent > EXTEND_PCT and max_timeout < extended_timeout):
            max_timeout = extended_timeout
            extended    = True
        if verbose:
            bar     = _progress_bar(percent)
            ext_tag = f" {C.DIM}(extended){C.RESET}" if extended else ""
            print(f"\r  {C.CYAN}{label:<22}{C.RESET}  {bar}{suffix}{ext_tag}\033[K",
                  end="", flush=True)
        else:
            bar     = _progress_bar(percent, width=18)
            ext_tag = f" {C.DIM}ext{C.RESET}" if extended else ""
            _update_node_status(iso,
                f"{C.CYAN}{label:<22}{C.RESET} {bar}{suffix}{ext_tag}")
        if percent == 100:
            break
    if percent == 100:
        if verbose:
            print(f"\r  {C.CYAN}{label:<22}{C.RESET}  "
                  f"{_progress_bar(100)} "
                  f"{C.YELLOW}⏳ Finalizing...{C.RESET}\033[K",
                  end="", flush=True)
        else:
            _update_node_status(iso,
                f"{C.CYAN}{label:<22}{C.RESET} {_progress_bar(100, 18)} "
                f"{C.YELLOW}⏳ Finalizing{C.RESET}")
        time.sleep(FINAL_VERIFY_WAIT)
    return percent

# ══════════════════════════════════════════════════════════════════════════════
#  EXIT-IP STABILITY CHECK (internal logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def _check_exit_stable(port: int, checks: int = STABILITY_CHECKS,
                       delay: float = STABILITY_DELAY) -> bool:
    for _ in range(checks):
        time.sleep(delay)
        r = run_cmd(f"curl -s -m 8 --socks5-hostname 127.0.0.1:{port} "
                    f"https://www.google.com/generate_204")
        if r.returncode != 0:
            return False
    return True

# ══════════════════════════════════════════════════════════════════════════════
#  DEPLOY A SINGLE NODE (internal logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def deploy_node_task(data, verbose=True):
    iso   = data["iso"]
    port  = data["port"]
    name  = data["name"].upper()
    label = name

    def _line(msg, inplace=False):
        if verbose:
            print(msg, end="" if inplace else "\n", flush=True)

    exit_count = get_exit_node_count(iso)
    if 0 <= exit_count < MIN_EXIT_NODES:
        warning_msg = f"{C.RED}[⚠] {name}: {exit_count} relay(s) available{C.RESET}"
        if verbose:
            _line(f"\n  {warning_msg}")
        else:
            _update_node_status(iso,
                f"{C.CYAN}{name:<22}{C.RESET} {warning_msg}")
        with _report_lock:
            report_data["WARNED"].append(f"{name} ({exit_count} relays)")

    run_cmd(f"tor-instance-create {iso}")
    write_torrc(iso, port, strict=True)

    success  = False
    exit_ip  = None
    best_pct = 0

    for attempt in range(1, MAX_FAST_RETRIES + 1):
        pct = _wait_bootstrap(iso, port, label, FAST_TIMEOUT, attempt,
                              extended_timeout=FAST_TIMEOUT_EXT, verbose=verbose)
        best_pct = max(best_pct, pct)
        if pct == 100:
            verify_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                          f"{_progress_bar(100, 18)} "
                          f"{C.YELLOW}⏳ Verifying{C.RESET}")
            if verbose:
                _line(f"\r  {verify_msg}\033[K", inplace=True)
            else:
                _update_node_status(iso, verify_msg)
            r = run_cmd(f"curl -s -m 10 --socks5-hostname 127.0.0.1:{port} "
                        f"https://www.google.com/generate_204")
            if r.returncode == 0:
                candidate_ip  = get_node_exit_ip(port, timeout=10)
                stability_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                                 f"{C.DIM}Checking stability...{C.RESET}")
                if verbose:
                    _line(f"\r  {stability_msg}\033[K", inplace=True)
                else:
                    _update_node_status(iso, stability_msg)
                if candidate_ip and _check_exit_stable(port):
                    exit_ip = candidate_ip
                    success = True
                    if attempt > 1:
                        with _report_lock:
                            report_data["RETRIED"].append(name)
                    break
                else:
                    retry_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                                 f"{C.YELLOW}⚠ Unstable — retrying{C.RESET}")
                    if verbose:
                        _line(f"\r  {retry_msg}\033[K", inplace=True)
                    else:
                        _update_node_status(iso, retry_msg)
                    continue
            else:
                retry_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                             f"{C.YELLOW}⚠ Retrying...{C.RESET}")
                if verbose:
                    _line(f"\r  {retry_msg}\033[K", inplace=True)
                else:
                    _update_node_status(iso, retry_msg)
                continue

    if not success:
        fallback_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                        f"{C.YELLOW}↻ Relaxed mode{C.RESET}")
        if verbose:
            _line(f"\r  {fallback_msg}\033[K", inplace=True)
        else:
            _update_node_status(iso, fallback_msg)
        write_torrc(iso, port, strict=False)
        time.sleep(1)
        timeout = TIMEOUT_LOW if (0 <= exit_count < LOW_EXIT_NODES) else TIMEOUT_NORMAL
        pct = _wait_bootstrap(iso, port, label, timeout,
                              attempt=MAX_FAST_RETRIES + 1, verbose=verbose)
        best_pct = max(best_pct, pct)
        if pct == 100:
            write_torrc(iso, port, strict=True)
            run_cmd(f"systemctl reload tor@{iso}")
            final_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                         f"{C.YELLOW}⏳ Final check{C.RESET}")
            if verbose:
                _line(f"\r  {final_msg}\033[K", inplace=True)
            else:
                _update_node_status(iso, final_msg)
            time.sleep(FINAL_VERIFY_WAIT)
            r = run_cmd(f"curl -s -m 15 --socks5-hostname 127.0.0.1:{port} "
                        f"https://www.google.com/generate_204")
            if r.returncode == 0:
                candidate_ip = get_node_exit_ip(port, timeout=15)
                if candidate_ip and _check_exit_stable(port):
                    exit_ip = candidate_ip
                    success = True
                    with _report_lock:
                        report_data["RETRIED"].append(name)

    if success:
        ip_tag      = f" {C.PURPLE}→ {exit_ip}{C.RESET}" if exit_ip else ""
        success_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                       f"{C.GREEN}✔  DEPLOYED{C.RESET}{ip_tag}")
        if verbose:
            _line(f"\r  {success_msg}\033[K")
        else:
            _update_node_status(iso, success_msg)
            time.sleep(0.3)
        entry = f"{name} (:{port})" + (f" → {exit_ip}" if exit_ip else "")
        with _report_lock:
            report_data["SUCCESS"].append(entry)
    else:
        fail_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                    f"{C.RED}✘  FAILED{C.RESET} "
                    f"{C.DIM}(peak: {best_pct}%){C.RESET}")
        if verbose:
            _line(f"\r  {fail_msg}\033[K")
        else:
            _update_node_status(iso, fail_msg)
            time.sleep(0.3)
        with _report_lock:
            report_data["FAILED"].append(f"{name} (:{port}) [peak {best_pct}%]")
    if not verbose:
        _mark_node_complete(iso, success)

# ══════════════════════════════════════════════════════════════════════════════
#  DEPLOY PARALLEL
# ══════════════════════════════════════════════════════════════════════════════
def deploy_nodes_parallel(selected: dict, workers: int = PARALLEL_WORKERS):
    global _display_active, _display_thread
    total = len(selected)
    if total == 0:
        print(f"\n  {C.GREEN}✔  Nothing to deploy.{C.RESET}")
        return
    workers = max(1, min(workers, total))
    with _progress_lock:
        _deployment_progress["total"]         = total
        _deployment_progress["completed"]     = 0
        _deployment_progress["success"]       = 0
        _deployment_progress["failed"]        = 0
        _deployment_progress["current_nodes"] = {}
    _display_active = True
    _display_thread = threading.Thread(target=_live_progress_display, daemon=True)
    _display_thread.start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(deploy_node_task, d, False) for d in selected.values()]
        concurrent.futures.wait(futures)
    _display_active = False
    if _display_thread:
        _display_thread.join(timeout=1)
    print("\033[H\033[2J", end="", flush=True)
    print(f"\n  {C.GREEN}✔  Deployment complete!{C.RESET}\n")

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL NODE INSTALL
# ══════════════════════════════════════════════════════════════════════════════
def install_global_nodes():
    clear_screen()
    draw_dashboard()
    show_location_list(
        loc_dict=GLOBAL_LOCATIONS,
        title=f"EXTENDED MODULES (ID 51–{50 + len(GLOBAL_LOCATIONS)}, ports 9130+)"
    )
    ids_input = input(
        f"\n  {C.YELLOW}Enter module IDs to install (e.g. 51,72,100): {C.RESET}"
    ).strip()
    try:
        ids      = [int(x.strip()) for x in ids_input.split(",")]
        selected = {i: GLOBAL_LOCATIONS[i] for i in ids if i in GLOBAL_LOCATIONS}
        if not selected:
            print(f"\n  {C.RED}✘  No valid IDs "
                  f"(range: 51–{50 + len(GLOBAL_LOCATIONS)}){C.RESET}")
            pause()
            return
        if len(selected) == 1:
            print(f"\n  {C.YELLOW}⚡  Deploying 1 extended module...{C.RESET}\n")
            for d in selected.values():
                deploy_node_task(d, verbose=True)
        else:
            deploy_nodes_parallel(selected)
        print_report()
        pause()
    except ValueError:
        print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
        pause()

def search_and_install_global():
    clear_screen()
    draw_dashboard()
    print(f"\n  {C.CYAN}🔍  SEARCH & INSTALL EXTENDED MODULE{C.RESET}\n")
    search_term = input(
        f"  {C.YELLOW}Search country name: {C.RESET}"
    ).strip().lower()
    if not search_term:
        return

    results = {nid: d for nid, d in ALL_LOCATIONS.items()
               if search_term in d["name"].lower()}

    if not results:
        print(f"\n  {C.RED}✘  No matches found for '{search_term}'{C.RESET}")
        pause()
        return

    print(f"\n  {C.GREEN}Found {len(results)} match(es):{C.RESET}\n")
    live, rows = running_isos(), []
    for nid, d in sorted(results.items()):
        iso, ec = d["iso"], _exit_cache.get(d["iso"], -1)
        if iso in live:
            state = f"{C.GREEN}● running{C.RESET}"
        elif node_is_installed(iso):
            state = f"{C.YELLOW}● stopped{C.RESET}"
        else:
            state = f"{C.DIM}○ not deployed{C.RESET}"
        rows.append([f"{C.ACCENT}{nid}{C.RESET}", f"{_flag(iso)} {d['name']}",
                     f"{C.TEAL}{d['port']}{C.RESET}", str(ec) if ec >= 0 else "?", state,
                     f"{C.DIM}{'primary' if nid <= 50 else 'extended'}{C.RESET}"])
    print("\n".join(table_lines(["ID", "Name", "Port", "Relays", "Status", "Group"], rows, "><>><<")))

    print()
    ids_input = input(
        f"  {C.YELLOW}Enter IDs to install (comma-separated, or Enter to cancel): "
        f"{C.RESET}"
    ).strip()
    if not ids_input:
        return
    try:
        ids      = [int(x.strip()) for x in ids_input.split(",")]
        selected = {i: ALL_LOCATIONS[i] for i in ids if i in ALL_LOCATIONS}
        if not selected:
            print(f"\n  {C.RED}✘  No valid IDs{C.RESET}")
            pause()
            return
        if len(selected) == 1:
            for d in selected.values():
                deploy_node_task(d, verbose=True)
        else:
            deploy_nodes_parallel(selected)
        print_report()
        pause()
    except ValueError:
        print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
        pause()

# ══════════════════════════════════════════════════════════════════════════════
#  DOWNLOAD NODE
# ══════════════════════════════════════════════════════════════════════════════
def download_node():
    clear_screen()
    draw_dashboard()
    show_location_list()
    print(f"\n  {C.DIM}For extended modules (ID 51+) use option [G2] from main menu{C.RESET}")
    id_input = input(
        f"\n  {C.YELLOW}Enter ONE module ID to deploy: {C.RESET}"
    ).strip()
    try:
        nid = int(id_input)
        d   = ALL_LOCATIONS.get(nid)
        if not d:
            raise KeyError
    except (ValueError, KeyError):
        print(f"\n  {C.RED}✘  Invalid ID{C.RESET}")
        pause()
        return

    iso, port, name = d["iso"], d["port"], d["name"].upper()
    if node_is_installed(iso):
        print(f"\n  {C.YELLOW}⚠  {name} already deployed. "
              f"Remove it first to re-deploy.{C.RESET}")
        pause()
        return

    print(f"\n  {C.CYAN}⚡  Deploying {_flag(iso)} {name} (port {port})...{C.RESET}\n")
    deploy_node_task(d, verbose=True)
    print_report()
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  LIVE IP PANEL
# ══════════════════════════════════════════════════════════════════════════════
def _fetch_ip_task(nid, d):
    iso  = d["iso"]
    port = d["port"]
    name = d["name"]
    if not node_is_running(iso):
        return nid, name, None, "not_running"
    ip = get_node_exit_ip(port, timeout=15)
    with _ip_lock:
        _ip_cache[nid] = {"name": name, "port": port, "ip": ip, "time": datetime.now()}
    return nid, name, ip, "ok" if ip else "failed"

def live_ip_panel():
    draw_dashboard()
    running = _running_locations()
    if not running:
        fail("No active modules.")
        pause()
        return
    screen_title("🌐", f"LIVE IP PANEL · {len(running)} active modules")
    widths, aligns = [4, 28, 5, 22, 10], "><><<"
    print(f"{C.DIM}{fixed_row(['#', 'Location', 'Port', 'Exit IP', 'Status'], widths, aligns)}{C.RESET}")
    print(fixed_rule(widths))
    _ip_cache.clear()

    def display_ip(nid):
        while nid not in _ip_cache:
            time.sleep(0.05)
        data = _ip_cache[nid]
        flag = _flag(ALL_LOCATIONS[nid]["iso"])
        if data["ip"]:
            ip_cell, status = f"{C.TEAL}{data['ip']}{C.RESET}", f"{C.GREEN}✔ active{C.RESET}"
        else:
            ip_cell, status = f"{C.RED}unreachable{C.RESET}", f"{C.YELLOW}⚠ timeout{C.RESET}"
        print(fixed_row([f"{C.ACCENT}{nid}{C.RESET}", f"{flag} {clip(data['name'], 24)}",
                         f"{C.DIM}{data['port']}{C.RESET}", ip_cell, status], widths, aligns))
        sys.stdout.flush()

    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = [pool.submit(_fetch_ip_task, nid, d) for nid, d in running.items()]
        for nid in running.keys():
            display_ip(nid)
        concurrent.futures.wait(futures)

    print(fixed_rule(widths))
    success_count = sum(1 for v in _ip_cache.values() if v.get("ip"))
    print(f"\n  {C.GREEN}{success_count}/{len(running)}{C.RESET} modules responding")
    pause()

def show_exit_ips():
    draw_dashboard()
    screen_title("🌍", "EXIT IP MAP · current routing endpoints", C.PURPLE)
    running = _running_locations()
    if not running:
        fail("No active modules.")
        pause()
        return
    note(f"Querying {len(running)} active module(s)…\n")
    old_ips = getattr(show_exit_ips, 'prev_ips', {})

    def _check(item):
        nid, d = item
        return nid, get_node_exit_ip(d["port"], timeout=15)

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        for nid, ip in pool.map(_check, running.items()):
            results[nid] = ip

    stamp = datetime.now().strftime("%H:%M:%S")
    rows = []
    for nid, d in running.items():
        ip, old_ip = results.get(nid), old_ips.get(nid)
        if ip:
            changed = old_ip and old_ip != ip
            ip_cell = f"{C.YELLOW if changed else C.TEAL}{ip}{C.RESET}"
            tag     = f"{C.GREEN}changed{C.RESET}" if changed else ""
        else:
            ip_cell, tag = f"{C.RED}unreachable{C.RESET}", ""
        rows.append([f"{C.ACCENT}{nid}{C.RESET}", f"{_flag(d['iso'])} {d['name']}",
                     f"{C.DIM}{d['port']}{C.RESET}", ip_cell, f"{C.DIM}{stamp}{C.RESET}", tag])
    print("\n".join(table_lines(["#", "Location", "Port", "Exit IP", "Updated", ""], rows, "><><<<")))

    show_exit_ips.prev_ips = results
    success = sum(1 for ip in results.values() if ip)
    changed = sum(1 for nid in results
                  if old_ips.get(nid) and results.get(nid) and old_ips[nid] != results[nid])
    print(f"\n  {C.GREEN}{success}/{len(running)}{C.RESET} responding", end="")
    print(f"   {C.DIM}│{C.RESET}   {C.YELLOW}{changed}{C.RESET} endpoint(s) changed since last check" if changed else "")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  IP ROTATION
# ══════════════════════════════════════════════════════════════════════════════
def rotate_ips():
    clear_screen()
    draw_dashboard()
    show_location_list()
    print(f"\n  {C.DIM}Extended modules: use IDs 51+{C.RESET}")
    ids_input = input(
        f"\n  {C.YELLOW}Enter module IDs to rotate (e.g. 1,3,51): {C.RESET}"
    ).strip()
    try:
        ids     = [int(x.strip()) for x in ids_input.split(",")]
        targets = {i: ALL_LOCATIONS[i] for i in ids if i in ALL_LOCATIONS}
    except ValueError:
        print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
        pause()
        return
    if not targets:
        print(f"\n  {C.RED}✘  No valid IDs{C.RESET}")
        pause()
        return

    print(f"\n  {C.CYAN}⟳  Capturing current exit endpoints...{C.RESET}\n")
    old_ips = {}

    def _get_old_ip(nid, d):
        iso = d["iso"]
        if not node_is_running(iso):
            return nid, None
        ip = get_node_exit_ip(d["port"], timeout=12)
        print(f"  {_flag(iso)} {d['name']:<25}  {ip if ip else 'N/A':<20}")
        return nid, ip

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for nid, ip in pool.map(
                lambda item: _get_old_ip(item[0], item[1]), targets.items()):
            old_ips[nid] = ip

    print(f"\n  {C.YELLOW}⟳  Restarting modules for IP rotation...{C.RESET}\n")
    for nid, d in targets.items():
        iso  = d["iso"]
        name = d["name"].upper()
        if not node_is_installed(iso):
            print(f"  {C.DIM}  ─  {name} — not deployed{C.RESET}")
            continue
        print(f"  {C.YELLOW}⟳  Rotating {name}...{C.RESET}", end="", flush=True)
        run_cmd(f"systemctl restart tor@{iso}")
        time.sleep(0.5)
        print(f"\r  {C.GREEN}✔  {name} restarted{C.RESET}\033[K")

    print(f"\n  {C.YELLOW}⏳  Waiting for re-bootstrap (30s)...{C.RESET}")
    time.sleep(30)

    print(f"\n  {C.CYAN}⟳  Capturing new exit endpoints...{C.RESET}\n")
    print(f"  {'Location':<25}  {'Previous IP':<22}  {'New IP':<22}  Changed")
    print(f"  {'─' * 78}")
    new_ips = {}

    def _get_new_ip(nid, d):
        iso = d["iso"]
        if not node_is_running(iso):
            return nid, None
        ip      = get_node_exit_ip(d["port"], timeout=15)
        old     = old_ips.get(nid)
        new_ips[nid] = ip
        old_disp = f"{C.DIM}{(old or 'N/A'):<22}{C.RESET}"
        if ip:
            new_disp    = f"{C.GREEN}{ip:<22}{C.RESET}"
            changed_tag = (f"{C.GREEN}✔ YES{C.RESET}"
                           if (old and ip and old != ip)
                           else f"{C.YELLOW}○ SAME{C.RESET}")
        else:
            new_disp    = f"{C.RED}{'unreachable':<22}{C.RESET}"
            changed_tag = f"{C.RED}✘ TIMEOUT{C.RESET}"
        print(f"  {_flag(iso)} {d['name']:<23}  {old_disp}  {new_disp}  {changed_tag}")
        return nid, ip

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda item: _get_new_ip(item[0], item[1]), targets.items()))

    print(f"  {'─' * 78}")
    changed = sum(1 for nid in targets.keys()
                  if old_ips.get(nid) and new_ips.get(nid)
                  and old_ips[nid] != new_ips[nid])
    print(f"\n  {C.GREEN}{changed}/{len(targets)} endpoints rotated successfully{C.RESET}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  START / STOP / RESTART
# ══════════════════════════════════════════════════════════════════════════════
def _pick_targets_from_input(prompt="Enter module IDs"):
    ids_input = input(f"\n  {C.YELLOW}{prompt}: {C.RESET}").strip()
    try:
        ids = [int(x.strip()) for x in ids_input.split(",")]
        return {i: ALL_LOCATIONS[i] for i in ids if i in ALL_LOCATIONS}
    except ValueError:
        return {}

def start_nodes(targets: dict):
    print(f"\n  {C.YELLOW}▶  Starting modules...{C.RESET}\n")
    for nid, d in targets.items():
        iso  = d["iso"]
        name = d["name"].upper()
        if not node_is_installed(iso):
            print(f"  {C.DIM}  ─  {name} — not deployed{C.RESET}")
            continue
        print(f"  {C.GREEN}▶  Starting {name}...{C.RESET}", end="", flush=True)
        run_cmd(f"systemctl start tor@{iso}")
        time.sleep(0.3)
        if node_is_running(iso):
            print(f"\r  {C.GREEN}✔  {name} started{C.RESET}\033[K")
        else:
            print(f"\r  {C.RED}✘  {name} failed to start{C.RESET}\033[K")
    print(f"\n  {C.GREEN}✔  Done{C.RESET}")

def stop_nodes(targets: dict):
    print(f"\n  {C.YELLOW}■  Stopping modules...{C.RESET}\n")
    for nid, d in targets.items():
        iso  = d["iso"]
        name = d["name"].upper()
        if not node_is_installed(iso):
            print(f"  {C.DIM}  ─  {name} — not deployed{C.RESET}")
            continue
        print(f"  {C.RED}■  Stopping {name}...{C.RESET}", end="", flush=True)
        run_cmd(f"systemctl stop tor@{iso}")
        time.sleep(0.2)
        print(f"\r  {C.GREEN}✔  {name} stopped{C.RESET}\033[K")
    print(f"\n  {C.GREEN}✔  Done{C.RESET}")

def restart_nodes(targets: dict):
    print(f"\n  {C.YELLOW}⟳  Restarting modules...{C.RESET}\n")
    for nid, d in targets.items():
        iso  = d["iso"]
        name = d["name"].upper()
        if not node_is_installed(iso):
            print(f"  {C.DIM}  ─  {name} — not deployed{C.RESET}")
            continue
        print(f"  {C.YELLOW}⟳  Restarting {name}...{C.RESET}", end="", flush=True)
        run_cmd(f"systemctl restart tor@{iso}")
        time.sleep(0.3)
        if node_is_running(iso):
            print(f"\r  {C.GREEN}✔  {name} restarted{C.RESET}\033[K")
        else:
            print(f"\r  {C.RED}✘  {name} failed{C.RESET}\033[K")
    print(f"\n  {C.GREEN}✔  Done{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  REMOVE
# ══════════════════════════════════════════════════════════════════════════════
def _remove_targets(targets: dict) -> int:
    removed = 0
    for nid, d in targets.items():
        iso  = d["iso"]
        name = d["name"].upper()
        if not node_is_installed(iso):
            print(f"  {C.DIM}  ─  {name} — not deployed{C.RESET}")
            continue
        print(f"  {C.RED}  ─  Removing {name}...{C.RESET}", end="", flush=True)
        run_cmd(f"systemctl stop tor@{iso}")
        run_cmd(f"systemctl disable tor@{iso}")
        run_cmd(f"rm -rf {_INTERNAL_INSTANCE_DIR}/{iso}")
        run_cmd(f"rm -rf {_INTERNAL_VARLIB_DIR}/{iso}")
        print(f"\r  {C.GREEN}✔  {name} removed{C.RESET}\033[K")
        removed += 1
    return removed

def remove_all_nodes():
    installed = {nid: d for nid, d in ALL_LOCATIONS.items()
                 if node_is_installed(d["iso"])}
    if not installed:
        print(f"\n  {C.GREEN}✔  No deployed modules to remove.{C.RESET}")
        pause()
        return
    print(f"\n  {C.RED}⚠   Remove ALL {len(installed)} deployed module(s)?{C.RESET}")
    confirm = input(f"  {C.YELLOW}Type 'yes' to confirm: {C.RESET}").strip().lower()
    if confirm != "yes":
        print(f"  {C.DIM}Cancelled.{C.RESET}")
        pause()
        return
    print()
    removed = _remove_targets(installed)
    print(f"\n  {C.GREEN}✔  {removed} module(s) removed.{C.RESET}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  STATUS TABLE
# ══════════════════════════════════════════════════════════════════════════════
def show_status():
    draw_dashboard()
    screen_title("📡", "MODULE STATUS")
    running = running_isos()
    rows = []
    for nid, d in ALL_LOCATIONS.items():
        iso = d["iso"]
        n   = _exit_cache.get(iso, -1)
        ec  = f"{n}" if n >= 0 else "?"
        if not node_is_installed(iso):
            status = f"{C.DIM}○ not deployed{C.RESET}"
        elif iso in running:
            status = f"{C.GREEN}● running{C.RESET}"
        else:
            status = f"{C.RED}● stopped{C.RESET}"
        rows.append([f"{C.ACCENT}{nid}{C.RESET}", f"{_flag(iso)} {d['name']}",
                     f"{C.TEAL}{d['port']}{C.RESET}", ec, status])
    print("\n".join(table_lines(["#", "Location", "Port", "Relays", "Status"], rows, "><>><")))
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════
def health_check():
    draw_dashboard()
    screen_title("🩺", "CONNECTIVITY HEALTH CHECK", C.PURPLE)
    passed = failed = 0
    running = running_isos()
    for nid, d in ALL_LOCATIONS.items():
        iso, port = d["iso"], d["port"]
        if iso not in running:
            continue
        label = pad(f"{_flag(iso)} {clip(d['name'].upper(), 24)}", 30)
        print(f"  {C.WHITE}{label}{C.RESET} {C.DIM}:{C.TEAL}{port}{C.RESET}  ", end="", flush=True)
        t0 = time.time()
        r  = run_cmd(f"curl -s -m 10 --socks5-hostname 127.0.0.1:{port} "
                     f"https://www.google.com/generate_204")
        ms = int((time.time() - t0) * 1000)
        if r.returncode == 0:
            print(f"{C.GREEN}✔  {ms} ms{C.RESET}")
            passed += 1
        else:
            print(f"{C.RED}✘  FAIL{C.RESET}")
            failed += 1
    print()
    print(f"  {_divider('─', 40)}")
    print(f"  {C.GREEN}{passed} passed{C.RESET}   {C.DIM}│{C.RESET}   {C.RED}{failed} failed{C.RESET}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  IP LEAK & BLOCK CHECK
#  For every active Tor node:
#    - verifies the exit IP is genuinely a Tor exit (check.torproject.org)
#    - checks for DNS leak (ipleak.net JSON API)
#    - checks Spamhaus DNSBL for blacklisting
# ══════════════════════════════════════════════════════════════════════════════
def _tor_verify_exit(port: int, expected_ip: str) -> bool:
    """Verify the exit IP is a Tor exit node by calling check.torproject.org."""
    try:
        r = run_out(
            f"curl -s -m 12 --socks5-hostname 127.0.0.1:{port} "
            f"https://check.torproject.org/api/ip"
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout.strip())
            is_tor = bool(data.get("IsTor"))
            api_ip = data.get("IP", "")
            # Both flags must agree: API must say Tor AND IP must match what we saw
            return is_tor and (api_ip == expected_ip)
    except Exception:
        pass
    return False


def _dns_leak_check(port: int, exit_ip: str) -> tuple:
    """
    Return (leaked: bool, info: str).
    Compares DNS resolver IPs reported by ipleak.net against the Tor exit IP.
    If the DNS resolver IP matches the exit IP → traffic stayed inside Tor.
    If it returns a foreign DNS (e.g. 8.8.8.8) → DNS leak.
    """
    try:
        r = run_out(
            f"curl -s -m 12 --socks5-hostname 127.0.0.1:{port} "
            f"https://ipleak.net/json/"
        )
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout.strip())
            dns_ips = data.get("dns", {}).get("ip", []) or []
            if not dns_ips:
                return False, "no resolver info"
            # If exit IP itself appears in the DNS list → no leak
            if exit_ip in dns_ips:
                return False, "ok"
            # Otherwise a foreign resolver leaked through
            sample = dns_ips[0]
            return True, f"resolver {sample}"
    except Exception:
        pass
    # On any error, treat as unknown → don't flag as leak (avoid false positives)
    return False, "check failed"


def _blacklist_check(ip: str) -> tuple:
    """
    Return (listed: bool, source: str).
    Uses Spamhaus ZEN (combined CSS/SBL/XBL/PBL) via DNS lookup.
    Listed IPs resolve to 127.0.0.0/24 from the blocklist zone.
    """
    try:
        parts  = ip.split(".")
        rev_ip = ".".join(reversed(parts))
        r = run_out(f"dig +short +time=5 +tries=1 {rev_ip}.zen.spamhaus.org")
        if r.returncode == 0 and r.stdout.strip():
            out = r.stdout.strip()
            if "127.0.0" in out:
                code = out.splitlines()[0].strip()
                return True, f"Spamhaus ZEN ({code})"
        return False, ""
    except Exception:
        return False, ""


def check_ip_leak_and_block():
    """Scan all active Tor nodes for blacklist, DNS leak, and Tor verification."""
    draw_dashboard()
    screen_title("🔒", "IP LEAK & BLOCK CHECK")

    running = _running_locations()
    if not running:
        fail("No active modules to scan.")
        pause()
        return

    note(f"Scanning {len(running)} active module(s) — this may take ~30s.")
    note("  • Tor verification : check.torproject.org/api/ip")
    note("  • DNS leak check   : ipleak.net/json/")
    note("  • Blacklist check  : Spamhaus ZEN DNSBL")
    print()

    def _scan(nid, d):
        iso, port = d["iso"], d["port"]
        res = {
            "nid": nid, "iso": iso, "name": d["name"], "flag": _flag(iso),
            "ip": None, "is_tor": False, "dns_leak": False,
            "dns_info": "", "blacklisted": False, "bl_info": ""
        }
        ip = get_node_exit_ip(port, timeout=15)
        res["ip"] = ip
        if not ip:
            return res
        res["is_tor"] = _tor_verify_exit(port, ip)
        leaked, dns_info = _dns_leak_check(port, ip)
        res["dns_leak"], res["dns_info"] = leaked, dns_info
        listed, src = _blacklist_check(ip)
        res["blacklisted"], res["bl_info"] = listed, src
        return res

    # 3 network calls per node — cap workers to avoid rate limits
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        results = list(pool.map(lambda item: _scan(*item), running.items()))
    results.sort(key=lambda x: x["nid"])

    good, bad, none = f"{C.GREEN}✔{C.RESET}", f"{C.RED}✘{C.RESET}", f"{C.DIM}–{C.RESET}"
    rows = []
    for r in results:
        if r["ip"]:
            rows.append([f"{C.ACCENT}{r['nid']}{C.RESET}", f"{r['flag']} {r['name']}",
                         f"{C.TEAL}{r['ip']}{C.RESET}",
                         good if r["is_tor"] else bad,
                         bad if r["dns_leak"] else good,
                         f"{C.RED}✘ {r['bl_info']}{C.RESET}" if r["blacklisted"]
                         else f"{C.GREEN}clean{C.RESET}"])
        else:
            rows.append([f"{C.ACCENT}{r['nid']}{C.RESET}", f"{r['flag']} {r['name']}",
                         f"{C.RED}unreachable{C.RESET}", none, none, none])
    print("\n".join(table_lines(["#", "Location", "Exit IP", "Tor", "DNS", "Blacklist"],
                                rows, "><<^^<")))

    total    = len(results)
    with_ip  = sum(1 for r in results if r["ip"])
    tor_ok   = sum(1 for r in results if r["ip"] and r["is_tor"])
    no_leak  = sum(1 for r in results if r["ip"] and not r["dns_leak"])
    clean_bl = sum(1 for r in results if r["ip"] and not r["blacklisted"])

    def frac(n, bad_color):
        return f"{C.GREEN if n == with_ip else bad_color}{n}/{with_ip}{C.RESET}"

    summary = [
        f"  {C.PURPLE}{'Active modules':<20}{C.RESET}{C.WHITE}{with_ip}/{total}{C.RESET}",
        f"  {C.PURPLE}{'Tor verified exits':<20}{C.RESET}{frac(tor_ok, C.YELLOW)}",
        f"  {C.PURPLE}{'No DNS leak':<20}{C.RESET}{frac(no_leak, C.YELLOW)}",
        f"  {C.PURPLE}{'Blacklist clean':<20}{C.RESET}{frac(clean_bl, C.RED)}",
    ]
    print("\n" + "\n".join("  " + l for l in box_lines("SUMMARY", summary, 44)))

    leaks   = [r for r in results if r["ip"] and r["dns_leak"]]
    blocked = [r for r in results if r["blacklisted"]]
    not_tor = [r for r in results if r["ip"] and not r["is_tor"]]
    if leaks:
        print()
        warn("DNS leak detected on:")
        for r in leaks:
            print(f"      {r['flag']} {r['name']:<22}  {r['dns_info']}")
    if blocked:
        print()
        warn(f"{C.RED}Blacklisted IPs — consider rotating:{C.RESET}")
        for r in blocked:
            print(f"      {r['flag']} {r['name']:<22}  {r['ip']}  {r['bl_info']}")
    if not_tor:
        print()
        warn("Not verified as Tor exits:")
        for r in not_tor:
            print(f"      {r['flag']} {r['name']:<22}  {r['ip']}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-RESTART  (internal paths unchanged; service names remain compatible)
# ══════════════════════════════════════════════════════════════════════════════
AUTO_RESTART_SCRIPT  = "/usr/local/bin/tor-nodes-auto-restart.sh"
AUTO_RESTART_SERVICE = "/etc/systemd/system/tor-nodes-restart.service"
AUTO_RESTART_TIMER   = "/etc/systemd/system/tor-nodes-restart.timer"

def setup_auto_restart():
    print(f"\n  {C.YELLOW}⟳  Setting up hourly auto-restart via systemd timer...{C.RESET}")
    try:
        with open(AUTO_RESTART_SCRIPT, "w") as f:
            f.write(
                "#!/bin/bash\n"
                f"for d in {_INTERNAL_INSTANCE_DIR}/*/; do\n"
                "  iso=$(basename \"$d\")\n"
                "  systemctl restart \"tor@$iso\" 2>/dev/null\n"
                "done\n"
            )
        os.chmod(AUTO_RESTART_SCRIPT, 0o755)
        with open(AUTO_RESTART_SERVICE, "w") as f:
            f.write(
                "[Unit]\n"
                f"Description={BRAND_NAME} — Restart All Location Modules\n\n"
                "[Service]\n"
                "Type=oneshot\n"
                f"ExecStart={AUTO_RESTART_SCRIPT}\n"
            )
        with open(AUTO_RESTART_TIMER, "w") as f:
            f.write(
                "[Unit]\n"
                f"Description={BRAND_NAME} — Hourly Module Restart\n\n"
                "[Timer]\n"
                "OnBootSec=15min\n"
                "OnUnitActiveSec=1h\n"
                "Persistent=true\n\n"
                "[Install]\n"
                "WantedBy=timers.target\n"
            )
        run_cmd("systemctl daemon-reload")
        run_cmd("systemctl enable --now tor-nodes-restart.timer")
        r = run_out("systemctl is-enabled tor-nodes-restart.timer")
        if "enabled" in r.stdout:
            print(f"  {C.GREEN}✔  Hourly auto-restart ENABLED.{C.RESET}")
        else:
            print(f"  {C.RED}✘  Could not confirm timer status.{C.RESET}")
    except Exception as e:
        print(f"  {C.RED}✘  Setup failed: {e}{C.RESET}")
    pause()

def disable_auto_restart():
    print(f"\n  {C.YELLOW}⟳  Disabling hourly auto-restart...{C.RESET}")
    run_cmd("systemctl disable --now tor-nodes-restart.timer")
    for p in (AUTO_RESTART_TIMER, AUTO_RESTART_SERVICE, AUTO_RESTART_SCRIPT):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    run_cmd("systemctl daemon-reload")
    print(f"  {C.GREEN}✔  Auto-restart disabled.{C.RESET}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  CPU GUARDIAN  — auto-stop high-CPU locations for 1 hour
# ══════════════════════════════════════════════════════════════════════════════
CPU_GUARDIAN_THRESHOLD  = 80        # % CPU per tor@<iso> process
CPU_GUARDIAN_INTERVAL   = 300       # seconds between checks (5 min)
CPU_GUARDIAN_COOLDOWN   = 3600      # seconds to keep location stopped (1 hour)

_guardian_thread: threading.Thread = None
_guardian_active: bool             = False
_guardian_lock                     = threading.Lock()
_guardian_cooldowns: dict          = {}   # iso -> unix timestamp when to re-enable
_guardian_log: list                = []   # list of (iso, cpu_pct, stopped_at) strings


def _get_tor_cpu(iso: str) -> float:
    """Return summed CPU% for all processes matching tor@<iso>."""
    try:
        r = run_out(
            f"ps -C tor -o %cpu= --no-headers 2>/dev/null || "
            f"systemctl show tor@{iso} --property=MainPID --value 2>/dev/null"
        )
        # Use ps with cgroup/unit filter via systemd
        r2 = run_out(
            f"systemctl status tor@{iso} --no-pager -l 2>/dev/null | "
            f"grep 'Main PID' | awk '{{print $3}}'"
        )
        pid = r2.stdout.strip()
        if not pid or not pid.isdigit():
            return 0.0
        ps = run_out(f"ps -p {pid} -o %cpu= --no-headers 2>/dev/null")
        try:
            return float(ps.stdout.strip())
        except ValueError:
            return 0.0
    except Exception:
        return 0.0


def _guardian_loop():
    global _guardian_active
    while _guardian_active:
        now = time.time()
        # Re-enable locations whose cooldown has expired
        with _guardian_lock:
            to_resume = [iso for iso, until in list(_guardian_cooldowns.items())
                         if now >= until]
        for iso in to_resume:
            run_cmd(f"systemctl start tor@{iso}")
            with _guardian_lock:
                del _guardian_cooldowns[iso]

        # Check CPU for all running locations
        for nid, d in list(ALL_LOCATIONS.items()):
            iso  = d["iso"]
            name = d["name"].upper()
            if not node_is_installed(iso) or not node_is_running(iso):
                continue
            with _guardian_lock:
                if iso in _guardian_cooldowns:
                    continue   # already in cooldown
            cpu = _get_tor_cpu(iso)
            if cpu >= CPU_GUARDIAN_THRESHOLD:
                run_cmd(f"systemctl stop tor@{iso}")
                resume_at = time.time() + CPU_GUARDIAN_COOLDOWN
                with _guardian_lock:
                    _guardian_cooldowns[iso] = resume_at
                    ts = datetime.now().strftime("%H:%M:%S")
                    _guardian_log.append(
                        f"{ts}  {_flag(iso)} {name:<22}  CPU: {cpu:.1f}%  "
                        f"→ paused 1h"
                    )

        # Sleep in small increments so we can exit promptly
        for _ in range(CPU_GUARDIAN_INTERVAL * 10):
            if not _guardian_active:
                break
            time.sleep(0.1)


def start_cpu_guardian():
    global _guardian_thread, _guardian_active, CPU_GUARDIAN_THRESHOLD
    if _guardian_thread and _guardian_thread.is_alive():
        print(f"\n  {C.YELLOW}⚠  CPU Guardian is already running.{C.RESET}")
        pause()
        return
    print(f"\n  {C.CYAN}  CPU GUARDIAN — CONFIGURATION{C.RESET}\n")
    print(f"  {C.DIM}Current defaults:{C.RESET}")
    print(f"    Threshold : {C.WHITE}{CPU_GUARDIAN_THRESHOLD}%{C.RESET} CPU per location")
    print(f"    Interval  : {C.WHITE}{CPU_GUARDIAN_INTERVAL}s{C.RESET} (5 min)")
    print(f"    Cooldown  : {C.WHITE}{CPU_GUARDIAN_COOLDOWN}s{C.RESET} (1 hour)\n")
    thr_in = input(
        f"  {C.YELLOW}CPU threshold % [{CPU_GUARDIAN_THRESHOLD}]: {C.RESET}"
    ).strip()
    if thr_in.isdigit():
        CPU_GUARDIAN_THRESHOLD = max(1, min(99, int(thr_in)))
    _guardian_active = True
    _guardian_thread = threading.Thread(target=_guardian_loop, daemon=True)
    _guardian_thread.start()
    print(f"\n  {C.GREEN}✔  CPU Guardian started — threshold: "
          f"{CPU_GUARDIAN_THRESHOLD}%  │  check every "
          f"{CPU_GUARDIAN_INTERVAL // 60} min  │  pause 1h{C.RESET}")
    pause()


def stop_cpu_guardian():
    global _guardian_active
    if not (_guardian_thread and _guardian_thread.is_alive()):
        print(f"\n  {C.DIM}CPU Guardian is not running.{C.RESET}")
        pause()
        return
    _guardian_active = False
    print(f"\n  {C.GREEN}✔  CPU Guardian stopped.{C.RESET}")
    # Re-enable anything still in cooldown
    with _guardian_lock:
        paused = list(_guardian_cooldowns.keys())
    for iso in paused:
        run_cmd(f"systemctl start tor@{iso}")
    with _guardian_lock:
        _guardian_cooldowns.clear()
    if paused:
        print(f"  {C.DIM}Re-enabled {len(paused)} paused location(s).{C.RESET}")
    pause()


def show_guardian_status():
    clear_screen()
    draw_dashboard()
    running = _guardian_thread and _guardian_thread.is_alive()
    state   = (f"{C.GREEN}● RUNNING{C.RESET}" if running
               else f"{C.RED}○ STOPPED{C.RESET}")
    print(f"\n  {C.CYAN}🛡  CPU GUARDIAN STATUS{C.RESET}  —  {state}\n")
    if running:
        print(f"  Threshold : {C.WHITE}{CPU_GUARDIAN_THRESHOLD}%{C.RESET}")
        print(f"  Interval  : {C.WHITE}{CPU_GUARDIAN_INTERVAL // 60} min{C.RESET}")
        print(f"  Cooldown  : {C.WHITE}{CPU_GUARDIAN_COOLDOWN // 60} min{C.RESET}\n")

    with _guardian_lock:
        cooldowns = dict(_guardian_cooldowns)
        log       = list(_guardian_log)

    if cooldowns:
        print(f"  {C.YELLOW}⏸  Currently paused locations:{C.RESET}")
        now = time.time()
        for iso, until in cooldowns.items():
            remaining = max(0, int(until - now))
            mins, secs = divmod(remaining, 60)
            loc = next((d for d in ALL_LOCATIONS.values() if d["iso"] == iso), None)
            name = loc["name"].upper() if loc else iso.upper()
            print(f"    {_flag(iso)} {name:<22}  resumes in {mins}m {secs}s")
    else:
        print(f"  {C.GREEN}✔  No locations currently paused.{C.RESET}")

    if log:
        print(f"\n  {C.DIM}Recent guardian events (last {min(len(log), 20)}):{C.RESET}")
        for entry in log[-20:]:
            print(f"  {C.DIM}{entry}{C.RESET}")
    pause()


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGNOSE
# ══════════════════════════════════════════════════════════════════════════════
def diagnose_node():
    clear_screen()
    draw_dashboard()
    show_location_list()
    print(f"\n  {C.DIM}For extended modules (ID 51+) enter the ID directly{C.RESET}")
    id_input = input(
        f"\n  {C.YELLOW}Enter ONE module ID to diagnose: {C.RESET}"
    ).strip()
    try:
        nid = int(id_input)
        d   = ALL_LOCATIONS.get(nid)
        if not d:
            raise KeyError
    except (ValueError, KeyError):
        print(f"\n  {C.RED}✘  Invalid ID{C.RESET}")
        pause()
        return

    iso, port, name = d["iso"], d["port"], d["name"].upper()
    flag = _flag(iso)
    print(f"\n  {C.CYAN}{'═' * 66}{C.RESET}")
    print(f"  {C.CYAN}  DIAGNOSING {flag} {name} ({iso.upper()})  —  port {port}{C.RESET}")
    print(f"  {C.CYAN}{'═' * 66}{C.RESET}\n")

    print(f"  {C.DIM}[1/5] Checking relay density for this location...{C.RESET}")
    _exit_cache.pop(iso, None)
    count = get_exit_node_count(iso)
    if count < 0:
        print(f"    {C.RED}✘  Could not retrieve relay data{C.RESET}")
    else:
        color = (C.GREEN if count >= LOW_EXIT_NODES
                 else (C.YELLOW if count >= MIN_EXIT_NODES else C.RED))
        print(f"    {color}{count} relay(s) available for this location{C.RESET}")
        if count < MIN_EXIT_NODES:
            print(f"    {C.YELLOW}⚠  Very low relay count — "
                  f"strict routing may not find a usable circuit.{C.RESET}")

    print(f"\n  {C.DIM}[2/5] Checking deployment state...{C.RESET}")
    if not node_is_installed(iso):
        print(f"    {C.YELLOW}  Creating instance...{C.RESET}")
        run_cmd(f"tor-instance-create {iso}")
    print(f"    {C.GREEN}✔  Instance directory present{C.RESET}")

    print(f"\n  {C.DIM}[3/5] Attempting bootstrap (relaxed mode, 180s timeout)...{C.RESET}")
    write_torrc(iso, port, strict=False)
    pct = _wait_bootstrap(iso, port, name, timeout=180, attempt=1, verbose=True)
    print()

    if pct < 100:
        print(f"\n  {C.RED}✘  Bootstrap stalled at {pct}%{C.RESET}")
        log = run_out(f"journalctl -u tor@{iso} -n 15 --no-pager")
        for line in log.stdout.strip().splitlines()[-15:]:
            print(f"    {C.DIM}{line}{C.RESET}")
        pause()
        return

    print(f"  {C.DIM}[4/5] Testing outbound connectivity...{C.RESET}")
    conn_ok = False
    for attempt in range(1, 4):
        r = run_cmd(
            f"curl -s -m 30 --socks5-hostname 127.0.0.1:{port} "
            f"https://www.google.com/generate_204")
        if r.returncode == 0:
            conn_ok = True
            print(f"    {C.GREEN}✔  Connectivity OK{C.RESET} "
                  f"{C.DIM}(attempt {attempt}){C.RESET}")
            break
        else:
            print(f"    {C.YELLOW}⚠  Attempt {attempt}/3 failed{C.RESET}")
            time.sleep(5)
    if not conn_ok:
        print(f"    {C.RED}✘  Connection failed after 3 attempts{C.RESET}")

    print(f"  {C.DIM}[5/5] Fetching exit endpoint + stability check...{C.RESET}")
    ip = None
    for attempt in range(1, 4):
        ip = get_node_exit_ip(port, timeout=20)
        if ip:
            break
        time.sleep(5)
    stable = _check_exit_stable(port) if ip else False
    if ip:
        tag = "stable" if stable else "UNSTABLE"
        col = C.GREEN if stable else C.YELLOW
        print(f"    {col}✔  Exit endpoint: {ip}  ({tag}){C.RESET}")
    else:
        print(f"    {C.RED}✘  Could not determine exit endpoint{C.RESET}")

    print(f"\n  {_divider('─', 66)}")
    if conn_ok and ip and stable:
        write_torrc(iso, port, strict=True)
        run_cmd(f"systemctl reload tor@{iso}")
        print(f"  {C.GREEN}✔  {flag} {name} is healthy and routing correctly.{C.RESET}")
    else:
        print(f"  {C.YELLOW}⚠  {flag} {name} left in RELAXED routing mode.{C.RESET}")
    print(f"  {_divider('─', 66)}")
    pause()

# ══════════════════════════════════════════════════════════════════════════════
#  DEPLOYMENT REPORT
# ══════════════════════════════════════════════════════════════════════════════
def print_report():
    elapsed    = int((datetime.now() - SESSION_START).total_seconds())
    mins, secs = divmod(elapsed, 60)
    good, bad  = report_data["SUCCESS"], report_data["FAILED"]
    total      = len(good) + len(bad)
    pct        = int(len(good) / total * 100) if total else 0
    w          = term_width()

    rows = [f"  {C.DIM}Session time: {mins}m {secs}s{C.RESET}"]
    if report_data["WARNED"]:
        rows += ["", f"  {C.YELLOW}⚠  Warnings{C.RESET}"]
        rows += [f"     {C.YELLOW}⚠{C.RESET}  {n}" for n in report_data["WARNED"]]
    if good:
        retried = set(report_data["RETRIED"])
        rows += ["", f"  {C.GREEN}✔  Deployed ×{len(good)}{C.RESET}"]
        for n in good:
            tag = f" {C.YELLOW}(retry){C.RESET}" if any(n.startswith(r) for r in retried) else ""
            rows.append(f"     {C.GREEN}✔{C.RESET}  {n}{tag}")
    if bad:
        rows += ["", f"  {C.RED}✘  Failed ×{len(bad)}{C.RESET}"]
        rows += [f"     {C.RED}✘{C.RESET}  {n}" for n in bad]
    if total:
        color = C.GREEN if pct >= 80 else (C.YELLOW if pct >= 50 else C.RED)
        rows += ["", f"  {_progress_bar(pct, w - 30)}  {color}success rate{C.RESET}"]
    if good:
        rows += ["─", f"  {C.DIM}Deployed location modules{C.RESET}"]
        for entry in good:
            # entry format: "NAME (:PORT) → IP"
            iso_guess = next((d["iso"] for d in ALL_LOCATIONS.values()
                              if d["name"].upper() in entry), "")
            flag       = _flag(iso_guess) if iso_guess else "🌐"
            name_port, _, exit_ip = entry.partition(" → ")
            alias      = _display_node_name(iso_guess) if iso_guess else name_port.strip()
            rows.append(f"  {flag}  {C.WHITE}{pad(alias, 18)}{C.RESET}  "
                        f"{C.TEAL}{pad(exit_ip.strip() or '—', 18)}{C.RESET}  {C.GREEN}✔ Ready{C.RESET}")
    print()
    print("\n".join("  " + l for l in box_lines(f"DEPLOYMENT REPORT · {BRAND_NAME}", rows, w)))

# ══════════════════════════════════════════════════════════════════════════════
#  PANEL INTEGRATION  (EZ-Panel — 3X-UI / PasarGuard)
#  Clones an existing panel inbound per location and routes it through the
#  matching local EOTor SOCKS5 port:  panel inbound 3031+ ➔ SOCKS 9080+.
# ══════════════════════════════════════════════════════════════════════════════
PANEL_XUI_DB          = "/etc/x-ui/x-ui.db"
PANEL_XUI_TOKEN       = "/etc/x-ui/ez_token.json"
PANEL_PG_CREDS        = os.path.expanduser("~/.pg_relay_creds")
PANEL_XUI_PATHS       = [PANEL_XUI_DB, "/usr/local/x-ui/x-ui"]
PANEL_PG_PATHS        = ["/opt/pasarguard", "/opt/PasarGuard", "/etc/pasarguard", "/etc/PasarGuard"]
PANEL_MARZBAN_PATHS   = ["/opt/marzban", "/etc/marzban", "/usr/local/bin/marzban"]
PANEL_IN_PORT_BASE    = 3030            # panel inbound port = base + module id
PANEL_OUTBOUND_PREFIX = "EoTor"
PANEL_LEGACY_PREFIXES = ("T.Sin",)      # tags written by older EZ-Panel releases
PANEL_TEST_URL        = "https://www.google.com/generate_204"


class PanelError(Exception):
    """A panel problem the user can act on; shown as a message, never a traceback."""


def _requests():
    try:
        import requests
        import urllib3
    except ImportError:
        raise PanelError("Python package 'requests' is missing — run: "
                         "pip3 install --break-system-packages requests")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return requests


def panel_countries():
    """The 50 primary locations with their panel-side inbound port."""
    return [{"id": nid, "code": d["iso"], "name": d["name"], "flag": _flag(d["iso"]),
             "out_port": d["port"], "in_port": PANEL_IN_PORT_BASE + nid}
            for nid, d in LOCATIONS.items()]


def panel_inbound_tag(c) -> str:
    return f"{c['flag']} {c['name']}"


def panel_outbound_tag(c, prefix=PANEL_OUTBOUND_PREFIX) -> str:
    return f"{prefix}-{c['code'].upper()}"


def panel_outbound_tags(c) -> list:
    return [panel_outbound_tag(c, p) for p in (PANEL_OUTBOUND_PREFIX, *PANEL_LEGACY_PREFIXES)]


def deployed_panel_countries():
    return [c for c in panel_countries() if node_is_installed(c["code"])]


def detect_panels():
    """[(name, found)] for every panel EZ-Panel knows about."""
    def found(paths):
        return any(os.path.exists(p) for p in paths)
    return [("3X-UI", found(PANEL_XUI_PATHS)),
            ("PasarGuard", found(PANEL_PG_PATHS)),
            ("Marzban", found(PANEL_MARZBAN_PATHS))]


def parse_selection(text, limit):
    """'1,3-5' → [1, 3, 4, 5], keeping only values within 1..limit."""
    chosen = set()
    for part in text.replace(" ", "").split(","):
        try:
            if "-" in part:
                lo, hi = (int(x) for x in part.split("-", 1))
                if 1 <= lo <= limit and 1 <= hi <= limit:
                    chosen.update(range(min(lo, hi), max(lo, hi) + 1))
            elif 1 <= int(part) <= limit:
                chosen.add(int(part))
        except ValueError:
            continue
    return sorted(chosen)


def _json_field(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


# ── 3X-UI ─────────────────────────────────────────────────────────────────────
class ThreeXUIClient:
    def __init__(self, base_url, api_token=None):
        requests = _requests()
        self.base_url     = base_url.rstrip("/")
        self.api_base_url = self.base_url[:-6] if self.base_url.endswith("/panel") else self.base_url
        self.last_error   = ""
        self.session      = requests.Session()
        self.session.trust_env = False
        self.session.verify    = False
        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}",
                                         "Accept": "application/json"})

    def _call(self, method, path, **kw):
        """Returns decoded JSON (dict) on HTTP 200 with success, else None and sets last_error."""
        try:
            r = self.session.request(method, f"{self.api_base_url}{path}", timeout=10, **kw)
            data = r.json()
        except Exception as e:
            self.last_error = str(e)
            return None
        if r.status_code == 200 and data.get("success"):
            return data
        self.last_error = f"HTTP {r.status_code}: {data.get('msg') or r.text[:100]}"
        return None

    def test_connection(self):
        url = f"{self.api_base_url}/panel/api/inbounds/list"
        last_error = ""
        for method in ("POST", "GET"):
            try:
                r = self.session.request(method, url, timeout=10)
                if r.status_code != 200:
                    last_error = f"HTTP {r.status_code}: {r.text[:100]}"
                    continue
                try:
                    result = r.json()
                except ValueError:
                    return True, None
                if result.get("success") or "obj" in result:
                    return True, None
                last_error = f"Status 200 but success=False. Msg: {result.get('msg')}"
            except Exception as e:
                last_error = str(e)
        return False, last_error

    def get_inbounds(self):
        data = self._call("POST", "/panel/api/inbounds/list") or self._call("GET", "/panel/api/inbounds/list")
        return (True, data.get("obj") or []) if data else (False, [])

    def create_inbound(self, payload):
        data = self._call("POST", "/panel/api/inbounds/add", json=payload)
        return (True, data) if data else (False, None)

    def delete_inbound(self, inbound_id):
        return bool(self._call("POST", f"/panel/api/inbounds/del/{inbound_id}"))

    def get_xray_setting(self):
        data = self._call("POST", "/panel/api/xray/")
        return (True, data.get("obj") or {}) if data else (False, None)

    def update_xray_setting(self, xray_setting_str, outbound_test_url=PANEL_TEST_URL):
        return bool(self._call("POST", "/panel/api/xray/update",
                               data={"xraySetting": xray_setting_str,
                                     "outboundTestUrl": outbound_test_url}))

    def _xray_config(self):
        success, settings = self.get_xray_setting()
        if not success or not settings:
            return None, PANEL_TEST_URL
        settings = _json_field(settings)
        config   = _json_field(settings.get("xraySetting", "{}"))
        return config, settings.get("outboundTestUrl", PANEL_TEST_URL)

    def _edit_xray(self, mutate):
        """Read-modify-write of the xray config. `mutate` returns True when it changed anything."""
        try:
            config, test_url = self._xray_config()
            if config is None:
                return False
            if not mutate(config):
                return False
            return self.update_xray_setting(json.dumps(config, indent=2), test_url)
        except Exception as e:
            self.last_error = str(e)
            return False

    def add_permanent_outbound(self, outbound):
        def mutate(cfg):
            cfg["outbounds"] = [o for o in cfg.get("outbounds", []) if o.get("tag") != outbound.get("tag")]
            cfg["outbounds"].append(outbound)
            return True
        return self._edit_xray(mutate)

    def add_routing_rule(self, rule):
        def mutate(cfg):
            rules = cfg.setdefault("routing", {}).setdefault("rules", [])
            tags  = rule.get("inboundTag", [])
            cfg["routing"]["rules"] = [r for r in rules if not any(t in r.get("inboundTag", []) for t in tags)]
            cfg["routing"]["rules"].append(rule)
            return True
        return self._edit_xray(mutate)

    def delete_outbound_and_routing(self, outbound_tags, inbound_tag):
        """True only if something was actually removed."""
        def mutate(cfg):
            outs, rules = cfg.get("outbounds", []), cfg.get("routing", {}).get("rules", [])
            keep_o = [o for o in outs if o.get("tag") not in outbound_tags]
            keep_r = [r for r in rules if inbound_tag not in r.get("inboundTag", [])
                      and r.get("outboundTag") not in outbound_tags]
            if len(keep_o) == len(outs) and len(keep_r) == len(rules):
                return False
            if "outbounds" in cfg:
                cfg["outbounds"] = keep_o
            if "rules" in cfg.get("routing", {}):
                cfg["routing"]["rules"] = keep_r
            return True
        return self._edit_xray(mutate)

    def restart_xray_service(self):
        return bool(self._call("POST", "/panel/api/server/restartXrayService"))


def xui_generate_api_token():
    """Create (or reuse) the 'EZ-Panel-Auto' API token in the local x-ui database."""
    if not os.path.exists(PANEL_XUI_DB):
        raise PanelError(f"Database not found at {PANEL_XUI_DB} — is 3X-UI installed?")
    requests = _requests()
    try:
        conn   = sqlite3.connect(PANEL_XUI_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings WHERE key IN ('webPort', 'webBasePath')")
        port, path = "54321", ""
        for key, value in cursor.fetchall():
            if key == "webPort":
                port = value
            elif key == "webBasePath":
                path = value.strip("/")
        suffix     = f"{path}" if path else ""
        candidates = [f"http://127.0.0.1:{port}/{suffix}", f"https://127.0.0.1:{port}/{suffix}"]
        base_url   = candidates[0]
        probe = requests.Session()
        probe.trust_env, probe.verify = False, False
        for candidate in candidates:
            try:
                probe.get(f"{candidate.rstrip('/')}/panel/api/inbounds/list", timeout=5)
                base_url = candidate
                break
            except Exception:
                continue
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('api_tokens', 'api_token')")
        table_row = cursor.fetchone()
        if not table_row:
            conn.close()
            raise PanelError("API tokens table not found in the 3X-UI database.")
        table = table_row[0]
        saved_plain = saved_hash = None
        if os.path.exists(PANEL_XUI_TOKEN):
            try:
                with open(PANEL_XUI_TOKEN) as f:
                    saved = json.load(f)
                saved_plain, saved_hash = saved.get("plaintext_token"), saved.get("hashed_token")
            except (OSError, ValueError):
                pass
        if saved_plain and saved_hash:
            cursor.execute(f"SELECT token FROM {table} WHERE name = ? AND enabled = 1", ("EZ-Panel-Auto",))
            row = cursor.fetchone()
            if row and row[0] == saved_hash:
                conn.close()
                return base_url, saved_plain
        plain  = "3xui_" + secrets.token_hex(20)
        hashed = hashlib.sha256(plain.encode()).hexdigest()
        cursor.execute(f"DELETE FROM {table} WHERE name = ?", ("EZ-Panel-Auto",))
        cursor.execute(f"INSERT INTO {table} (name, token, enabled, created_at) VALUES (?, ?, ?, ?)",
                       ("EZ-Panel-Auto", hashed, 1, int(time.time() * 1000)))
        conn.commit()
        conn.close()
        _write_private(PANEL_XUI_TOKEN, json.dumps({"plaintext_token": plain, "hashed_token": hashed}))
        return base_url, plain
    except sqlite3.Error as e:
        raise PanelError(f"3X-UI database error: {e}")


def _write_private(path, text):
    """Write a secrets file readable by its owner only (never world-readable, not even briefly)."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(text)
        return True
    except OSError:
        return False


class XUIBackend:
    name = "3X-UI"

    def __init__(self, client):
        self.client = client

    def sources(self):
        success, inbounds = self.client.get_inbounds()
        return inbounds if success else []

    def configured_ports(self):
        return {ib.get("port") for ib in self.sources()}

    def configured_codes(self):
        config, _ = self.client._xray_config()
        if not config:
            return set()
        outbound_tags = {o.get("tag") for o in config.get("outbounds", [])}
        rule_targets  = {r.get("outboundTag") for r in config.get("routing", {}).get("rules", [])}
        return {c["code"] for c in panel_countries()
                if any(t in outbound_tags and t in rule_targets for t in panel_outbound_tags(c))}

    def is_configured(self, c):
        return c["code"] in self.configured_codes()

    def pick_source(self):
        inbounds = self.sources()
        if not inbounds:
            fail("No inbounds found to clone from.")
            pause()
            return None
        screen_title("📌", "SELECT INBOUND TO CLONE")
        rows = [[f"{C.ACCENT}{i}{C.RESET}", f"{C.TEAL}{ib.get('port', '?')}{C.RESET}",
                 str(ib.get("protocol", "?")), str(ib.get("remark") or "—")]
                for i, ib in enumerate(inbounds, 1)]
        print("\n".join(table_lines(["#", "Port", "Protocol", "Remark"], rows, ">>><")))
        note("\n0 = go back")
        while True:
            value = ask("Inbound port to clone from")
            if value in ("0", ""):
                return None
            try:
                match = next((ib for ib in inbounds if ib.get("port") == int(value)), None)
            except ValueError:
                match = None
            if match:
                return match
            fail("No inbound with that port.")

    def describe(self, source):
        return f"inbound port {source.get('port')}"

    def create(self, source, c):
        cl = self.client
        inbound_tag, outbound_tag = panel_inbound_tag(c), panel_outbound_tag(c)
        success, current = cl.get_inbounds()
        for ib in (current if success else []):
            if ib.get("port") == c["in_port"] or ib.get("tag") == inbound_tag:
                cl.delete_inbound(ib.get("id"))
        created, _ = cl.create_inbound({
            "enable": True, "remark": inbound_tag, "listen": source.get("listen", ""),
            "port": c["in_port"], "protocol": source.get("protocol"), "expiryTime": 0, "total": 0,
            "tag": inbound_tag,
            "settings": _json_field(source.get("settings")),
            "streamSettings": _json_field(source.get("streamSettings")),
            "sniffing": _json_field(source.get("sniffing")),
        })
        if not created:
            return False, f"inbound create failed on port {c['in_port']} ({cl.last_error})"
        if not cl.add_permanent_outbound({
                "protocol": "socks", "tag": outbound_tag,
                "settings": {"servers": [{"address": "127.0.0.1", "port": c["out_port"]}]}}):
            return False, f"SOCKS outbound failed ({cl.last_error})"
        if not cl.add_routing_rule({"type": "field", "inboundTag": [inbound_tag],
                                    "outboundTag": outbound_tag}):
            return False, f"routing rule failed ({cl.last_error})"
        return True, f"in {c['in_port']} ➔ out {c['out_port']}"

    def remove(self, c):
        cl, inbound_tag = self.client, panel_inbound_tag(c)
        success, inbounds = cl.get_inbounds()
        inbound_deleted = False
        for ib in (inbounds if success else []):
            if ib.get("port") == c["in_port"] or ib.get("tag") == inbound_tag:
                inbound_deleted = cl.delete_inbound(ib.get("id")) or inbound_deleted
        xray_cleaned = cl.delete_outbound_and_routing(panel_outbound_tags(c), inbound_tag)
        return inbound_deleted or xray_cleaned, ""

    def finalize(self):
        info("Restarting Xray core…")
        if self.client.restart_xray_service():
            ok("Xray restarted.")
            return True
        warn("Saved, but the automatic Xray restart failed — restart it from the panel.")
        return False


# ── PasarGuard ────────────────────────────────────────────────────────────────
class PasarGuardAPI:
    def __init__(self, base_url, username, password, core_id=1):
        self.base_url   = base_url.rstrip("/")
        self.username   = username
        self.password   = password
        self.core_id    = core_id
        self.last_error = ""
        self.headers    = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def _request(self, method, path, **kw):
        requests = _requests()
        try:
            r = requests.request(method, f"{self.base_url}{path}", headers=self.headers,
                                 timeout=15, **kw)
        except requests.exceptions.ConnectionError:
            self.last_error = "Cannot connect to the panel."
            return None
        except Exception as e:
            self.last_error = str(e)
            return None
        if r.status_code in (200, 201, 204):
            return r
        self.last_error = f"HTTP {r.status_code}: {r.text[:200]}"
        return None

    def login(self):
        r = self._request("POST", "/api/admin/token",
                          data={"username": self.username, "password": self.password})
        if r is None:
            if "401" in self.last_error:
                self.last_error = "Invalid username or password."
            return False
        data = r.json()
        self.headers.update({"Authorization": f"{data.get('token_type', 'Bearer')} {data.get('access_token')}",
                             "Content-Type": "application/json"})
        return True

    def get_core_config(self):
        r = self._request("GET", f"/api/core/{self.core_id}")
        if r is None:
            return None
        data = r.json()
        return data.get("config", data)

    def save_core_config(self, config, restart_nodes=True):
        return self._request("PUT", f"/api/core/{self.core_id}", json={"config": config},
                             params={"restart_nodes": str(restart_nodes).lower()}) is not None

    def list_inbounds_raw(self):
        config = self.get_core_config()
        return config.get("inbounds", []) if config else []

    def get_hosts(self):
        r = self._request("GET", "/api/hosts")
        return r.json() if r is not None else None

    def save_hosts(self, hosts):
        return self._request("PUT", "/api/hosts", json=hosts) is not None

    def delete_host(self, host_id):
        return self._request("DELETE", f"/api/host/{host_id}") is not None

    @staticmethod
    def flatten_hosts(data):
        flat = []
        if isinstance(data, dict):
            for group_tag, hosts in data.items():
                if isinstance(hosts, list):
                    flat += [(group_tag, h) for h in hosts]
                elif isinstance(hosts, dict):
                    flat.append((group_tag, hosts))
        elif isinstance(data, list):
            flat = [(h.get("inbound_tag") or h.get("tag") or h.get("inboundTag") or "—", h) for h in data]
        return flat

    def clone_host(self, source_index, target_inbound_tag, new_remark):
        raw = self.get_hosts()
        if raw is None:
            return False
        data = copy.deepcopy(raw)
        flat = self.flatten_hosts(data)
        if not 1 <= source_index <= len(flat):
            self.last_error = "Invalid host index."
            return False
        new_host = copy.deepcopy(flat[source_index - 1][1])
        new_host.pop("id", None)
        new_host["remark"]      = new_remark
        new_host["inbound_tag"] = target_inbound_tag
        if "name" in new_host:
            new_host["name"] = new_remark
        if isinstance(data, list):
            data[:] = [h for h in data if not (h.get("inbound_tag") == target_inbound_tag
                                               and h.get("remark") == new_remark)]
            data.append(new_host)
        elif isinstance(data, dict):
            group = data.setdefault(target_inbound_tag, [])
            group = group if isinstance(group, list) else [group]
            data[target_inbound_tag] = [h for h in group if h.get("remark") != new_remark] + [new_host]
        else:
            self.last_error = "Unexpected /api/hosts format."
            return False
        return self.save_hosts(data)

    def remove_relay(self, inbound_tag):
        """Drop inbound/outbound/routing for `inbound_tag`, then its hosts. Returns (removed_anything, detail)."""
        config = self.get_core_config()
        if config is None:
            return False, self.last_error
        counts = {}
        for key in ("inbounds", "outbounds"):
            before = config.get(key, [])
            config[key] = [x for x in before if x.get("tag") != inbound_tag]
            counts[key] = len(before) - len(config[key])
        routing = config.setdefault("routing", {})
        before  = routing.get("rules", [])
        routing["rules"] = [r for r in before if not (inbound_tag in r.get("inboundTag", [])
                                                      or r.get("outboundTag") == inbound_tag)]
        counts["rules"] = len(before) - len(routing["rules"])
        if sum(counts.values()) and not self.save_core_config(config):
            return False, self.last_error
        removed_hosts = 0
        raw = self.get_hosts()
        for group_tag, h in (self.flatten_hosts(raw) if raw is not None else []):
            if (h.get("inbound_tag") == inbound_tag or group_tag == inbound_tag) and h.get("id") is not None:
                removed_hosts += self.delete_host(h["id"])
        return bool(sum(counts.values()) or removed_hosts), ""


def _parse_env_file(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _detect_pg_url():
    for base in PANEL_PG_PATHS:
        path = os.path.join(base, ".env")
        if not os.path.isfile(path):
            continue
        try:
            env      = _parse_env_file(path)
            host     = env.get("UVICORN_HOST", "127.0.0.1").strip()
            port     = env.get("UVICORN_PORT", "8000").strip()
            certfile = env.get("UVICORN_SSL_CERTFILE", "").strip()
            connect  = "127.0.0.1" if host in ("0.0.0.0", "") else host
            domain   = next((part for part in certfile.replace("\\", "/").split("/")
                             if "." in part and not part.endswith(".pem")), "") if certfile else ""
            return f"{'https' if certfile else 'http'}://{domain or connect}:{port}"
        except OSError as e:
            warn(f"Could not parse {path}: {e}")
    return ""


def _pg_credentials():
    import getpass
    if os.path.isfile(PANEL_PG_CREDS):
        try:
            env = _parse_env_file(PANEL_PG_CREDS)
            if env.get("URL") and env.get("USER") and env.get("PASS"):
                info(f"Using saved credentials  {C.DIM}{env['URL']} · {env['USER']}{C.RESET}")
                return env["URL"], env["USER"], env["PASS"]
        except OSError:
            pass
    detected = _detect_pg_url()
    if detected and confirm(f"Is this your PasarGuard address? {detected}"):
        url = detected
    else:
        url = ask("Panel URL (e.g. https://panel.example.com:8000)")
    user = ask("Admin username")
    print(f"\n  {C.ACCENT}❯{C.RESET} {C.YELLOW}Admin password:{C.RESET} ", end="", flush=True)
    password = getpass.getpass("")
    if _write_private(PANEL_PG_CREDS, f"URL={url}\nUSER={user}\nPASS={password}\n"):
        note(f"Credentials saved to {PANEL_PG_CREDS} (owner-only).")
    return url, user, password


class PGBackend:
    name = "PasarGuard"

    def __init__(self, api):
        self.api = api

    def sources(self):
        return self.api.list_inbounds_raw()

    def configured_ports(self):
        return {ib.get("port") for ib in self.sources() if ib.get("port") is not None}

    def configured_codes(self):
        config = self.api.get_core_config()
        if not config:
            return set()
        ib_tags = {x.get("tag") for x in config.get("inbounds", [])}
        ob_tags = {x.get("tag") for x in config.get("outbounds", [])}
        return {c["code"] for c in panel_countries()
                if panel_inbound_tag(c) in ib_tags and panel_inbound_tag(c) in ob_tags}

    def is_configured(self, c):
        return c["code"] in self.configured_codes()

    def pick_source(self):
        inbounds = self.sources()
        if not inbounds:
            fail(f"No inbounds available ({self.api.last_error or 'empty core config'}).")
            pause()
            return None
        screen_title("📌", "SELECT INBOUND TO CLONE")
        rows = []
        for i, ib in enumerate(inbounds, 1):
            ss = ib.get("streamSettings", {}) or {}
            rows.append([f"{C.ACCENT}{i}{C.RESET}", f"{C.TEAL}{ib.get('port', '?')}{C.RESET}",
                         str(ib.get("protocol", "?")), str(ss.get("network", "tcp")),
                         str(ss.get("security", "none")), str(ib.get("tag", "—"))])
        print("\n".join(table_lines(["#", "Port", "Protocol", "Network", "Security", "Tag"], rows, ">>><<<")))
        note("\n0 = go back")
        inbound = None
        while inbound is None:
            value = ask("Inbound #")
            if value in ("0", ""):
                return None
            if value.isdigit() and 1 <= int(value) <= len(inbounds):
                inbound = inbounds[int(value) - 1]
            else:
                fail(f"Enter a number from 1 to {len(inbounds)}.")

        flat = PasarGuardAPI.flatten_hosts(self.api.get_hosts())
        if not flat:
            fail("No hosts found to clone from.")
            pause()
            return None
        screen_title("📌", "SELECT HOST TO CLONE")
        rows = [[f"{C.ACCENT}{i}{C.RESET}", str(tag), str(h.get("remark") or h.get("name") or "—"),
                 str(h.get("address", "—")), str(h.get("port", "?"))]
                for i, (tag, h) in enumerate(flat, 1)]
        print("\n".join(table_lines(["#", "Inbound tag", "Remark", "Address", "Port"], rows, "><<<>")))
        note("\n0 = go back")
        while True:
            value = ask("Host #")
            if value in ("0", ""):
                return None
            if value.isdigit() and 1 <= int(value) <= len(flat):
                return {"inbound": inbound, "host_index": int(value)}
            fail(f"Enter a number from 1 to {len(flat)}.")

    def describe(self, source):
        ib = source["inbound"]
        return f"inbound {ib.get('tag', '?')} (port {ib.get('port', '?')}), host #{source['host_index']}"

    def create(self, source, c):
        api, tag = self.api, panel_inbound_tag(c)
        config = api.get_core_config()
        if config is None:
            return False, f"could not fetch core config ({api.last_error})"
        inbounds, outbounds = config.setdefault("inbounds", []), config.setdefault("outbounds", [])
        inbounds[:]  = [x for x in inbounds if x.get("port") != c["in_port"] and x.get("tag") != tag]
        outbounds[:] = [x for x in outbounds if x.get("tag") != tag]
        new_inbound = copy.deepcopy(source["inbound"])
        new_inbound["port"], new_inbound["tag"] = c["in_port"], tag
        inbounds.append(new_inbound)
        outbounds.append({"tag": tag, "protocol": "socks",
                          "settings": {"address": "127.0.0.1", "port": c["out_port"]}})
        rules = config.setdefault("routing", {}).setdefault("rules", [])
        rules[:] = [r for r in rules if not (tag in r.get("inboundTag", []) or r.get("outboundTag") == tag)]
        rules.append({"type": "field", "inboundTag": [tag], "outboundTag": tag})
        if not api.save_core_config(config):
            return False, f"saving core config failed ({api.last_error})"
        msg = f"in {c['in_port']} ➔ out {c['out_port']}"
        if not api.clone_host(source["host_index"], tag, tag):
            msg += f"  {C.YELLOW}(host clone failed: {api.last_error}){C.RESET}"
        return True, msg

    def remove(self, c):
        return self.api.remove_relay(panel_inbound_tag(c))

    def finalize(self):
        return True


# ── Panel flows (shared by 3X-UI and PasarGuard) ─────────────────────────────
def _panel_run_create(backend, countries):
    """Pick a clone source, confirm, then create every selected location."""
    source = backend.pick_source()
    if source is None:
        return
    draw_dashboard()
    screen_title("📋", "SUMMARY")
    out(f"{C.PURPLE}{'Clone from':<12}{C.RESET}{backend.describe(source)}",
        f"{C.PURPLE}{'Locations':<12}{C.RESET}{len(countries)}  "
        f"{C.DIM}({', '.join(c['name'] for c in countries[:6])}{'…' if len(countries) > 6 else ''}){C.RESET}")
    if not confirm("Start creation?"):
        note("Cancelled.")
        time.sleep(1)
        return
    print()
    created = 0
    for c in countries:
        success, msg = backend.create(source, c)
        label = f"{c['flag']} {pad(c['name'], 16)}"
        (ok if success else fail)(f"{label} {C.DIM if success else C.RED}{msg}{C.RESET}")
        created += bool(success)
    if created:
        backend.finalize()
    print()
    (ok if created else fail)(f"{created}/{len(countries)} location(s) configured.")
    pause()


def _panel_select(countries, title, prompt):
    """Numbered picker over `countries`; returns the chosen subset ([] to go back)."""
    while True:
        draw_dashboard()
        screen_title("📌", title)
        rows = [[f"{C.ACCENT}{i}{C.RESET}", f"{c['flag']} {c['name']}",
                 f"{C.TEAL}{c['in_port']}{C.RESET}", f"{C.TEAL}{c['out_port']}{C.RESET}"]
                for i, c in enumerate(countries, 1)]
        print("\n".join(table_lines(["#", "Location", "Panel in", "SOCKS out"], rows, "><>>")))
        note("\n0 = go back")
        text = ask(prompt)
        if text in ("0", ""):
            return []
        chosen = parse_selection(text, len(countries))
        if chosen:
            return [countries[i - 1] for i in chosen]
        fail("Invalid selection (examples: 3   or   1-4,7).")
        time.sleep(1.2)


def panel_batch_create(backend):
    existing = backend.configured_ports()
    missing  = [c for c in panel_countries() if c["in_port"] not in existing]
    if not missing:
        ok("All 50 primary locations are already configured.")
        pause()
        return
    if len(missing) < 50:
        note(f"{50 - len(missing)} already configured — skipping those.")
    _panel_run_create(backend, missing)


def panel_custom_create(backend):
    existing = backend.configured_ports()
    missing  = [c for c in panel_countries() if c["in_port"] not in existing]
    if not missing:
        ok("All 50 primary locations are already configured.")
        pause()
        return
    chosen = _panel_select(missing, "CUSTOM CREATE · SELECT LOCATIONS", "Location number(s)")
    if chosen:
        _panel_run_create(backend, chosen)


def panel_sync_deployed(backend):
    deployed = deployed_panel_countries()
    if not deployed:
        info("No EOTor modules are deployed yet — install some from the main menu first.")
        pause()
        return
    done    = backend.configured_codes()
    pending = [c for c in deployed if c["code"] not in done]
    if not pending:
        ok("Every deployed EOTor module is already configured in the panel.")
        pause()
        return
    chosen = _panel_select(pending, "DEPLOYED MODULES · NOT YET IN PANEL", "Module number(s)")
    if chosen:
        _panel_run_create(backend, chosen)


def panel_delete(backend, everything):
    existing   = backend.configured_ports()
    candidates = [c for c in panel_countries() if c["in_port"] in existing]
    if not candidates:
        info("Nothing to delete — no EOTor locations are configured in this panel.")
        pause()
        return
    targets = candidates if everything else _panel_select(
        candidates, "DELETE · SELECT LOCATIONS", "Location number(s) to delete")
    if not targets:
        return
    warn(f"{C.RED}This removes the inbound, SOCKS outbound and routing rule "
         f"for {len(targets)} location(s).{C.RESET}")
    if not confirm(f"Delete {len(targets)} location(s)?"):
        note("Cancelled.")
        time.sleep(1)
        return
    print()
    removed = 0
    for c in targets:
        done, detail = backend.remove(c)
        label = f"{c['flag']} {c['name']}"
        if done:
            print(f"  {C.RED}🗑{C.RESET}  {label}")
            removed += 1
        else:
            print(f"  {C.DIM}⏭  {label} — nothing to delete {detail}{C.RESET}")
    if removed:
        backend.finalize()
    print()
    ok(f"{removed} location(s) removed.")
    pause()


def panel_menu(backend):
    items = [
        ("1", "Batch create", "all primary locations"),
        ("2", "Custom create", "choose locations"),
        ("3", "Sync deployed modules", "EOTor nodes missing from the panel"),
        None,
        "Remove",
        ("4", "Delete all EOTor configurations", "", "danger"),
        ("5", "Delete selected configurations", "", "danger"),
        None,
        ("0", "Back"),
    ]
    run_menu(f"{backend.name.upper()} · CONTROL PANEL", items, {
        "1": lambda: panel_batch_create(backend),
        "2": lambda: panel_custom_create(backend),
        "3": lambda: panel_sync_deployed(backend),
        "4": lambda: panel_delete(backend, True),
        "5": lambda: panel_delete(backend, False),
    }, subtitle="Panel inbounds 3031–3080 ➔ local SOCKS 9080–9129")


def _connect_xui():
    info("Authenticating with the local 3X-UI database…")
    base_url, token = xui_generate_api_token()
    client = ThreeXUIClient(base_url, api_token=token)
    connected, error = client.test_connection()
    if not connected:
        run_cmd("systemctl restart x-ui")
        time.sleep(3)
        connected, error = client.test_connection()
    if not connected:
        raise PanelError(f"Cannot connect to 3X-UI: {error}\n     Try: systemctl restart x-ui")
    ok("Connected to 3X-UI.")
    return XUIBackend(client)


def _connect_pg():
    info("Connecting to PasarGuard…")
    url, user, password = _pg_credentials()
    api = PasarGuardAPI(url, user, password)
    if not api.login():
        if os.path.isfile(PANEL_PG_CREDS) and confirm("Login failed. Delete the saved credentials?"):
            try:
                os.remove(PANEL_PG_CREDS)
                note("Saved credentials removed — choose the panel again to re-enter them.")
            except OSError:
                pass
        raise PanelError(f"PasarGuard login failed: {api.last_error}")
    ok("Logged in to PasarGuard.")
    return PGBackend(api)


def _enter_panel(connect):
    try:
        backend = connect()
    except PanelError as e:
        fail(str(e))
        pause()
        return
    time.sleep(0.8)
    panel_menu(backend)


def _marzban_soon():
    info("Marzban support is under development.")
    time.sleep(2)


def panel_integration_menu():
    detected = [name for name, found in detect_panels() if found]
    if detected == ["3X-UI"]:
        return _enter_panel(_connect_xui)
    if detected == ["PasarGuard"]:
        return _enter_panel(_connect_pg)
    state = dict(detect_panels())
    def hint(name):
        return "detected" if state[name] else "not found"
    items = [
        ("1", "3X-UI Panel", hint("3X-UI")),
        ("2", "PasarGuard Panel", hint("PasarGuard")),
        ("3", "Marzban Panel", "coming soon"),
        None,
        ("0", "Back"),
    ]
    run_menu("PANEL INTEGRATION · EZ-PANEL", items, {
        "1": lambda: _enter_panel(_connect_xui),
        "2": lambda: _enter_panel(_connect_pg),
        "3": _marzban_soon,
    }, subtitle="Route panel inbounds through your EOTor locations")


# ══════════════════════════════════════════════════════════════════════════════
#  MENU ACTIONS
# ══════════════════════════════════════════════════════════════════════════════
def _reset_report():
    report_data.update({"SUCCESS": [], "FAILED": [], "SKIPPED": [], "RETRIED": [], "WARNED": []})

def _deploy_selection(selected: dict):
    if len(selected) == 1:
        deploy_node_task(next(iter(selected.values())), verbose=True)
    else:
        deploy_nodes_parallel(selected)
    print_report()
    pause()

def _parse_ids(text: str) -> list:
    return [int(x.strip()) for x in text.split(",")]

def install_primary_by_ids():
    draw_dashboard()
    show_location_list()
    try:
        ids = _parse_ids(ask("Module IDs to install (e.g. 1,4,12)"))
    except ValueError:
        fail("Invalid input")
        return pause()
    selected = {i: LOCATIONS[i] for i in ids if i in LOCATIONS}
    if not selected:
        fail("No valid IDs (1–50)")
        return pause()
    _deploy_selection(selected)

def install_all_primary():
    to_install = {}
    for nid, d in LOCATIONS.items():
        if node_is_installed(d["iso"]):
            report_data["SKIPPED"].append(d["name"].upper())
        else:
            to_install[nid] = d
    if report_data["SKIPPED"]:
        note(f"({len(report_data['SKIPPED'])} already deployed)")
    deploy_nodes_parallel(to_install)
    print_report()
    pause()

def reinstall_failed():
    selected = {nid: d for nid, d in LOCATIONS.items() if not node_is_installed(d["iso"])}
    if not selected:
        ok("All primary modules deployed!")
        return pause()
    deploy_nodes_parallel(selected)
    print_report()
    pause()

def show_extended_list():
    show_global_location_list()
    pause()

def _control_by_ids(action, prompt):
    draw_dashboard()
    show_location_list()
    note("Use IDs 51+ for extended modules")
    selected = _pick_targets_from_input(prompt)
    if selected:
        action(selected)
    pause()

def _control_all(action):
    installed = {nid: d for nid, d in ALL_LOCATIONS.items() if node_is_installed(d["iso"])}
    if installed:
        action(installed)
    else:
        fail("No modules deployed")
    pause()

def remove_by_ids():
    draw_dashboard()
    show_location_list()
    note("Use IDs 51+ for extended modules")
    try:
        ids = _parse_ids(ask("Module IDs to remove"))
    except ValueError:
        fail("Invalid input")
        return pause()
    targets = {i: ALL_LOCATIONS[i] for i in ids if i in ALL_LOCATIONS}
    if targets:
        print()
        removed = _remove_targets(targets)
        print()
        ok(f"{removed} module(s) removed")
    pause()

def refresh_relay_density():
    _exit_cache.clear()
    fetch_all_exit_counts()
    ok("Relay density data refreshed")
    time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def _submenu(title, items, handlers, subtitle=None):
    def run():
        _reset_report()
        run_menu(title, items, handlers, subtitle)
    return run

MAIN_ITEMS = [
    ("1", "Setup & Engine",            "install · update · uninstall"),
    ("2", "Install Location Modules",  "50 primary locations"),
    ("3", "Extended Modules",          "160+ more locations"),
    ("4", "Control Modules",           "start · stop · restart · remove"),
    ("5", "Monitoring & Diagnostics",  "status · health · leak check"),
    ("6", "IP & Routing",              "deploy · live IPs · rotate"),
    ("7", "Automation & Guardian",     "auto-restart · CPU guardian"),
    ("8", "Panel Integration",         "3X-UI · PasarGuard (EZ-Panel)"),
    None,
    ("0", "Exit"),
]

def build_main_handlers():
    return {
        "1": _submenu("SETUP & ENGINE", [
            ("1", "Install Engine", "tor · tor-geoipdb · curl"),
            ("2", "Update System"),
            ("3", "Uninstall System", "removes every module", "danger"),
            None, ("0", "Back")],
            {"1": engine_install, "2": engine_update, "3": engine_uninstall}),

        "2": _submenu("INSTALL LOCATION MODULES", [
            ("1", "Install modules", "select by ID"),
            ("2", "Install ALL 50 primary modules"),
            ("3", "Re-install failed modules", "deploys whatever is missing"),
            None, ("0", "Back")],
            {"1": install_primary_by_ids, "2": install_all_primary, "3": reinstall_failed}),

        "3": _submenu(f"EXTENDED MODULES · {len(GLOBAL_LOCATIONS)} locations", [
            ("1", "Show extended location list"),
            ("2", "Install extended modules", "select by ID"),
            ("3", "Search & install by country name"),
            None, ("0", "Back")],
            {"1": show_extended_list, "2": install_global_nodes, "3": search_and_install_global}),

        "4": _submenu("CONTROL MODULES", [
            ("1", "Start modules", "select by ID"),
            ("2", "Stop modules", "select by ID"),
            ("3", "Restart modules", "select by ID"),
            ("4", "Start ALL modules"),
            ("5", "Stop ALL modules"),
            ("6", "Restart ALL modules"),
            None,
            ("7", "Remove modules", "select by ID", "danger"),
            ("8", "Remove ALL modules", "", "danger"),
            None, ("0", "Back")],
            {"1": lambda: _control_by_ids(start_nodes, "Module IDs to start"),
             "2": lambda: _control_by_ids(stop_nodes, "Module IDs to stop"),
             "3": lambda: _control_by_ids(restart_nodes, "Module IDs to restart"),
             "4": lambda: _control_all(start_nodes),
             "5": lambda: _control_all(stop_nodes),
             "6": lambda: _control_all(restart_nodes),
             "7": remove_by_ids, "8": remove_all_nodes}),

        "5": _submenu("MONITORING & DIAGNOSTICS", [
            ("1", "Live status table"),
            ("2", "Health check", "connectivity test"),
            ("3", "Refresh relay density counters"),
            ("4", "Show current exit IP per location"),
            ("5", "IP leak & block check", "Tor verify · DNS leak · blacklist"),
            ("6", "Diagnose a problem module"),
            None, ("0", "Back")],
            {"1": show_status, "2": health_check, "3": refresh_relay_density,
             "4": show_exit_ips, "5": check_ip_leak_and_block, "6": diagnose_node}),

        "6": _submenu("IP & ROUTING", [
            ("1", "Deploy module", "with live progress"),
            ("2", "Live IP panel", "real-time viewer"),
            ("3", "Rotate IP", "refresh exit routing"),
            None, ("0", "Back")],
            {"1": download_node, "2": live_ip_panel, "3": rotate_ips}),

        "7": _submenu(lambda: f"AUTOMATION & GUARDIAN · CPU Guardian {_guardian_badge()}", [
            ("1", "Enable hourly auto-restart", "all modules"),
            ("2", "Disable hourly auto-restart"),
            None,
            ("3", "Start CPU Guardian"),
            ("4", "Stop CPU Guardian"),
            ("5", "Guardian status & event log"),
            None, ("0", "Back")],
            {"1": setup_auto_restart, "2": disable_auto_restart, "3": start_cpu_guardian,
             "4": stop_cpu_guardian, "5": show_guardian_status}),

        "8": panel_integration_menu,
    }

def main():
    try:
        check_root()
        self_install()
        fetch_all_exit_counts()
        _reset_report()
        run_menu(lambda: f"MAIN MENU · {BRAND_NAME} {BRAND_VERSION}", MAIN_ITEMS, build_main_handlers())
        print(f"\n  {C.ACCENT}Goodbye — {BRAND_NAME} shutting down.{C.RESET}\n")
    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}✘  Interrupted by user.{C.RESET}\n")
    sys.exit(0)

if __name__ == "__main__":
    main()

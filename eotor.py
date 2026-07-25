#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import shutil
import urllib.request
import subprocess
import concurrent.futures
import threading
import itertools
from datetime import datetime
from collections import OrderedDict

# ══════════════════════════════════════════════════════════════════════════════
#  ANSI COLOR PALETTE
# ══════════════════════════════════════════════════════════════════════════════
class C:
    CYAN   = '\033[1;36m'
    GREEN  = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RED    = '\033[1;31m'
    PURPLE = '\033[1;35m'
    BLUE   = '\033[1;34m'
    WHITE  = '\033[1;37m'
    DIM    = '\033[2m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

# ══════════════════════════════════════════════════════════════════════════════
#  BRANDING
# ══════════════════════════════════════════════════════════════════════════════
BRAND_NAME    = "EOTor Engine"
BRAND_VERSION = "v3.4"
BRAND_TAGLINE = "Enterprise Multi-Location Routing Manager"

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

def _progress_bar(percent: int, width: int = 26) -> str:
    filled = int(width * percent / 100)
    empty  = width - filled
    if percent < 40:
        color = C.RED
    elif percent < 80:
        color = C.YELLOW
    else:
        color = C.GREEN
    bar = f"{color}{'█' * filled}{C.DIM}{'░' * empty}{C.RESET}"
    return f"[{bar}] {color}{percent:>3}%{C.RESET}"

def _install_bar(percent: int, width: int = 30) -> str:
    """Flat progress bar for installer steps."""
    filled = int(width * percent / 100)
    empty  = width - filled
    if percent < 40:
        color = C.RED
    elif percent < 80:
        color = C.YELLOW
    else:
        color = C.GREEN
    bar = f"{color}{'█' * filled}{'░' * empty}{C.RESET}"
    return f" {bar}  {color}{percent:>3}%{C.RESET}"

def _section_header(title: str, color=None) -> str:
    color = color or C.CYAN
    pad   = max(73 - 4 - len(title), 1)
    return f"\n{color}  ┌─ {title} {'─' * pad}┐{C.RESET}"

def _divider(char="═", width=75, color=None) -> str:
    color = color or C.DIM
    return f"{color}{char * width}{C.RESET}"

# ══════════════════════════════════════════════════════════════════════════════
#  ASCII LOGO
# ══════════════════════════════════════════════════════════════════════════════
def _print_logo():
    logo_lines = [
        r"   ███████╗ ██████╗ ████████╗ ██████╗ ██████╗ ",
        r"   ██╔════╝██╔═══██╗╚══██╔══╝██╔═══██╗██╔══██╗",
        r"   █████╗  ██║   ██║   ██║   ██║   ██║██████╔╝",
        r"   ██╔══╝  ██║   ██║   ██║   ██║   ██║██╔══██╗",
        r"   ███████╗╚██████╔╝   ██║   ╚██████╔╝██║  ██║",
        r"   ╚══════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝",
        r"",
        f"   {'ENGINE':^50}  {BRAND_VERSION}",
    ]
    print(f"\n{C.CYAN}", end="")
    for line in logo_lines:
        print(line)
    print(f"{C.RESET}")
    tagline = f"  {BRAND_TAGLINE}"
    print(f"{C.DIM}{tagline}{C.RESET}")
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
    os.system("clear")
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
    input(f"\n{C.DIM}  Press Enter to continue...{C.RESET}")

def engine_update():
    os.system("clear")
    _print_logo()
    print(f"  {C.CYAN}⟳  Updating {BRAND_NAME} Core...{C.RESET}\n")
    _animate_install_step("Refreshing Package Sources", 0.4)
    run_cmd("apt-get update -qq")
    _animate_install_step("Upgrading Core Components", 0.6)
    run_out("apt-get install -yq --only-upgrade tor tor-geoipdb curl")
    _animate_install_step("Verifying Updated Components", 0.3)
    print(f"\n  {C.GREEN}✔  {BRAND_NAME} Core updated successfully.{C.RESET}")
    input(f"\n{C.DIM}  Press Enter to continue...{C.RESET}")

def engine_uninstall():
    installed = {nid: d for nid, d in ALL_LOCATIONS.items() if node_is_installed(d["iso"])}
    print(f"\n  {C.RED}⚠   WARNING — This will permanently remove ALL "
          f"{len(installed)} location module(s){C.RESET}")
    print(f"  {C.RED}    and uninstall the {BRAND_NAME} Core from this system.{C.RESET}\n")
    confirm = input(f"  {C.YELLOW}Type 'yes' to confirm: {C.RESET}").strip().lower()
    if confirm != "yes":
        print(f"  {C.DIM}Cancelled.{C.RESET}")
        input(f"\n{C.DIM}  Press Enter to continue...{C.RESET}")
        return
    if installed:
        print()
        _remove_targets(installed)
    print(f"\n  {C.YELLOW}⟳  Removing core packages...{C.RESET}")
    run_cmd("apt-get purge -yq tor tor-geoipdb")
    run_cmd("apt-get autoremove -yq")
    print(f"\n  {C.GREEN}✔  {BRAND_NAME} Core and all location modules removed.{C.RESET}")
    input(f"\n{C.DIM}  Press Enter to continue...{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  SERVER INFO
# ══════════════════════════════════════════════════════════════════════════════
def get_server_info():
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
def draw_dashboard():
    os.system("clear")
    _print_logo()

    ip, loc, isp = get_server_info()
    os_info = "Linux"
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME"):
                    os_info = line.split("=")[1].strip().strip('"')
    except:
        pass

    inst_count    = sum(1 for d in ALL_LOCATIONS.values() if node_is_installed(d["iso"]))
    running_count = sum(1 for d in ALL_LOCATIONS.values() if node_is_running(d["iso"]))
    total_count   = len(ALL_LOCATIONS)

    print(f"  {_divider('─', 71)}")
    print(f"  {C.PURPLE}▸ Server IP    :{C.RESET}  {ip}")
    print(f"  {C.PURPLE}▸ Location     :{C.RESET}  {loc}")
    print(f"  {C.PURPLE}▸ ISP          :{C.RESET}  {isp}")
    print(f"  {C.PURPLE}▸ OS           :{C.RESET}  {os_info}")
    print(f"  {C.PURPLE}▸ Date / Time  :{C.RESET}  {datetime.now().strftime('%Y-%m-%d  %H:%M')}")
    print(f"  {C.PURPLE}▸ Modules      :{C.RESET}  "
          f"{C.GREEN}{inst_count}/{total_count}{C.RESET}  "
          f"{C.DIM}(50 primary + {len(GLOBAL_LOCATIONS)} extended){C.RESET}")
    print(f"  {C.PURPLE}▸ Active       :{C.RESET}  {C.GREEN}{running_count}/{total_count}{C.RESET}")
    print(f"  {_divider('─', 71)}")

# ══════════════════════════════════════════════════════════════════════════════
#  LOCATION LIST
# ══════════════════════════════════════════════════════════════════════════════
def show_location_list(loc_dict=None, title=None):
    if loc_dict is None:
        loc_dict = LOCATIONS
    if title is None:
        title = "PRIMARY LOCATION MODULES (ports 9080–9129)"

    legend = (
        f"  {C.GREEN}■{C.RESET}{C.DIM}=active   "
        f"{C.DIM}○{C.RESET}{C.DIM}=inactive   "
        f"relay density: "
        f"{C.GREEN}optimal{C.RESET}{C.DIM}  "
        f"{C.YELLOW}limited{C.RESET}{C.DIM}  "
        f"{C.RED}critical{C.RESET}"
    )
    print(legend)
    print(f"  {_divider('─', 73)}")
    print(f"  {C.CYAN}{title}{C.RESET}")
    print()

    items  = list(loc_dict.items())
    mid    = (len(items) + 1) // 2
    left   = items[:mid]
    right  = items[mid:]

    for i in range(mid):
        row_parts = []
        if i < len(left):
            nid, d = left[i]
            iso    = d["iso"]
            port   = d["port"]
            name   = d["name"]
            flag   = _flag(iso)
            node   = _display_node_name(iso)
            inst   = f"{C.GREEN}■{C.RESET}" if node_is_installed(iso) else f"{C.DIM}○{C.RESET}"
            ec     = _ec_badge(iso)
            cell   = (f"{C.WHITE}[{nid:>3}]{C.RESET} {inst} {flag} "
                      f"{name:<20} {C.DIM}:{port}{C.RESET} {ec}")
            row_parts.append(cell)
        if i < len(right):
            nid, d = right[i]
            iso    = d["iso"]
            port   = d["port"]
            name   = d["name"]
            flag   = _flag(iso)
            inst   = f"{C.GREEN}■{C.RESET}" if node_is_installed(iso) else f"{C.DIM}○{C.RESET}"
            ec     = _ec_badge(iso)
            cell   = (f"{C.WHITE}[{nid:>3}]{C.RESET} {inst} {flag} "
                      f"{name:<20} {C.DIM}:{port}{C.RESET} {ec}")
            row_parts.append(cell)
        print("   ".join(row_parts))

    print(f"  {_divider('─', 73)}")

def show_global_location_list():
    os.system("clear")
    draw_dashboard()
    show_location_list(
        loc_dict=GLOBAL_LOCATIONS,
        title=f"EXTENDED LOCATION MODULES (ports 9130–{9130 + len(GLOBAL_LOCATIONS) - 1})"
    )

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════
def _menu_row(num_str, text, color=None):
    color   = color or C.WHITE
    label   = f"[{num_str}]"
    visible = 4 + len(label) + 1 + len(text)
    pad     = max(73 - visible, 1)
    return (f"{C.CYAN}║{C.RESET}    {color}{label}{C.RESET} "
            f"{text}{' ' * pad}{C.CYAN}║{C.RESET}")

def _menu_section(title, color):
    visible = 2 + len(title)
    pad     = max(73 - visible, 1)
    return (f"{C.CYAN}║{C.RESET}  {color}{title}{C.RESET}"
            f"{' ' * pad}{C.CYAN}║{C.RESET}")

def _menu_blank():
    return f"{C.CYAN}║{C.RESET}{' ' * 73}{C.CYAN}║{C.RESET}"

def show_menu():
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.WHITE}MAIN MENU  —  {BRAND_NAME} {BRAND_VERSION}{C.RESET}"
          f"{' ' * (73 - 18 - len(BRAND_NAME) - len(BRAND_VERSION))}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Setup & Engine"))
    print(_menu_row("2", "Install Location Modules"))
    print(_menu_row("3", "Extended Modules"))
    print(_menu_row("4", "Control Modules"))
    print(_menu_row("5", "Monitoring & Diagnostics"))
    print(_menu_row("6", "IP & Routing"))
    print(_menu_row("7", "Automation & Guardian"))
    print(_menu_blank())
    print(_menu_row("0", "Exit"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_1():
    """Setup & Engine"""
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.GREEN}SETUP & ENGINE{C.RESET}{' ' * 57}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Install Engine"))
    print(_menu_row("2", "Update System"))
    print(_menu_row("3", "Uninstall System"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_2():
    """Install Location Modules"""
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.GREEN}INSTALL LOCATION MODULES{C.RESET}{' ' * 47}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Install modules (select by ID)"))
    print(_menu_row("2", "Install ALL 50 primary modules"))
    print(_menu_row("3", "Re-install failed modules"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_3():
    """Extended Modules"""
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.BLUE}EXTENDED MODULES  ({len(GLOBAL_LOCATIONS)} locations: 9130+){C.RESET}{' ' * (73 - 40 - len(str(len(GLOBAL_LOCATIONS))))}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Show extended location list"))
    print(_menu_row("2", "Install extended module(s) (select by ID)"))
    print(_menu_row("3", "Search & install by country name"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_4():
    """Control Modules"""
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.YELLOW}CONTROL MODULES{C.RESET}{' ' * 56}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Start modules"))
    print(_menu_row("2", "Stop modules"))
    print(_menu_row("3", "Restart modules"))
    print(_menu_row("4", "Start ALL modules"))
    print(_menu_row("5", "Stop ALL modules"))
    print(_menu_row("6", "Restart ALL modules"))
    print(_menu_blank())
    print(_menu_row("7", "Remove modules"))
    print(_menu_row("8", "Remove ALL modules"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_5():
    """Monitoring & Diagnostics"""
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.PURPLE}MONITORING & DIAGNOSTICS{C.RESET}{' ' * 47}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Live status table"))
    print(_menu_row("2", "Health check (connectivity test)"))
    print(_menu_row("3", "Refresh relay density counters"))
    print(_menu_row("4", "Show current exit IP per location"))
    print(_menu_row("5", "Diagnose a problem module"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_6():
    """IP & Routing"""
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.BLUE}IP & ROUTING{C.RESET}{' ' * 59}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Deploy module (with progress)"))
    print(_menu_row("2", "Live IP panel (real-time viewer)"))
    print(_menu_row("3", "Rotate IP (refresh exit routing)"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


def show_submenu_7():
    """Automation & Guardian"""
    guardian_state = (f"{C.GREEN}● ON{C.RESET}"
                      if (_guardian_thread and _guardian_thread.is_alive())
                      else f"{C.DIM}○ OFF{C.RESET}")
    print(f"\n{C.CYAN}╔{'═' * 73}╗{C.RESET}")
    # "AUTOMATION & GUARDIAN  [CPU Guardian: ● ON]" = 44 visible chars
    _g_title = f"AUTOMATION & GUARDIAN  [CPU Guardian: {guardian_state}]"
    _g_pad = max(73 - 2 - 44, 1)
    print(f"{C.CYAN}║{C.RESET}  {C.PURPLE}{_g_title}{C.RESET}{chr(32) * _g_pad}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
    print(_menu_row("1", "Enable hourly auto-restart (all modules)"))
    print(_menu_row("2", "Disable hourly auto-restart"))
    print(_menu_blank())
    print(_menu_row("3", "Start CPU Guardian"))
    print(_menu_row("4", "Stop CPU Guardian"))
    print(_menu_row("5", "Guardian status & event log"))
    print(_menu_blank())
    print(_menu_row("0", "← Back"))
    print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")


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
        percent = int((completed / total) * 100)
        bar     = _progress_bar(percent, width=50)
        spin    = _spin()
        print("\033[H\033[2J", end="", flush=True)
        print(f"{C.CYAN}╔{'═' * 73}╗{C.RESET}")
        print(f"{C.CYAN}║{C.RESET}  {C.WHITE}PARALLEL DEPLOYMENT  —  {BRAND_NAME}{C.RESET}"
              f"{' ' * (73 - 28 - len(BRAND_NAME))}{C.CYAN}║{C.RESET}")
        print(f"{C.CYAN}╠{'═' * 73}╣{C.RESET}")
        print(f"{C.CYAN}║{C.RESET}  {bar}  {C.CYAN}║{C.RESET}")
        print(f"{C.CYAN}║{C.RESET}  "
              f"Total: {C.WHITE}{total:>2}{C.RESET} │ "
              f"Success: {C.GREEN}{success:>2}{C.RESET} │ "
              f"Failed: {C.RED}{failed:>2}{C.RESET} │ "
              f"Pending: {C.YELLOW}{total - completed:>2}{C.RESET}  "
              f"  {C.DIM}{spin}{C.RESET}{C.CYAN}║{C.RESET}")
        print(f"{C.CYAN}╚{'═' * 73}╝{C.RESET}")
        print()
        print(f"  {C.CYAN}Active Modules:{C.RESET}")
        print(f"  {'─' * 72}")
        if current:
            for iso in sorted(current.keys()):
                print(f"  {current[iso]}")
        else:
            print(f"  {C.DIM}Waiting for modules to initialize...{C.RESET}")
        print(f"  {'─' * 72}")
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
    os.system("clear")
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
            input(f"\n{C.DIM}  Press Enter...{C.RESET}")
            return
        if len(selected) == 1:
            print(f"\n  {C.YELLOW}⚡  Deploying 1 extended module...{C.RESET}\n")
            for d in selected.values():
                deploy_node_task(d, verbose=True)
        else:
            deploy_nodes_parallel(selected)
        print_report()
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
    except ValueError:
        print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")

def search_and_install_global():
    os.system("clear")
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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return

    print(f"\n  {C.GREEN}Found {len(results)} match(es):{C.RESET}\n")
    print(f"  {'ID':>4}  {'Name':<30}  {'Port':>5}  {'Relays':>6}  {'Status'}")
    print(f"  {'─' * 62}")
    for nid, d in sorted(results.items()):
        iso   = d["iso"]
        port  = d["port"]
        name  = d["name"]
        flag  = _flag(iso)
        ec    = _exit_cache.get(iso, -1)
        ec_s  = f"{ec:>6}" if ec >= 0 else "     ?"
        grp   = "primary " if nid <= 50 else "extended"
        inst  = (f"{C.GREEN}■ active{C.RESET}" if node_is_installed(iso)
                 else f"{C.DIM}○ inactive{C.RESET}")
        print(f"  {nid:>4}  {flag} {name:<28}  {port:>5}  {ec_s}  "
              f"{inst}  {C.DIM}[{grp}]{C.RESET}")

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
            input(f"\n{C.DIM}  Press Enter...{C.RESET}")
            return
        if len(selected) == 1:
            for d in selected.values():
                deploy_node_task(d, verbose=True)
        else:
            deploy_nodes_parallel(selected)
        print_report()
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
    except ValueError:
        print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  DOWNLOAD NODE
# ══════════════════════════════════════════════════════════════════════════════
def download_node():
    os.system("clear")
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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return

    iso, port, name = d["iso"], d["port"], d["name"].upper()
    if node_is_installed(iso):
        print(f"\n  {C.YELLOW}⚠  {name} already deployed. "
              f"Remove it first to re-deploy.{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return

    print(f"\n  {C.CYAN}⚡  Deploying {_flag(iso)} {name} (port {port})...{C.RESET}\n")
    deploy_node_task(d, verbose=True)
    print_report()
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

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
    os.system("clear")
    draw_dashboard()
    running = {nid: d for nid, d in ALL_LOCATIONS.items() if node_is_running(d["iso"])}
    if not running:
        print(f"  {C.RED}✘  No active modules.{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return
    print(f"\n  {C.CYAN}🌐  LIVE IP PANEL — {len(running)} ACTIVE MODULES{C.RESET}\n")
    print(f"  {'#':>4}  {'Location':<25}  {'Port':>5}  {'Exit IP':<22}  Status")
    print(f"  {'─' * 74}")
    _ip_cache.clear()

    def display_ip(nid):
        while nid not in _ip_cache:
            time.sleep(0.05)
        data = _ip_cache[nid]
        ip   = data["ip"]
        name = data["name"]
        port = data["port"]
        flag = _flag(ALL_LOCATIONS[nid]["iso"])
        if ip:
            status     = f"{C.GREEN}✔ active{C.RESET}"
            ip_display = f"{C.GREEN}{ip:<22}{C.RESET}"
        else:
            status     = f"{C.YELLOW}⚠ timeout{C.RESET}"
            ip_display = f"{C.RED}{'unreachable':<22}{C.RESET}"
        print(f"  {nid:>4}  {flag} {name:<23}  {port:>5}  {ip_display}  {status}")
        sys.stdout.flush()

    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = [pool.submit(_fetch_ip_task, nid, d) for nid, d in running.items()]
        for nid in running.keys():
            display_ip(nid)
        concurrent.futures.wait(futures)

    print(f"  {'─' * 74}")
    success_count = sum(1 for v in _ip_cache.values() if v.get("ip"))
    print(f"\n  {C.GREEN}{success_count}/{len(running)} modules{C.RESET} responding")
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

def show_exit_ips():
    os.system("clear")
    draw_dashboard()
    print(f"\n  {C.PURPLE}🌍  EXIT IP MAP — CURRENT ROUTING ENDPOINTS{C.RESET}\n")
    running = {nid: d for nid, d in ALL_LOCATIONS.items() if node_is_running(d["iso"])}
    if not running:
        print(f"  {C.RED}✘  No active modules.{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return
    print(f"  {C.DIM}Querying {len(running)} active module(s)...{C.RESET}\n")
    print(f"  {'#':>4}  {'Location':<26}  {'Port':>5}  {'Exit IP':<22}  Updated")
    print(f"  {'─' * 82}")
    old_ips = getattr(show_exit_ips, 'prev_ips', {})

    def _check(item):
        nid, d = item
        return nid, get_node_exit_ip(d["port"], timeout=15)

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        for nid, ip in pool.map(_check, running.items()):
            results[nid] = ip

    current_time = datetime.now().strftime("%H:%M:%S")
    for nid, d in running.items():
        ip     = results.get(nid)
        old_ip = old_ips.get(nid)
        flag   = _flag(d["iso"])
        if ip:
            if old_ip and old_ip != ip:
                ip_display = f"{C.YELLOW}{ip:<22}{C.RESET}"
                changed    = f" {C.GREEN}[CHANGED]{C.RESET}"
            else:
                ip_display = f"{C.GREEN}{ip:<22}{C.RESET}"
                changed    = ""
            print(f"  {nid:>4}  {flag} {d['name']:<24}  {d['port']:>5}  "
                  f"{ip_display}  {current_time}{changed}")
        else:
            print(f"  {nid:>4}  {flag} {d['name']:<24}  {d['port']:>5}  "
                  f"{C.RED}{'unreachable':<22}{C.RESET}  {current_time}")

    show_exit_ips.prev_ips = results
    print(f"  {'─' * 82}")
    success = sum(1 for ip in results.values() if ip)
    changed = sum(1 for nid in results.keys()
                  if old_ips.get(nid) and results.get(nid)
                  and old_ips[nid] != results[nid])
    print(f"\n  {C.GREEN}{success}/{len(running)} responding{C.RESET}", end="")
    if changed > 0:
        print(f"  │  {C.YELLOW}{changed} endpoint(s) changed since last check{C.RESET}")
    else:
        print()
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  IP ROTATION
# ══════════════════════════════════════════════════════════════════════════════
def rotate_ips():
    os.system("clear")
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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return
    if not targets:
        print(f"\n  {C.RED}✘  No valid IDs{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return
    print(f"\n  {C.RED}⚠   Remove ALL {len(installed)} deployed module(s)?{C.RESET}")
    confirm = input(f"  {C.YELLOW}Type 'yes' to confirm: {C.RESET}").strip().lower()
    if confirm != "yes":
        print(f"  {C.DIM}Cancelled.{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
        return
    print()
    removed = _remove_targets(installed)
    print(f"\n  {C.GREEN}✔  {removed} module(s) removed.{C.RESET}")
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  STATUS TABLE
# ══════════════════════════════════════════════════════════════════════════════
def show_status():
    draw_dashboard()
    print(f"\n  {C.CYAN}📡  MODULE STATUS TABLE{C.RESET}\n")
    print(f"  {'#':>4}  {'Location':<26}  {'Port':>5}  {'Relays':>6}  Status")
    print(f"  {'─' * 65}")
    for nid, d in ALL_LOCATIONS.items():
        iso  = d["iso"]
        port = d["port"]
        name = d["name"]
        flag = _flag(iso)
        n    = _exit_cache.get(iso, -1)
        ec   = f"{n:>6}" if n >= 0 else "     ?"
        if not node_is_installed(iso):
            status = f"{C.DIM}○ inactive{C.RESET}"
        elif node_is_running(iso):
            status = f"{C.GREEN}● active{C.RESET}"
        else:
            status = f"{C.RED}✘ stopped{C.RESET}"
        print(f"  {nid:>4}  {flag} {name:<24}  {port:>5}  {ec}  {status}")
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════
def health_check():
    draw_dashboard()
    print(f"\n  {C.PURPLE}🩺  CONNECTIVITY HEALTH CHECK{C.RESET}\n")
    ok = fail = 0
    for nid, d in ALL_LOCATIONS.items():
        iso  = d["iso"]
        port = d["port"]
        name = d["name"].upper()
        flag = _flag(iso)
        if not node_is_running(iso):
            continue
        print(f"  {flag} {C.CYAN}{name:<24}{C.RESET}  :{port}  … ", end="", flush=True)
        t0 = time.time()
        r  = run_cmd(f"curl -s -m 10 --socks5-hostname 127.0.0.1:{port} "
                     f"https://www.google.com/generate_204")
        ms = int((time.time() - t0) * 1000)
        if r.returncode == 0:
            print(f"{C.GREEN}✔  {ms}ms{C.RESET}")
            ok += 1
        else:
            print(f"{C.RED}✘  FAIL{C.RESET}")
            fail += 1
    print(f"\n  {_divider('─', 50)}")
    print(f"  {C.GREEN}{ok} passed{C.RESET}  │  {C.RED}{fail} failed{C.RESET}")
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")


def stop_cpu_guardian():
    global _guardian_active
    if not (_guardian_thread and _guardian_thread.is_alive()):
        print(f"\n  {C.DIM}CPU Guardian is not running.{C.RESET}")
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")


def show_guardian_status():
    os.system("clear")
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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGNOSE
# ══════════════════════════════════════════════════════════════════════════════
def diagnose_node():
    os.system("clear")
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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
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
        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
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
    input(f"\n{C.DIM}  Press Enter...{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  DEPLOYMENT REPORT
# ══════════════════════════════════════════════════════════════════════════════
def print_report():
    elapsed    = int((datetime.now() - SESSION_START).total_seconds())
    mins, secs = divmod(elapsed, 60)
    total      = len(report_data["SUCCESS"]) + len(report_data["FAILED"])
    pct        = int(len(report_data["SUCCESS"]) / total * 100) if total else 0
    filled     = int(pct / 5)
    bar        = f"{'█' * filled}{'░' * (20 - filled)}"

    print(f"\n  {_divider()}")
    print(f"  {C.CYAN}  📊  DEPLOYMENT REPORT  —  {BRAND_NAME}{C.RESET}")
    print(f"  {C.DIM}  Session time: {mins}m {secs}s{C.RESET}")
    print(f"  {_divider('─', 75)}")

    if report_data["WARNED"]:
        print(f"  {C.YELLOW}⚠   Warnings:{C.RESET}")
        for n in report_data["WARNED"]:
            print(f"      ⚠  {n}")

    if report_data["SUCCESS"]:
        retried = set(report_data["RETRIED"])
        print(f"\n  {C.GREEN}✔   Deployed ×{len(report_data['SUCCESS'])}:{C.RESET}")
        for n in report_data["SUCCESS"]:
            tag = (f" {C.YELLOW}(retry){C.RESET}"
                   if any(n.startswith(r) for r in retried) else "")
            print(f"      ✔  {n}{tag}")

    if report_data["FAILED"]:
        print(f"\n  {C.RED}✘   Failed ×{len(report_data['FAILED'])}:{C.RESET}")
        for n in report_data["FAILED"]:
            print(f"      ✘  {n}")

    if total:
        color = C.GREEN if pct >= 80 else (C.YELLOW if pct >= 50 else C.RED)
        print(f"\n  [{color}{bar}{C.RESET}] {color}{pct}% success rate{C.RESET}")

    # Location summary table
    if report_data["SUCCESS"]:
        print(f"\n  {C.DIM}  Deployed Location Modules:{C.RESET}")
        print(f"  {'─' * 60}")
        for entry in report_data["SUCCESS"]:
            # entry format: "NAME (:PORT) → IP"
            iso_guess = next(
                (d["iso"] for d in ALL_LOCATIONS.values()
                 if d["name"].upper() in entry), "")
            flag = _flag(iso_guess) if iso_guess else "🌐"
            parts = entry.split(" → ")
            name_port = parts[0].strip()
            exit_ip   = parts[1].strip() if len(parts) > 1 else "—"
            node_alias = _display_node_name(iso_guess) if iso_guess else name_port
            status_icon = f"{C.GREEN}✔ Ready{C.RESET}"
            print(f"  {flag}  {node_alias:<18}  {exit_ip:<22}  {status_icon}")
        print(f"  {'─' * 60}")

    print(f"  {_divider()}")

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    try:
        check_root()
        self_install()
        fetch_all_exit_counts()

        while True:
            report_data.update({
                "SUCCESS": [], "FAILED": [], "SKIPPED": [],
                "RETRIED": [], "WARNED": []
            })
            draw_dashboard()
            show_menu()
            choice = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip().lower()

            if choice == "0":
                print(f"\n  {C.CYAN}Goodbye — {BRAND_NAME} shutting down.{C.RESET}\n")
                sys.exit(0)

            # ── 1: Setup & Engine ─────────────────────────────────────────────
            elif choice == "1":
                while True:
                    draw_dashboard(); show_submenu_1()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1": engine_install()
                    elif sub == "2": engine_update()
                    elif sub == "3": engine_uninstall()
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            # ── 2: Install Location Modules ───────────────────────────────────
            elif choice == "2":
                while True:
                    draw_dashboard(); show_submenu_2()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1":
                        os.system("clear"); draw_dashboard(); show_location_list()
                        ids_input = input(
                            f"\n  {C.YELLOW}Enter module IDs (e.g. 1,4,12): {C.RESET}"
                        ).strip()
                        try:
                            ids      = [int(x.strip()) for x in ids_input.split(",")]
                            selected = {i: LOCATIONS[i] for i in ids if i in LOCATIONS}
                            if not selected:
                                print(f"\n  {C.RED}✘  No valid IDs (1–50){C.RESET}")
                                input(f"\n{C.DIM}  Press Enter...{C.RESET}"); continue
                            if len(selected) == 1:
                                for d in selected.values():
                                    deploy_node_task(d, verbose=True)
                            else:
                                deploy_nodes_parallel(selected)
                            print_report()
                            input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                        except ValueError:
                            print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
                            input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "2":
                        to_install = {}
                        for nid, d in LOCATIONS.items():
                            if node_is_installed(d["iso"]):
                                report_data["SKIPPED"].append(d["name"].upper())
                            else:
                                to_install[nid] = d
                        if report_data["SKIPPED"]:
                            print(f"\n  {C.DIM}({len(report_data['SKIPPED'])} already deployed){C.RESET}")
                        deploy_nodes_parallel(to_install)
                        print_report()
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "3":
                        selected = {nid: d for nid, d in LOCATIONS.items()
                                    if not node_is_installed(d["iso"])}
                        if not selected:
                            print(f"\n  {C.GREEN}✔  All primary modules deployed!{C.RESET}")
                            input(f"\n{C.DIM}  Press Enter...{C.RESET}"); continue
                        deploy_nodes_parallel(selected)
                        print_report()
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            # ── 3: Extended Modules ───────────────────────────────────────────
            elif choice == "3":
                while True:
                    draw_dashboard(); show_submenu_3()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1":
                        show_global_location_list()
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "2": install_global_nodes()
                    elif sub == "3": search_and_install_global()
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            # ── 4: Control Modules ────────────────────────────────────────────
            elif choice == "4":
                while True:
                    draw_dashboard(); show_submenu_4()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1":
                        os.system("clear"); draw_dashboard(); show_location_list()
                        print(f"  {C.DIM}Use IDs 51+ for extended modules{C.RESET}")
                        selected = _pick_targets_from_input("Enter module IDs to start")
                        if selected: start_nodes(selected)
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "2":
                        os.system("clear"); draw_dashboard(); show_location_list()
                        print(f"  {C.DIM}Use IDs 51+ for extended modules{C.RESET}")
                        selected = _pick_targets_from_input("Enter module IDs to stop")
                        if selected: stop_nodes(selected)
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "3":
                        os.system("clear"); draw_dashboard(); show_location_list()
                        print(f"  {C.DIM}Use IDs 51+ for extended modules{C.RESET}")
                        selected = _pick_targets_from_input("Enter module IDs to restart")
                        if selected: restart_nodes(selected)
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "4":
                        installed = {nid: d for nid, d in ALL_LOCATIONS.items()
                                     if node_is_installed(d["iso"])}
                        if installed: start_nodes(installed)
                        else: print(f"\n  {C.RED}✘  No modules deployed{C.RESET}")
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "5":
                        installed = {nid: d for nid, d in ALL_LOCATIONS.items()
                                     if node_is_installed(d["iso"])}
                        if installed: stop_nodes(installed)
                        else: print(f"\n  {C.RED}✘  No modules deployed{C.RESET}")
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "6":
                        installed = {nid: d for nid, d in ALL_LOCATIONS.items()
                                     if node_is_installed(d["iso"])}
                        if installed: restart_nodes(installed)
                        else: print(f"\n  {C.RED}✘  No modules deployed{C.RESET}")
                        input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "7":
                        os.system("clear"); draw_dashboard(); show_location_list()
                        print(f"  {C.DIM}Use IDs 51+ for extended modules{C.RESET}")
                        try:
                            ids_input = input(
                                f"\n  {C.YELLOW}Enter module IDs to remove: {C.RESET}"
                            ).strip()
                            ids     = [int(x.strip()) for x in ids_input.split(",")]
                            targets = {i: ALL_LOCATIONS[i] for i in ids if i in ALL_LOCATIONS}
                            if targets:
                                print()
                                removed = _remove_targets(targets)
                                print(f"\n  {C.GREEN}✔  {removed} module(s) removed{C.RESET}")
                            input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                        except ValueError:
                            print(f"\n  {C.RED}✘  Invalid input{C.RESET}")
                            input(f"\n{C.DIM}  Press Enter...{C.RESET}")
                    elif sub == "8":
                        remove_all_nodes()
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            # ── 5: Monitoring & Diagnostics ───────────────────────────────────
            elif choice == "5":
                while True:
                    draw_dashboard(); show_submenu_5()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1": show_status()
                    elif sub == "2": health_check()
                    elif sub == "3":
                        _exit_cache.clear()
                        fetch_all_exit_counts()
                        print(f"\n  {C.GREEN}✔  Relay density data refreshed{C.RESET}")
                        time.sleep(1)
                    elif sub == "4": show_exit_ips()
                    elif sub == "5": diagnose_node()
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            # ── 6: IP & Routing ───────────────────────────────────────────────
            elif choice == "6":
                while True:
                    draw_dashboard(); show_submenu_6()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1": download_node()
                    elif sub == "2": live_ip_panel()
                    elif sub == "3": rotate_ips()
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            # ── 7: Automation & Guardian ──────────────────────────────────────
            elif choice == "7":
                while True:
                    draw_dashboard(); show_submenu_7()
                    sub = input(f"\n  {C.YELLOW}Enter option: {C.RESET}").strip()
                    if sub == "0": break
                    elif sub == "1": setup_auto_restart()
                    elif sub == "2": disable_auto_restart()
                    elif sub == "3": start_cpu_guardian()
                    elif sub == "4": stop_cpu_guardian()
                    elif sub == "5": show_guardian_status()
                    else:
                        print(f"\n  {C.RED}✘  Invalid option{C.RESET}"); time.sleep(1)

            else:
                print(f"\n  {C.RED}✘  Invalid option — please try again.{C.RESET}")
                time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}✘  Interrupted by user.{C.RESET}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()

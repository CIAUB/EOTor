"""The 213 location tables (50 primary + extended) and flag emoji."""

from .config import DISPLAY_CONF_NAME, DISPLAY_INSTANCE_DIR


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


def flag_emoji(iso: str) -> str:
    return _FLAG_MAP.get(iso.lower(), "🌐")


def _display_instance_path(iso: str) -> str:
    """Return user-facing path for a location config (alias only)."""
    return f"{DISPLAY_INSTANCE_DIR}/{iso}/{DISPLAY_CONF_NAME}"


def display_node_name(iso: str) -> str:
    """Return EOTor-branded node name, e.g. eotor_de."""
    return f"eotor_{iso.lower()}"


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

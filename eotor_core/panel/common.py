"""Shared panel constants, location mapping and helpers."""

import json
import os

from ..locations import ALL_LOCATIONS, flag_emoji, LOCATIONS
from ..system import node_is_installed


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


def load_requests():
    try:
        import requests
        import urllib3
    except ImportError:
        raise PanelError("Python package 'requests' is missing — run: "
                         "pip3 install --break-system-packages requests")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return requests


def panel_countries(extended: bool = False):
    """Locations with their panel-side inbound port (primary 50, or all when extended)."""
    source = ALL_LOCATIONS if extended else LOCATIONS
    return [{"id": nid, "code": d["iso"], "name": d["name"], "flag": flag_emoji(d["iso"]),
             "out_port": d["port"], "in_port": PANEL_IN_PORT_BASE + nid}
            for nid, d in source.items()]


def panel_inbound_tag(c) -> str:
    return f"{c['flag']} {c['name']}"


def panel_outbound_tag(c, prefix=PANEL_OUTBOUND_PREFIX) -> str:
    return f"{prefix}-{c['code'].upper()}"


def panel_outbound_tags(c) -> list:
    return [panel_outbound_tag(c, p) for p in (PANEL_OUTBOUND_PREFIX, *PANEL_LEGACY_PREFIXES)]


def deployed_panel_countries(extended: bool = False):
    return [c for c in panel_countries(extended) if node_is_installed(c["code"])]


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
                lo, hi = sorted(int(x) for x in part.split("-", 1))
                chosen.update(range(max(lo, 1), min(hi, limit) + 1))
            elif 1 <= int(part) <= limit:
                chosen.add(int(part))
        except ValueError:
            continue
    return sorted(chosen)


def json_field(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def write_private(path, text):
    """Write a secrets file readable by its owner only (never world-readable, not even briefly)."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(text)
        return True
    except OSError:
        return False

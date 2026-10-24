"""Exit-IP and server-info lookups, relay counts."""

import concurrent.futures
import ipaddress
import json
import time
import urllib.request

from .config import exit_cache, LOW_EXIT_NODES, MIN_EXIT_NODES
from .locations import ALL_LOCATIONS
from .system import run_out
from .theme import C
from .ui import spin


def get_exit_node_count(iso: str) -> int:
    if iso in exit_cache:
        return exit_cache[iso]
    try:
        url = f"https://onionoo.torproject.org/summary?flag=Exit&country={iso}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            d     = json.loads(r.read().decode())
            count = len(d.get("relays", []))
            exit_cache[iso] = count
            return count
    except:
        exit_cache[iso] = -1
        return -1


def fetch_all_exit_counts(quiet: bool = False):
    isos = list({d["iso"] for d in ALL_LOCATIONS.values() if d["iso"] not in exit_cache})
    if not isos:
        return
    if not quiet:
        print(f"\n{C.DIM}  {spin()}  Fetching location availability data...{C.RESET}",
              flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        list(pool.map(get_exit_node_count, isos))


def ec_badge(iso: str) -> str:
    n = exit_cache.get(iso, -1)
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


_server_info_cache = {"at": 0.0, "value": None}


def clean_text(value) -> str:
    """Strip control characters from text that came from the network."""
    return "".join(ch for ch in str(value or "") if ch.isprintable())


def valid_ip(value) -> str:
    """Return the canonical IP string, or '' when value is not an IP address."""
    try:
        return str(ipaddress.ip_address(str(value).strip()))
    except ValueError:
        return ""


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
                ip = valid_ip(d.get("query"))
                if ip:
                    return (ip,
                            clean_text(f"{d.get('city')}, {d.get('country')}"),
                            clean_text(d.get("isp")))
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
                return valid_ip(d.get("query")) or None
    except (ValueError, OSError):
        pass
    return None

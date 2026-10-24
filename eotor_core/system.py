"""Shell helpers, systemd unit state and torrc files."""

import os
import re
import subprocess
import sys
import time

from .config import BRAND_NAME, INTERNAL_INSTANCE_DIR
from .locations import ALL_LOCATIONS
from .theme import C


def run_cmd(cmd):
    return subprocess.run(cmd, shell=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_out(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def check_root():
    if os.geteuid() != 0:
        print(f"\n{C.RED}  ✘  Permission denied — {BRAND_NAME} must be run as root.{C.RESET}\n")
        sys.exit(1)


INSTALL_PATH  = "/usr/local/bin/eotor"
LAUNCHER_MARK = "# eotor-launcher"


def launcher_text(script_path: str) -> str:
    return f'#!/bin/sh\n{LAUNCHER_MARK}\nexec python3 "{script_path}" "$@"\n'


def launcher_is_healthy(path: str) -> bool:
    """True when `path` is one of our launchers and the script it runs still exists."""
    try:
        with open(path) as f:
            text = f.read()
    except OSError:
        return False
    target = re.search(r'^exec python3 "(.+)" "\$@"$', text, re.M)
    return LAUNCHER_MARK in text and bool(target) and os.path.isfile(target.group(1))


def self_install() -> bool:
    """Register the `eotor` command. Replaces a missing, stale or legacy single-file copy."""
    script_path = os.path.realpath(sys.argv[0])
    if not os.path.isfile(script_path) or launcher_is_healthy(INSTALL_PATH):
        return False
    try:
        with open(INSTALL_PATH, "w") as f:
            f.write(launcher_text(script_path))
        os.chmod(INSTALL_PATH, 0o755)
    except OSError:
        return False
    print(f"  {C.GREEN}✔{C.RESET}  Registered as a system command. "
          f"{C.DIM}You can now run:{C.RESET} {C.WHITE}eotor{C.RESET}")
    time.sleep(1.2)
    return True


def node_is_installed(iso):
    return os.path.exists(f"{INTERNAL_INSTANCE_DIR}/{iso}/torrc")


def node_is_running(iso):
    return run_out(f"systemctl is-active tor@{iso}").stdout.strip() == "active"


def running_isos() -> set:
    """All active tor@<iso> units in one systemctl call (used for bulk displays)."""
    r = run_out("systemctl list-units 'tor@*.service' --state=active --plain --no-legend --no-pager")
    return {m.group(1) for m in re.finditer(r"^\s*tor@([\w-]+)\.service", r.stdout, re.M)}


def running_locations() -> dict:
    live = running_isos()
    return {nid: d for nid, d in ALL_LOCATIONS.items() if d["iso"] in live}


def localize_torrc_text(text: str) -> str:
    return re.sub(r"^(SocksPort\s+)0\.0\.0\.0:", r"\g<1>127.0.0.1:", text, flags=re.M)


def _torrc_path(iso: str) -> str:
    return f"{INTERNAL_INSTANCE_DIR}/{iso}/torrc"


def _read_torrc(iso: str) -> str:
    try:
        with open(_torrc_path(iso)) as f:
            return f.read()
    except OSError:
        return ""


def exposed_modules() -> list:
    """Installed modules whose SOCKS port listens on all interfaces."""
    return [d["iso"] for d in ALL_LOCATIONS.values()
            if node_is_installed(d["iso"])
            and re.search(r"^SocksPort\s+0\.0\.0\.0:", _read_torrc(d["iso"]), re.M)]


def localize_installed_torrcs() -> list:
    """Rewrite world-bound SocksPort lines to 127.0.0.1. Returns the changed ISOs."""
    changed = []
    for iso in exposed_modules():
        text = localize_torrc_text(_read_torrc(iso))
        try:
            with open(_torrc_path(iso), "w") as f:
                f.write(text)
            changed.append(iso)
        except OSError:
            pass
    return changed


def write_torrc(iso: str, port: int, strict: bool = True):
    strict_val = "1" if strict else "0"
    try:
        with open(_torrc_path(iso), "w") as f:
            f.write(
                f"SocksPort 127.0.0.1:{port}\n"
                f"ExitNodes {{{iso}}}\n"
                f"StrictNodes {strict_val}\n"
            )
    except Exception as e:
        print(f"\n  {C.RED}✘  Configuration write error: {e}{C.RESET}")

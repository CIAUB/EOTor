"""Start, stop, restart, remove and inspect modules."""

import time

from .config import exit_cache, INTERNAL_INSTANCE_DIR, INTERNAL_VARLIB_DIR
from .dashboard import draw_dashboard, show_location_list
from .deploy import parse_ids
from .locations import ALL_LOCATIONS, flag_emoji
from .system import node_is_installed, node_is_running, run_cmd, running_isos
from .theme import C
from .ui import ask, clip, divider_line, fail, note, ok, pad, pause, screen_title, table_lines


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


def remove_targets(targets: dict) -> int:
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
        run_cmd(f"rm -rf {INTERNAL_INSTANCE_DIR}/{iso}")
        run_cmd(f"rm -rf {INTERNAL_VARLIB_DIR}/{iso}")
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
    removed = remove_targets(installed)
    print(f"\n  {C.GREEN}✔  {removed} module(s) removed.{C.RESET}")
    pause()


def show_status():
    draw_dashboard()
    screen_title("📡", "MODULE STATUS")
    running = running_isos()
    rows = []
    for nid, d in ALL_LOCATIONS.items():
        iso = d["iso"]
        n   = exit_cache.get(iso, -1)
        ec  = f"{n}" if n >= 0 else "?"
        if not node_is_installed(iso):
            status = f"{C.DIM}○ not deployed{C.RESET}"
        elif iso in running:
            status = f"{C.GREEN}● running{C.RESET}"
        else:
            status = f"{C.RED}● stopped{C.RESET}"
        rows.append([f"{C.ACCENT}{nid}{C.RESET}", f"{flag_emoji(iso)} {d['name']}",
                     f"{C.TEAL}{d['port']}{C.RESET}", ec, status])
    print("\n".join(table_lines(["#", "Location", "Port", "Relays", "Status"], rows, "><>><")))
    pause()


def health_check():
    draw_dashboard()
    screen_title("🩺", "CONNECTIVITY HEALTH CHECK", C.PURPLE)
    passed = failed = 0
    running = running_isos()
    for nid, d in ALL_LOCATIONS.items():
        iso, port = d["iso"], d["port"]
        if iso not in running:
            continue
        label = pad(f"{flag_emoji(iso)} {clip(d['name'].upper(), 24)}", 30)
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
    print(f"  {divider_line('─', 40)}")
    print(f"  {C.GREEN}{passed} passed{C.RESET}   {C.DIM}│{C.RESET}   {C.RED}{failed} failed{C.RESET}")
    pause()


def control_by_ids(action, prompt):
    draw_dashboard()
    show_location_list()
    note("Use IDs 51+ for extended modules")
    selected = _pick_targets_from_input(prompt)
    if selected:
        action(selected)
    pause()


def control_all(action):
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
        ids = parse_ids(ask("Module IDs to remove"))
    except ValueError:
        fail("Invalid input")
        return pause()
    targets = {i: ALL_LOCATIONS[i] for i in ids if i in ALL_LOCATIONS}
    if targets:
        print()
        removed = remove_targets(targets)
        print()
        ok(f"{removed} module(s) removed")
    pause()

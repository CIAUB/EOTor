"""Live exit IPs and IP rotation."""

import concurrent.futures
import sys
import time
from datetime import datetime

from .config import exit_cache, ip_cache, ip_lock, PARALLEL_WORKERS
from .dashboard import draw_dashboard, show_location_list
from .locations import ALL_LOCATIONS, flag_emoji
from .network import fetch_all_exit_counts, get_node_exit_ip
from .system import node_is_installed, node_is_running, run_cmd, running_locations
from .theme import C
from .ui import (
    clear_screen,
    clip,
    fail,
    fixed_row,
    fixed_rule,
    note,
    ok,
    pause,
    screen_title,
    table_lines,
)


def _fetch_ip_task(nid, d):
    iso  = d["iso"]
    port = d["port"]
    name = d["name"]
    if not node_is_running(iso):
        return nid, name, None, "not_running"
    ip = get_node_exit_ip(port, timeout=15)
    with ip_lock:
        ip_cache[nid] = {"name": name, "port": port, "ip": ip, "time": datetime.now()}
    return nid, name, ip, "ok" if ip else "failed"


def live_ip_panel():
    draw_dashboard()
    running = running_locations()
    if not running:
        fail("No active modules.")
        pause()
        return
    screen_title("🌐", f"LIVE IP PANEL · {len(running)} active modules")
    widths, aligns = [4, 28, 5, 22, 10], "><><<"
    print(f"{C.DIM}{fixed_row(['#', 'Location', 'Port', 'Exit IP', 'Status'], widths, aligns)}{C.RESET}")
    print(fixed_rule(widths))
    ip_cache.clear()

    def display_ip(nid):
        while nid not in ip_cache:
            time.sleep(0.05)
        data = ip_cache[nid]
        flag = flag_emoji(ALL_LOCATIONS[nid]["iso"])
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
    success_count = sum(1 for v in ip_cache.values() if v.get("ip"))
    print(f"\n  {C.GREEN}{success_count}/{len(running)}{C.RESET} modules responding")
    pause()


def show_exit_ips():
    draw_dashboard()
    screen_title("🌍", "EXIT IP MAP · current routing endpoints", C.PURPLE)
    running = running_locations()
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
        rows.append([f"{C.ACCENT}{nid}{C.RESET}", f"{flag_emoji(d['iso'])} {d['name']}",
                     f"{C.DIM}{d['port']}{C.RESET}", ip_cell, f"{C.DIM}{stamp}{C.RESET}", tag])
    print("\n".join(table_lines(["#", "Location", "Port", "Exit IP", "Updated", ""], rows, "><><<<")))

    show_exit_ips.prev_ips = results
    success = sum(1 for ip in results.values() if ip)
    changed = sum(1 for nid in results
                  if old_ips.get(nid) and results.get(nid) and old_ips[nid] != results[nid])
    print(f"\n  {C.GREEN}{success}/{len(running)}{C.RESET} responding", end="")
    print(f"   {C.DIM}│{C.RESET}   {C.YELLOW}{changed}{C.RESET} endpoint(s) changed since last check" if changed else "")
    pause()


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
        print(f"  {flag_emoji(iso)} {d['name']:<25}  {ip if ip else 'N/A':<20}")
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
        print(f"  {flag_emoji(iso)} {d['name']:<23}  {old_disp}  {new_disp}  {changed_tag}")
        return nid, ip

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda item: _get_new_ip(item[0], item[1]), targets.items()))

    print(f"  {'─' * 78}")
    changed = sum(1 for nid in targets.keys()
                  if old_ips.get(nid) and new_ips.get(nid)
                  and old_ips[nid] != new_ips[nid])
    print(f"\n  {C.GREEN}{changed}/{len(targets)} endpoints rotated successfully{C.RESET}")
    pause()


def refresh_relay_density():
    exit_cache.clear()
    fetch_all_exit_counts()
    ok("Relay density data refreshed")
    time.sleep(1)

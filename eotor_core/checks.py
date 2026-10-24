"""Leak, blacklist and per-node diagnostics."""

import concurrent.futures
import ipaddress
import json
import time

from .config import exit_cache, LOW_EXIT_NODES, MIN_EXIT_NODES, PARALLEL_WORKERS
from .dashboard import draw_dashboard, show_location_list
from .deploy import check_exit_stable, wait_bootstrap
from .locations import ALL_LOCATIONS, flag_emoji
from .network import get_exit_node_count, get_node_exit_ip
from .system import node_is_installed, run_cmd, run_out, running_locations, write_torrc
from .theme import C
from .ui import (
    box_lines,
    clear_screen,
    divider_line,
    fail,
    note,
    pause,
    screen_title,
    table_lines,
    warn,
)


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
        addr = ipaddress.ip_address(ip)
        if addr.version != 4:
            return False, ""
        rev_ip = ".".join(reversed(str(addr).split(".")))
        r = run_out(f"dig +short +time=5 +tries=1 {rev_ip}.zen.spamhaus.org")
        if r.returncode == 0 and r.stdout.strip():
            out = r.stdout.strip()
            if "127.0.0" in out:
                code = out.splitlines()[0].strip()
                return True, f"Spamhaus ZEN ({code})"
        return False, ""
    except (ValueError, OSError):
        return False, ""


def check_ip_leak_and_block():
    """Scan all active Tor nodes for blacklist, DNS leak, and Tor verification."""
    draw_dashboard()
    screen_title("🔒", "IP LEAK & BLOCK CHECK")

    running = running_locations()
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
            "nid": nid, "iso": iso, "name": d["name"], "flag": flag_emoji(iso),
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
    flag = flag_emoji(iso)
    print(f"\n  {C.CYAN}{'═' * 66}{C.RESET}")
    print(f"  {C.CYAN}  DIAGNOSING {flag} {name} ({iso.upper()})  —  port {port}{C.RESET}")
    print(f"  {C.CYAN}{'═' * 66}{C.RESET}\n")

    print(f"  {C.DIM}[1/5] Checking relay density for this location...{C.RESET}")
    exit_cache.pop(iso, None)
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
    pct = wait_bootstrap(iso, port, name, timeout=180, attempt=1, verbose=True)
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
    stable = check_exit_stable(port) if ip else False
    if ip:
        tag = "stable" if stable else "UNSTABLE"
        col = C.GREEN if stable else C.YELLOW
        print(f"    {col}✔  Exit endpoint: {ip}  ({tag}){C.RESET}")
    else:
        print(f"    {C.RED}✘  Could not determine exit endpoint{C.RESET}")

    print(f"\n  {divider_line('─', 66)}")
    if conn_ok and ip and stable:
        write_torrc(iso, port, strict=True)
        run_cmd(f"systemctl reload tor@{iso}")
        print(f"  {C.GREEN}✔  {flag} {name} is healthy and routing correctly.{C.RESET}")
    else:
        print(f"  {C.YELLOW}⚠  {flag} {name} left in RELAXED routing mode.{C.RESET}")
    print(f"  {divider_line('─', 66)}")
    pause()

"""Deploying location modules (single, parallel, extended)."""

import concurrent.futures
import re
import sys
import threading
import time

from .config import (
    BRAND_NAME,
    exit_cache,
    EXTEND_PCT,
    FAST_TIMEOUT,
    FAST_TIMEOUT_EXT,
    FINAL_VERIFY_WAIT,
    LOW_EXIT_NODES,
    MAX_FAST_RETRIES,
    MIN_EXIT_NODES,
    PARALLEL_WORKERS,
    report_data,
    report_lock,
    STABILITY_CHECKS,
    STABILITY_DELAY,
    TIMEOUT_LOW,
    TIMEOUT_NORMAL,
)
from .dashboard import draw_dashboard, show_global_location_list, show_location_list
from .locations import ALL_LOCATIONS, flag_emoji, GLOBAL_LOCATIONS, LOCATIONS
from .network import get_exit_node_count, get_node_exit_ip
from .report import print_report
from .system import node_is_installed, run_cmd, run_out, running_isos, write_torrc
from .theme import C
from .ui import (
    ask,
    box_lines,
    clear_screen,
    fail,
    note,
    ok,
    pause,
    progress_bar,
    spin,
    table_lines,
    term_width,
)


_deployment_progress = {
    "total": 0, "completed": 0, "success": 0, "failed": 0, "current_nodes": {}
}
_progress_lock  = threading.Lock()
_display_thread = None
_display_active = False


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
                 f"{C.ACCENT}{spin()}{C.RESET}")
        rows = ["", f"  {progress_bar(int(completed / total * 100), w - 14)}", stats, ""]
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


def wait_bootstrap(iso: str, port: int, label: str,
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
            bar     = progress_bar(percent)
            ext_tag = f" {C.DIM}(extended){C.RESET}" if extended else ""
            print(f"\r  {C.CYAN}{label:<22}{C.RESET}  {bar}{suffix}{ext_tag}\033[K",
                  end="", flush=True)
        else:
            bar     = progress_bar(percent, width=18)
            ext_tag = f" {C.DIM}ext{C.RESET}" if extended else ""
            _update_node_status(iso,
                f"{C.CYAN}{label:<22}{C.RESET} {bar}{suffix}{ext_tag}")
        if percent == 100:
            break
    if percent == 100:
        if verbose:
            print(f"\r  {C.CYAN}{label:<22}{C.RESET}  "
                  f"{progress_bar(100)} "
                  f"{C.YELLOW}⏳ Finalizing...{C.RESET}\033[K",
                  end="", flush=True)
        else:
            _update_node_status(iso,
                f"{C.CYAN}{label:<22}{C.RESET} {progress_bar(100, 18)} "
                f"{C.YELLOW}⏳ Finalizing{C.RESET}")
        time.sleep(FINAL_VERIFY_WAIT)
    return percent


def check_exit_stable(port: int, checks: int = STABILITY_CHECKS,
                       delay: float = STABILITY_DELAY) -> bool:
    for _ in range(checks):
        time.sleep(delay)
        r = run_cmd(f"curl -s -m 8 --socks5-hostname 127.0.0.1:{port} "
                    f"https://www.google.com/generate_204")
        if r.returncode != 0:
            return False
    return True


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
        with report_lock:
            report_data["WARNED"].append(f"{name} ({exit_count} relays)")

    run_cmd(f"tor-instance-create {iso}")
    write_torrc(iso, port, strict=True)

    success  = False
    exit_ip  = None
    best_pct = 0

    for attempt in range(1, MAX_FAST_RETRIES + 1):
        pct = wait_bootstrap(iso, port, label, FAST_TIMEOUT, attempt,
                              extended_timeout=FAST_TIMEOUT_EXT, verbose=verbose)
        best_pct = max(best_pct, pct)
        if pct == 100:
            verify_msg = (f"{C.CYAN}{name:<22}{C.RESET} "
                          f"{progress_bar(100, 18)} "
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
                if candidate_ip and check_exit_stable(port):
                    exit_ip = candidate_ip
                    success = True
                    if attempt > 1:
                        with report_lock:
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
        pct = wait_bootstrap(iso, port, label, timeout,
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
                if candidate_ip and check_exit_stable(port):
                    exit_ip = candidate_ip
                    success = True
                    with report_lock:
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
        with report_lock:
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
        with report_lock:
            report_data["FAILED"].append(f"{name} (:{port}) [peak {best_pct}%]")
    if not verbose:
        _mark_node_complete(iso, success)


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
        iso, ec = d["iso"], exit_cache.get(d["iso"], -1)
        if iso in live:
            state = f"{C.GREEN}● running{C.RESET}"
        elif node_is_installed(iso):
            state = f"{C.YELLOW}● stopped{C.RESET}"
        else:
            state = f"{C.DIM}○ not deployed{C.RESET}"
        rows.append([f"{C.ACCENT}{nid}{C.RESET}", f"{flag_emoji(iso)} {d['name']}",
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

    print(f"\n  {C.CYAN}⚡  Deploying {flag_emoji(iso)} {name} (port {port})...{C.RESET}\n")
    deploy_node_task(d, verbose=True)
    print_report()
    pause()


def _deploy_selection(selected: dict):
    if len(selected) == 1:
        deploy_node_task(next(iter(selected.values())), verbose=True)
    else:
        deploy_nodes_parallel(selected)
    print_report()
    pause()


def parse_ids(text: str) -> list:
    return [int(x.strip()) for x in text.split(",")]


def install_primary_by_ids():
    draw_dashboard()
    show_location_list()
    try:
        ids = parse_ids(ask("Module IDs to install (e.g. 1,4,12)"))
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

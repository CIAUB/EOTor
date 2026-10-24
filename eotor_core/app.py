"""Main menu wiring and entry point."""

import sys
import threading

from .automation import (
    disable_auto_restart,
    setup_auto_restart,
    show_guardian_status,
    start_cpu_guardian,
    stop_cpu_guardian,
)
from .checks import check_ip_leak_and_block, diagnose_node
from .config import BRAND_NAME, BRAND_VERSION
from .control import (
    control_all,
    control_by_ids,
    health_check,
    remove_all_nodes,
    remove_by_ids,
    restart_nodes,
    show_status,
    start_nodes,
    stop_nodes,
)
from .dashboard import guardian_badge, run_menu
from .deploy import (
    download_node,
    install_all_primary,
    install_global_nodes,
    install_primary_by_ids,
    reinstall_failed,
    search_and_install_global,
    show_extended_list,
)
from .engine import engine_install, engine_localize, engine_uninstall, engine_update
from .ips import live_ip_panel, refresh_relay_density, rotate_ips, show_exit_ips
from .locations import GLOBAL_LOCATIONS
from .network import fetch_all_exit_counts
from .panel.flows import panel_integration_menu
from .report import reset_report
from .system import check_root, self_install
from .theme import C


def _submenu(title, items, handlers, subtitle=None):
    def run():
        reset_report()
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
            ("4", "Bind SOCKS to localhost", "close ports to the internet"),
            None, ("0", "Back")],
            {"1": engine_install, "2": engine_update, "3": engine_uninstall,
             "4": engine_localize}),

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
            {"1": lambda: control_by_ids(start_nodes, "Module IDs to start"),
             "2": lambda: control_by_ids(stop_nodes, "Module IDs to stop"),
             "3": lambda: control_by_ids(restart_nodes, "Module IDs to restart"),
             "4": lambda: control_all(start_nodes),
             "5": lambda: control_all(stop_nodes),
             "6": lambda: control_all(restart_nodes),
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

        "7": _submenu(lambda: f"AUTOMATION & GUARDIAN · CPU Guardian {guardian_badge()}", [
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
        threading.Thread(target=fetch_all_exit_counts, kwargs={"quiet": True}, daemon=True).start()
        reset_report()
        run_menu(lambda: f"MAIN MENU · {BRAND_NAME} {BRAND_VERSION}", MAIN_ITEMS, build_main_handlers())
        print(f"\n  {C.ACCENT}Goodbye — {BRAND_NAME} shutting down.{C.RESET}\n")
    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}✘  Interrupted by user.{C.RESET}\n")
    sys.exit(0)

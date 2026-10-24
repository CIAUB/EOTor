"""System dashboard, location lists and the data-driven menu runner."""

import time
from datetime import datetime

from .config import guardian
from .locations import ALL_LOCATIONS, flag_emoji, GLOBAL_LOCATIONS, LOCATIONS
from .network import ec_badge, get_server_info
from .panel.common import detect_panels
from .system import exposed_modules, node_is_installed, running_isos
from .theme import C
from .ui import (
    ask,
    box_lines,
    clear_screen,
    clip,
    fail,
    menu_lines,
    pad,
    print_logo,
    progress_bar,
    status_led,
    term_width,
)


def _os_name() -> str:
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME"):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "Linux"


def draw_dashboard():
    clear_screen()
    print_logo()

    ip, loc, isp = get_server_info()
    all_isos      = {d["iso"] for d in ALL_LOCATIONS.values()}
    inst_count    = sum(1 for iso in all_isos if node_is_installed(iso))
    running_count = len(running_isos() & all_isos)
    total_count   = len(ALL_LOCATIONS)
    guardian_on   = guardian.running()

    w    = term_width()
    half = (w - 2) // 2

    def kv(key, value, room):
        return f"{C.PURPLE}{key:<9}{C.RESET}{clip(value, room - 9)}"

    def two(left, right):
        return "  " + pad(left, half - 2) + right

    panels = "   ".join(f"{name} {status_led(found)}" for name, found in detect_panels())
    rows = [
        two(kv("IP", f"{C.TEAL}{ip}{C.RESET}", half), kv("ISP", isp, half)),
        two(kv("Location", loc, half), kv("OS", _os_name(), half)),
        two(kv("Time", datetime.now().strftime("%Y-%m-%d  %H:%M"), half),
            kv("Guardian", f"{status_led(guardian_on)} {'ON' if guardian_on else 'OFF'}", half)),
        "─",
        "  " + kv("Modules", f"{C.WHITE}{inst_count}{C.RESET}{C.DIM}/{total_count} deployed{C.RESET}  "
                            f"{progress_bar(int(inst_count / total_count * 100), 16, C.ACCENT)}", w),
        "  " + kv("Active", f"{C.GREEN if running_count else C.DIM}{running_count}{C.RESET}"
                           f"{C.DIM}/{total_count} running{C.RESET}", w),
        "  " + kv("Panels", panels, w),
    ]
    exposed = exposed_modules()
    if exposed:
        rows.append("  " + kv("Security", f"{C.YELLOW}{len(exposed)} module(s) listen on 0.0.0.0{C.RESET}"
                                          f"{C.DIM}  ·  Setup & Engine ➔ [4]{C.RESET}", w))
    print("\n".join("  " + l for l in box_lines("SYSTEM", rows, w)))


def show_location_list(loc_dict=None, title=None):
    if loc_dict is None:
        loc_dict = LOCATIONS
    if title is None:
        title = "PRIMARY LOCATION MODULES · ports 9080–9129"

    running = running_isos()
    w       = term_width()
    ncols   = 2 if w >= 96 else 1
    cell_w  = (w - 4) // ncols

    def cell(nid, d):
        iso = d["iso"]
        if iso in running:
            led = f"{C.GREEN}●{C.RESET}"
        elif node_is_installed(iso):
            led = f"{C.YELLOW}●{C.RESET}"
        else:
            led = f"{C.DIM}○{C.RESET}"
        text = (f"{C.ACCENT}{nid:>3}{C.RESET}  {led} {flag_emoji(iso)} "
                f"{C.WHITE}{pad(clip(d['name'], 22), 22)}{C.RESET} "
                f"{C.DIM}:{C.TEAL}{d['port']}{C.RESET} {ec_badge(iso)}")
        return pad(text, cell_w)

    items = list(loc_dict.items())
    per   = (len(items) + ncols - 1) // ncols
    cols  = [items[i * per:(i + 1) * per] for i in range(ncols)]
    rows  = []
    for r in range(per):
        rows.append(" " + "".join(cell(*col[r]) for col in cols if r < len(col)))
    rows += ["─",
             f" {C.GREEN}●{C.RESET}{C.DIM} running   {C.RESET}{C.YELLOW}●{C.RESET}{C.DIM} stopped   "
             f"{C.RESET}{C.DIM}○ not deployed    relays: {C.RESET}"
             f"{C.GREEN}10+{C.RESET} {C.YELLOW}3–9{C.RESET} {C.RED}<3{C.RESET}"]
    print("\n".join("  " + l for l in box_lines(title, rows, w)))


def show_global_location_list():
    draw_dashboard()
    show_location_list(
        loc_dict=GLOBAL_LOCATIONS,
        title=f"EXTENDED LOCATION MODULES · ports 9130–{9130 + len(GLOBAL_LOCATIONS) - 1}"
    )


def show_menu(title, items, subtitle=None):
    print()
    print("\n".join("  " + l for l in menu_lines(title, items, term_width(), subtitle)))


def run_menu(title, items, handlers, subtitle=None):
    """Draw dashboard + menu, dispatch on the chosen key; '0' goes back."""
    while True:
        draw_dashboard()
        show_menu(title() if callable(title) else title, items, subtitle)
        choice = ask("Select option").lower()
        if choice == "0":
            return
        handler = handlers.get(choice)
        if handler is None:
            fail("Invalid option")
            time.sleep(1)
        else:
            handler()


def guardian_badge() -> str:
    on = guardian.running()
    return f"{status_led(on)} {'ON' if on else 'OFF'}"

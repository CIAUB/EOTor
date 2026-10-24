"""Tor engine install, update, uninstall and SOCKS localhost migration."""

from .config import BRAND_NAME
from .control import remove_targets
from .dashboard import draw_dashboard
from .locations import ALL_LOCATIONS
from .system import (
    exposed_modules,
    localize_installed_torrcs,
    node_is_installed,
    run_cmd,
    run_out,
    running_isos,
)
from .theme import C
from .ui import (
    animate_install_step,
    clear_screen,
    confirm,
    divider_line,
    note,
    ok,
    pause,
    print_logo,
    screen_title,
    warn,
)


def engine_install():
    clear_screen()
    print_logo()
    print(f"{divider_line()}")
    print(f"  {C.WHITE}INSTALLING {BRAND_NAME.upper()} CORE{C.RESET}")
    print(f"{divider_line()}\n")

    steps = [
        "Initializing EOTor Engine Runtime",
        "Checking System Prerequisites",
        "Refreshing Package Database",
        "Installing Core Components",
        "Disabling Conflicting Services",
        "Verifying Installation Integrity",
    ]

    animate_install_step(steps[0], 0.4)

    run_cmd("dpkg --configure -a")
    animate_install_step(steps[1], 0.3)

    run_cmd("apt-get update -qq")
    animate_install_step(steps[2], 0.4)

    missing = [p for p in ["tor", "tor-geoipdb", "curl"]
               if run_cmd(f"dpkg -s {p}").returncode != 0]
    if missing:
        print(f"\n  {C.YELLOW}⚡  Installing missing components: "
              f"{', '.join(missing)}{C.RESET}")
        run_cmd(f"apt-get install -yq {' '.join(missing)}")
    animate_install_step(steps[3], 0.5)

    run_cmd("systemctl stop tor.service")
    run_cmd("systemctl disable tor.service")
    animate_install_step(steps[4], 0.3)

    still_missing = [p for p in ["tor", "tor-geoipdb", "curl"]
                     if run_cmd(f"dpkg -s {p}").returncode != 0]
    animate_install_step(steps[5], 0.3)

    print()
    print(f"  {divider_line('─', 71)}")
    if still_missing:
        print(f"  {C.RED}✘  Some components could not be installed: "
              f"{', '.join(still_missing)}{C.RESET}")
        print(f"  {C.DIM}Check the system package manager for errors.{C.RESET}")
    else:
        print(f"  {C.GREEN}✔  {BRAND_NAME} Core installed successfully.{C.RESET}")
        print(f"  {C.DIM}Default service disabled to prevent port conflicts.{C.RESET}")
    print(f"  {divider_line('─', 71)}")
    pause()


def engine_update():
    clear_screen()
    print_logo()
    print(f"  {C.CYAN}⟳  Updating {BRAND_NAME} Core...{C.RESET}\n")
    animate_install_step("Refreshing Package Sources", 0.4)
    run_cmd("apt-get update -qq")
    animate_install_step("Upgrading Core Components", 0.6)
    run_out("apt-get install -yq --only-upgrade tor tor-geoipdb curl")
    animate_install_step("Verifying Updated Components", 0.3)
    print(f"\n  {C.GREEN}✔  {BRAND_NAME} Core updated successfully.{C.RESET}")
    pause()


def engine_uninstall():
    installed = {nid: d for nid, d in ALL_LOCATIONS.items() if node_is_installed(d["iso"])}
    print(f"\n  {C.RED}⚠   WARNING — This will permanently remove ALL "
          f"{len(installed)} location module(s){C.RESET}")
    print(f"  {C.RED}    and uninstall the {BRAND_NAME} Core from this system.{C.RESET}\n")
    confirm = input(f"  {C.YELLOW}Type 'yes' to confirm: {C.RESET}").strip().lower()
    if confirm != "yes":
        print(f"  {C.DIM}Cancelled.{C.RESET}")
        pause()
        return
    if installed:
        print()
        remove_targets(installed)
    print(f"\n  {C.YELLOW}⟳  Removing core packages...{C.RESET}")
    run_cmd("apt-get purge -yq tor tor-geoipdb")
    run_cmd("apt-get autoremove -yq")
    print(f"\n  {C.GREEN}✔  {BRAND_NAME} Core and all location modules removed.{C.RESET}")
    pause()


def engine_localize():
    draw_dashboard()
    screen_title("🔒", "BIND SOCKS TO LOCALHOST")
    exposed = exposed_modules()
    if not exposed:
        ok("Every module already listens on 127.0.0.1 only.")
        return pause()
    warn(f"{len(exposed)} module(s) accept SOCKS connections from the whole internet.")
    note("Panels on this server keep working (they connect through 127.0.0.1).")
    note("Anything reaching these ports from another machine will stop working.")
    if not confirm("Restrict them to localhost?"):
        return
    changed = localize_installed_torrcs()
    live = running_isos()
    for iso in changed:
        if iso in live:
            run_cmd(f"systemctl restart tor@{iso}")
    ok(f"{len(changed)} module(s) now listen on 127.0.0.1 only.")
    pause()

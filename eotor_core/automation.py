"""Auto-restart timer and the CPU guardian."""

import os
import threading
import time
from datetime import datetime

from .config import BRAND_NAME, guardian, INTERNAL_INSTANCE_DIR
from .dashboard import draw_dashboard
from .locations import ALL_LOCATIONS, flag_emoji
from .system import node_is_installed, node_is_running, run_cmd, run_out
from .theme import C
from .ui import clear_screen, pause


AUTO_RESTART_SCRIPT  = "/usr/local/bin/tor-nodes-auto-restart.sh"
AUTO_RESTART_SERVICE = "/etc/systemd/system/tor-nodes-restart.service"
AUTO_RESTART_TIMER   = "/etc/systemd/system/tor-nodes-restart.timer"


def setup_auto_restart():
    print(f"\n  {C.YELLOW}⟳  Setting up hourly auto-restart via systemd timer...{C.RESET}")
    try:
        with open(AUTO_RESTART_SCRIPT, "w") as f:
            f.write(
                "#!/bin/bash\n"
                f"for d in {INTERNAL_INSTANCE_DIR}/*/; do\n"
                "  iso=$(basename \"$d\")\n"
                "  systemctl restart \"tor@$iso\" 2>/dev/null\n"
                "done\n"
            )
        os.chmod(AUTO_RESTART_SCRIPT, 0o755)
        with open(AUTO_RESTART_SERVICE, "w") as f:
            f.write(
                "[Unit]\n"
                f"Description={BRAND_NAME} — Restart All Location Modules\n\n"
                "[Service]\n"
                "Type=oneshot\n"
                f"ExecStart={AUTO_RESTART_SCRIPT}\n"
            )
        with open(AUTO_RESTART_TIMER, "w") as f:
            f.write(
                "[Unit]\n"
                f"Description={BRAND_NAME} — Hourly Module Restart\n\n"
                "[Timer]\n"
                "OnBootSec=15min\n"
                "OnUnitActiveSec=1h\n"
                "Persistent=true\n\n"
                "[Install]\n"
                "WantedBy=timers.target\n"
            )
        run_cmd("systemctl daemon-reload")
        run_cmd("systemctl enable --now tor-nodes-restart.timer")
        r = run_out("systemctl is-enabled tor-nodes-restart.timer")
        if "enabled" in r.stdout:
            print(f"  {C.GREEN}✔  Hourly auto-restart ENABLED.{C.RESET}")
        else:
            print(f"  {C.RED}✘  Could not confirm timer status.{C.RESET}")
    except Exception as e:
        print(f"  {C.RED}✘  Setup failed: {e}{C.RESET}")
    pause()


def disable_auto_restart():
    print(f"\n  {C.YELLOW}⟳  Disabling hourly auto-restart...{C.RESET}")
    run_cmd("systemctl disable --now tor-nodes-restart.timer")
    for p in (AUTO_RESTART_TIMER, AUTO_RESTART_SERVICE, AUTO_RESTART_SCRIPT):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    run_cmd("systemctl daemon-reload")
    print(f"  {C.GREEN}✔  Auto-restart disabled.{C.RESET}")
    pause()


CPU_GUARDIAN_THRESHOLD  = 80        # % CPU per tor@<iso> process
CPU_GUARDIAN_INTERVAL   = 300       # seconds between checks (5 min)
CPU_GUARDIAN_COOLDOWN   = 3600      # seconds to keep location stopped (1 hour)


def _get_tor_cpu(iso: str) -> float:
    """CPU% of the tor@<iso> main process."""
    try:
        pid = run_out(f"systemctl show tor@{iso} -p MainPID --value").stdout.strip()
        if not pid.isdigit() or pid == "0":
            return 0.0
        ps = run_out(f"ps -p {pid} -o %cpu= --no-headers")
        return float(ps.stdout.strip())
    except (ValueError, OSError):
        return 0.0


def _guardian_loop():
    while guardian.active:
        now = time.time()
        # Re-enable locations whose cooldown has expired
        with guardian.lock:
            to_resume = [iso for iso, until in list(guardian.cooldowns.items())
                         if now >= until]
        for iso in to_resume:
            run_cmd(f"systemctl start tor@{iso}")
            with guardian.lock:
                del guardian.cooldowns[iso]

        # Check CPU for all running locations
        for nid, d in list(ALL_LOCATIONS.items()):
            iso  = d["iso"]
            name = d["name"].upper()
            if not node_is_installed(iso) or not node_is_running(iso):
                continue
            with guardian.lock:
                if iso in guardian.cooldowns:
                    continue   # already in cooldown
            cpu = _get_tor_cpu(iso)
            if cpu >= CPU_GUARDIAN_THRESHOLD:
                run_cmd(f"systemctl stop tor@{iso}")
                resume_at = time.time() + CPU_GUARDIAN_COOLDOWN
                with guardian.lock:
                    guardian.cooldowns[iso] = resume_at
                    ts = datetime.now().strftime("%H:%M:%S")
                    guardian.log.append(
                        f"{ts}  {flag_emoji(iso)} {name:<22}  CPU: {cpu:.1f}%  "
                        f"→ paused 1h"
                    )

        # Sleep in small increments so we can exit promptly
        for _ in range(CPU_GUARDIAN_INTERVAL * 10):
            if not guardian.active:
                break
            time.sleep(0.1)


def start_cpu_guardian():
    global CPU_GUARDIAN_THRESHOLD
    if guardian.running():
        print(f"\n  {C.YELLOW}⚠  CPU Guardian is already running.{C.RESET}")
        pause()
        return
    print(f"\n  {C.CYAN}  CPU GUARDIAN — CONFIGURATION{C.RESET}\n")
    print(f"  {C.DIM}Current defaults:{C.RESET}")
    print(f"    Threshold : {C.WHITE}{CPU_GUARDIAN_THRESHOLD}%{C.RESET} CPU per location")
    print(f"    Interval  : {C.WHITE}{CPU_GUARDIAN_INTERVAL}s{C.RESET} (5 min)")
    print(f"    Cooldown  : {C.WHITE}{CPU_GUARDIAN_COOLDOWN}s{C.RESET} (1 hour)\n")
    thr_in = input(
        f"  {C.YELLOW}CPU threshold % [{CPU_GUARDIAN_THRESHOLD}]: {C.RESET}"
    ).strip()
    if thr_in.isdigit():
        CPU_GUARDIAN_THRESHOLD = max(1, min(99, int(thr_in)))
    guardian.active = True
    guardian.thread = threading.Thread(target=_guardian_loop, daemon=True)
    guardian.thread.start()
    print(f"\n  {C.GREEN}✔  CPU Guardian started — threshold: "
          f"{CPU_GUARDIAN_THRESHOLD}%  │  check every "
          f"{CPU_GUARDIAN_INTERVAL // 60} min  │  pause 1h{C.RESET}")
    pause()


def stop_cpu_guardian():
    if not guardian.running():
        print(f"\n  {C.DIM}CPU Guardian is not running.{C.RESET}")
        pause()
        return
    guardian.active = False
    print(f"\n  {C.GREEN}✔  CPU Guardian stopped.{C.RESET}")
    # Re-enable anything still in cooldown
    with guardian.lock:
        paused = list(guardian.cooldowns.keys())
    for iso in paused:
        run_cmd(f"systemctl start tor@{iso}")
    with guardian.lock:
        guardian.cooldowns.clear()
    if paused:
        print(f"  {C.DIM}Re-enabled {len(paused)} paused location(s).{C.RESET}")
    pause()


def show_guardian_status():
    clear_screen()
    draw_dashboard()
    running = guardian.running()
    state   = (f"{C.GREEN}● RUNNING{C.RESET}" if running
               else f"{C.RED}○ STOPPED{C.RESET}")
    print(f"\n  {C.CYAN}🛡  CPU GUARDIAN STATUS{C.RESET}  —  {state}\n")
    if running:
        print(f"  Threshold : {C.WHITE}{CPU_GUARDIAN_THRESHOLD}%{C.RESET}")
        print(f"  Interval  : {C.WHITE}{CPU_GUARDIAN_INTERVAL // 60} min{C.RESET}")
        print(f"  Cooldown  : {C.WHITE}{CPU_GUARDIAN_COOLDOWN // 60} min{C.RESET}\n")

    with guardian.lock:
        cooldowns = dict(guardian.cooldowns)
        log       = list(guardian.log)

    if cooldowns:
        print(f"  {C.YELLOW}⏸  Currently paused locations:{C.RESET}")
        now = time.time()
        for iso, until in cooldowns.items():
            remaining = max(0, int(until - now))
            mins, secs = divmod(remaining, 60)
            loc = next((d for d in ALL_LOCATIONS.values() if d["iso"] == iso), None)
            name = loc["name"].upper() if loc else iso.upper()
            print(f"    {flag_emoji(iso)} {name:<22}  resumes in {mins}m {secs}s")
    else:
        print(f"  {C.GREEN}✔  No locations currently paused.{C.RESET}")

    if log:
        print(f"\n  {C.DIM}Recent guardian events (last {min(len(log), 20)}):{C.RESET}")
        for entry in log[-20:]:
            print(f"  {C.DIM}{entry}{C.RESET}")
    pause()

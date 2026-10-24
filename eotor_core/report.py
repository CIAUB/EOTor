"""Deployment report."""

from datetime import datetime

from .config import BRAND_NAME, report_data, SESSION_START
from .locations import ALL_LOCATIONS, display_node_name, flag_emoji
from .theme import C
from .ui import box_lines, pad, progress_bar, term_width


def print_report():
    elapsed    = int((datetime.now() - SESSION_START).total_seconds())
    mins, secs = divmod(elapsed, 60)
    good, bad  = report_data["SUCCESS"], report_data["FAILED"]
    total      = len(good) + len(bad)
    pct        = int(len(good) / total * 100) if total else 0
    w          = term_width()

    rows = [f"  {C.DIM}Session time: {mins}m {secs}s{C.RESET}"]
    if report_data["WARNED"]:
        rows += ["", f"  {C.YELLOW}⚠  Warnings{C.RESET}"]
        rows += [f"     {C.YELLOW}⚠{C.RESET}  {n}" for n in report_data["WARNED"]]
    if good:
        retried = set(report_data["RETRIED"])
        rows += ["", f"  {C.GREEN}✔  Deployed ×{len(good)}{C.RESET}"]
        for n in good:
            tag = f" {C.YELLOW}(retry){C.RESET}" if any(n.startswith(r) for r in retried) else ""
            rows.append(f"     {C.GREEN}✔{C.RESET}  {n}{tag}")
    if bad:
        rows += ["", f"  {C.RED}✘  Failed ×{len(bad)}{C.RESET}"]
        rows += [f"     {C.RED}✘{C.RESET}  {n}" for n in bad]
    if total:
        color = C.GREEN if pct >= 80 else (C.YELLOW if pct >= 50 else C.RED)
        rows += ["", f"  {progress_bar(pct, w - 30)}  {color}success rate{C.RESET}"]
    if good:
        rows += ["─", f"  {C.DIM}Deployed location modules{C.RESET}"]
        for entry in good:
            # entry format: "NAME (:PORT) → IP"
            iso_guess = next((d["iso"] for d in ALL_LOCATIONS.values()
                              if d["name"].upper() in entry), "")
            flag       = flag_emoji(iso_guess) if iso_guess else "🌐"
            name_port, _, exit_ip = entry.partition(" → ")
            alias      = display_node_name(iso_guess) if iso_guess else name_port.strip()
            rows.append(f"  {flag}  {C.WHITE}{pad(alias, 18)}{C.RESET}  "
                        f"{C.TEAL}{pad(exit_ip.strip() or '—', 18)}{C.RESET}  {C.GREEN}✔ Ready{C.RESET}")
    print()
    print("\n".join("  " + l for l in box_lines(f"DEPLOYMENT REPORT · {BRAND_NAME}", rows, w)))


def reset_report():
    report_data.update({"SUCCESS": [], "FAILED": [], "SKIPPED": [], "RETRIED": [], "WARNED": []})

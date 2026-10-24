"""Terminal widgets: width-aware boxes, tables, prompts, progress bars."""

import itertools
import re
import shutil
import sys
import time
import unicodedata

from .config import BRAND_DEVELOPER, BRAND_TAGLINE, BRAND_VERSION
from .theme import C, gradient_text


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_spinner_iter   = itertools.cycle(_SPINNER_FRAMES)


def spin() -> str:
    return next(_spinner_iter)


def _bar_color(percent: int) -> str:
    return C.RED if percent < 40 else (C.YELLOW if percent < 80 else C.GREEN)


def progress_bar(percent: int, width: int = 26, color: str = None) -> str:
    filled = int(width * percent / 100)
    color  = color or _bar_color(percent)
    return (f"{color}{'━' * filled}{C.DIM}{'╌' * (width - filled)}{C.RESET} "
            f"{color}{percent:>3}%{C.RESET}")


def _install_bar(percent: int, width: int = 30) -> str:
    return f" {progress_bar(percent, width)}"


def divider_line(char="─", width=None, color=None) -> str:
    color = color or C.DIM
    return f"{color}{char * (width or term_width() - 4)}{C.RESET}"


# ── Width-aware layout helpers ────────────────────────────────────────────────
_ANSI_RE = re.compile(r"\033\[[0-9;?]*[A-Za-z]")


def _char_width(ch: str) -> int:
    o = ord(ch)
    if o == 0x200D or 0xFE00 <= o <= 0xFE0F or unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def vlen(s: str) -> int:
    """Visible terminal width: ANSI codes are free, wide glyphs count as two cells."""
    return sum(_char_width(ch) for ch in _ANSI_RE.sub("", s))


def pad(s: str, width: int, align: str = "<") -> str:
    gap = max(width - vlen(s), 0)
    if align == ">":
        return " " * gap + s
    if align == "^":
        return " " * (gap // 2) + s + " " * (gap - gap // 2)
    return s + " " * gap


def term_width() -> int:
    cols = shutil.get_terminal_size((100, 24)).columns
    return max(64, min(cols - 4, 100))


def box_lines(title, rows, width=None, color=None):
    """Rounded panel. `rows` items: str, or ('─',) for a divider."""
    w, color = width or term_width(), color or C.ACCENT
    inner = w - 2
    head = f" {title} " if title else ""
    out = [f"{color}╭─{C.RESET}{C.BOLD}{C.WHITE}{head}{C.RESET}"
           f"{color}{'─' * (inner - 1 - vlen(head))}╮{C.RESET}"]
    for row in rows:
        if row == "─":
            out.append(f"{color}├{'─' * inner}┤{C.RESET}")
        else:
            out.append(f"{color}│{C.RESET}{pad(row, inner)}{color}│{C.RESET}")
    out.append(f"{color}╰{'─' * inner}╯{C.RESET}")
    return out


def menu_lines(title, items, width=None, subtitle=None, color=None):
    """items: (key, label[, hint[, style]]) tuples, None for a gap, or a plain str for a section label."""
    rows = []
    if subtitle:
        rows += [f"  {C.DIM}{subtitle}{C.RESET}", ""]
    inner = (width or term_width()) - 2
    for it in items:
        if it is None:
            rows.append("")
            continue
        if isinstance(it, str):
            rows.append(f"  {C.DIM}{it.upper()}{C.RESET}")
            continue
        key, label, *rest = it
        hint  = rest[0] if rest else ""
        style = rest[1] if len(rest) > 1 else ""
        key_col = C.RED if style == "danger" else (C.DIM if key == "0" else C.ACCENT)
        txt_col = C.RED if style == "danger" else (C.DIM if key == "0" else C.WHITE)
        left = f"  {key_col}{C.BOLD}[{key}]{C.RESET}  {txt_col}{label}{C.RESET}"
        if hint:
            room = inner - vlen(left) - 3
            hint = hint if vlen(hint) <= room else hint[:max(room - 1, 0)] + "…"
            left = pad(left, inner - vlen(hint) - 2) + f"{C.DIM}{hint}{C.RESET}"
        rows.append(left)
    return box_lines(title, rows, width, color)


def table_lines(headers, rows, aligns=None, indent="  "):
    aligns = aligns or "<" * len(headers)
    cols = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(vlen(str(c)) for c in col) for col in cols]
    def fmt(cells):
        parts = [pad(str(c), widths[i], aligns[i]) for i, c in enumerate(cells)]
        return indent + "  ".join(parts)
    head = f"{C.DIM}{fmt(headers)}{C.RESET}"
    rule = f"{C.DIM}{indent}{'  '.join('─' * w for w in widths)}{C.RESET}"
    return [head, rule] + [fmt(r) for r in rows]


def fixed_row(cells, widths, aligns=None, indent="  "):
    aligns = aligns or "<" * len(cells)
    return indent + "  ".join(pad(str(c), widths[i], aligns[i]) for i, c in enumerate(cells))


def fixed_rule(widths, indent="  "):
    return f"{C.DIM}{indent}{'  '.join('─' * w for w in widths)}{C.RESET}"


# ── Console helpers ───────────────────────────────────────────────────────────
def clear_screen():
    if sys.stdout.isatty():
        sys.stdout.write("\033[H\033[2J\033[3J")
        sys.stdout.flush()


def out(*lines, indent=2):
    for line in lines:
        print(" " * indent + line)


def ok(msg):    print(f"  {C.GREEN}✔{C.RESET}  {msg}")


def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")


def fail(msg):  print(f"  {C.RED}✘{C.RESET}  {msg}")


def info(msg):  print(f"  {C.BLUE}ℹ{C.RESET}  {msg}")


def note(msg):  print(f"  {C.DIM}{msg}{C.RESET}")


def ask(label):
    return input(f"\n  {C.ACCENT}❯{C.RESET} {C.YELLOW}{label}:{C.RESET} ").strip()


def pause(msg="Press Enter to continue"):
    input(f"\n  {C.DIM}{msg}…{C.RESET}")


def confirm(prompt="Proceed?"):
    ans = input(f"\n  {C.YELLOW}❓ {prompt}{C.RESET} {C.DIM}[y/N]{C.RESET} ").strip().lower()
    return ans in ("y", "yes")


def screen_title(icon, title, color=None):
    print(f"\n  {color or C.ACCENT}{icon}  {C.BOLD}{title}{C.RESET}\n")


def print_logo():
    logo_lines = [
        r"███████╗ ██████╗ ████████╗ ██████╗ ██████╗ ",
        r"██╔════╝██╔═══██╗╚══██╔══╝██╔═══██╗██╔══██╗",
        r"█████╗  ██║   ██║   ██║   ██║   ██║██████╔╝",
        r"██╔══╝  ██║   ██║   ██║   ██║   ██║██╔══██╗",
        r"███████╗╚██████╔╝   ██║   ╚██████╔╝██║  ██║",
        r"╚══════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝",
    ]
    print()
    for i, line in enumerate(logo_lines):
        print(f"   {gradient_text(i, len(logo_lines))}{line}{C.RESET}")
    print(f"   {C.WHITE}{C.BOLD}E N G I N E{C.RESET}  {C.DIM}·{C.RESET}  "
          f"{C.ACCENT}{BRAND_VERSION}{C.RESET}  {C.DIM}·  {BRAND_TAGLINE}  ·  by {BRAND_DEVELOPER}{C.RESET}")
    print()


_INSTALL_STEPS = [
    (5,   "Initializing EOTor Engine Runtime"),
    (15,  "Verifying System Prerequisites"),
    (25,  "Configuring Package Sources"),
    (40,  "Installing Core Components"),
    (55,  "Preparing Routing Modules"),
    (70,  "Loading Location Definitions"),
    (80,  "Applying Permissions & Ownership"),
    (90,  "Registering System Service"),
    (100, "Finalizing Installation"),
]


def _print_install_step(step_idx: int, message: str, done: bool = False):
    pct    = _INSTALL_STEPS[step_idx][0]
    icon   = f"{C.GREEN}✔{C.RESET}" if done else f"{C.YELLOW}{spin()}{C.RESET}"
    bar    = _install_bar(pct)
    status = f"{C.GREEN}Done{C.RESET}" if done else f"{C.YELLOW}Running...{C.RESET}"
    print(f"\r  {icon}  {message:<45} {status}", flush=True)
    if done:
        print(f"    {bar}", flush=True)


def animate_install_step(message: str, duration: float = 0.6):
    """Show spinner animation for a step, then mark done."""
    frames = _SPINNER_FRAMES
    end_time = time.time() + duration
    idx = 0
    while time.time() < end_time:
        frame = frames[idx % len(frames)]
        print(f"\r  {C.YELLOW}{frame}{C.RESET}  {message:<45} {C.DIM}Running...{C.RESET}",
              end="", flush=True)
        time.sleep(0.07)
        idx += 1
    print(f"\r  {C.GREEN}✔{C.RESET}  {message:<45} {C.GREEN}Done      {C.RESET}")


def clip(text: str, width: int) -> str:
    text = str(text)
    if vlen(text) <= width:
        return text
    while text and vlen(text) > width - 1:
        text = text[:-1]
    return text + "…"


def status_led(on: bool) -> str:
    return f"{C.GREEN}●{C.RESET}" if on else f"{C.DIM}○{C.RESET}"

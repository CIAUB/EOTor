"""Colour palette with truecolor / 256 / 16 / no-colour fallbacks."""

import os
import sys


def _detect_color_mode():
    if os.environ.get("NO_COLOR"):
        return None
    if not (os.environ.get("FORCE_COLOR") or sys.stdout.isatty()):
        return None
    colorterm = os.environ.get("COLORTERM", "").lower()
    if "truecolor" in colorterm or "24bit" in colorterm or os.environ.get("FORCE_COLOR") == "truecolor":
        return "true"
    if "256" in os.environ.get("TERM", ""):
        return "256"
    return "16"


_COLOR_MODE = _detect_color_mode()


def _to_256(r, g, b):
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)


def _fg(rgb, basic, bold=False):
    if _COLOR_MODE is None:
        return ""
    if _COLOR_MODE == "true":
        return "\033[%s38;2;%d;%d;%dm" % ("1;" if bold else "", *rgb)
    if _COLOR_MODE == "256":
        return "\033[%s38;5;%dm" % ("1;" if bold else "", _to_256(*rgb))
    return "\033[%sm" % basic


def _esc(code):
    return "" if _COLOR_MODE is None else code


class C:
    ACCENT = _fg((230, 57, 70), "1;31", bold=True)     # brand crimson: borders, titles
    RED    = _fg((255, 107, 107), "1;31")              # errors
    GREEN  = _fg((74, 222, 128), "1;32")               # success / active
    YELLOW = _fg((251, 191, 36), "1;33")               # prompts / warnings
    BLUE   = _fg((96, 165, 250), "1;34")               # info
    PURPLE = _fg((192, 132, 252), "1;35")              # labels
    TEAL   = _fg((45, 212, 191), "1;36")               # IPs, ports, numbers
    WHITE  = _fg((241, 245, 249), "1;37")              # primary text
    DIM    = _fg((120, 128, 145), "2;37")              # muted text
    BOLD   = _esc("\033[1m")
    RESET  = _esc("\033[0m")
    CYAN   = ACCENT                                    # legacy alias used by older call sites


def gradient_text(i, n):
    """Crimson → deep red gradient for the logo, i in [0, n)."""
    t = i / max(n - 1, 1)
    rgb = (int(250 - 60 * t), int(70 - 40 * t), int(80 - 40 * t))
    return _fg(rgb, "1;31", bold=True)

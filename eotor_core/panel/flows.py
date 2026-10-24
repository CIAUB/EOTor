"""Interactive panel flows shared by both backends."""

import os
import time

from ..dashboard import draw_dashboard, run_menu
from ..panel.common import (
    deployed_panel_countries,
    detect_panels,
    panel_countries,
    PANEL_PG_CREDS,
    PanelError,
    parse_selection,
)
from ..panel.pasarguard import PasarGuardAPI, pg_credentials, PGBackend
from ..panel.xui import ThreeXUIClient, xui_generate_api_token, XUIBackend
from ..system import run_cmd
from ..theme import C
from ..ui import (
    ask,
    confirm,
    fail,
    info,
    note,
    ok,
    out,
    pad,
    pause,
    screen_title,
    table_lines,
    warn,
)


# ── Panel flows (shared by 3X-UI and PasarGuard) ─────────────────────────────
def _panel_run_create(backend, countries):
    """Pick a clone source, confirm, then create every selected location."""
    source = backend.pick_source()
    if source is None:
        return
    draw_dashboard()
    screen_title("📋", "SUMMARY")
    out(f"{C.PURPLE}{'Clone from':<12}{C.RESET}{backend.describe(source)}",
        f"{C.PURPLE}{'Locations':<12}{C.RESET}{len(countries)}  "
        f"{C.DIM}({', '.join(c['name'] for c in countries[:6])}{'…' if len(countries) > 6 else ''}){C.RESET}")
    if not confirm("Start creation?"):
        note("Cancelled.")
        time.sleep(1)
        return
    print()
    info("Applying to the panel…")
    created = 0
    for c, success, msg in backend.create_many(source, countries):
        label = f"{c['flag']} {pad(c['name'], 16)}"
        (ok if success else fail)(f"{label} {C.DIM if success else C.RED}{msg}{C.RESET}")
        created += bool(success)
    if created:
        backend.finalize()
    print()
    (ok if created else fail)(f"{created}/{len(countries)} location(s) configured.")
    pause()


def _panel_select(countries, title, prompt):
    """Numbered picker over `countries`; returns the chosen subset ([] to go back)."""
    while True:
        draw_dashboard()
        screen_title("📌", title)
        rows = [[f"{C.ACCENT}{i}{C.RESET}", f"{c['flag']} {c['name']}",
                 f"{C.TEAL}{c['in_port']}{C.RESET}", f"{C.TEAL}{c['out_port']}{C.RESET}"]
                for i, c in enumerate(countries, 1)]
        print("\n".join(table_lines(["#", "Location", "Panel in", "SOCKS out"], rows, "><>>")))
        note("\n0 = go back")
        text = ask(prompt)
        if text in ("0", ""):
            return []
        chosen = parse_selection(text, len(countries))
        if chosen:
            return [countries[i - 1] for i in chosen]
        fail("Invalid selection (examples: 3   or   1-4,7).")
        time.sleep(1.2)


def panel_batch_create(backend):
    done    = backend.configured_codes()
    missing = [c for c in panel_countries() if c["code"] not in done]
    if not missing:
        ok("All 50 primary locations are already configured.")
        pause()
        return
    if len(missing) < 50:
        note(f"{50 - len(missing)} already configured — skipping those.")
    _panel_run_create(backend, missing)


def panel_custom_create(backend):
    done    = backend.configured_codes()
    missing = [c for c in panel_countries() if c["code"] not in done]
    if not missing:
        ok("All 50 primary locations are already configured.")
        pause()
        return
    chosen = _panel_select(missing, "CUSTOM CREATE · SELECT LOCATIONS", "Location number(s)")
    if chosen:
        _panel_run_create(backend, chosen)


def panel_sync_deployed(backend):
    deployed = deployed_panel_countries(extended=True)
    if not deployed:
        info("No EOTor modules are deployed yet — install some from the main menu first.")
        pause()
        return
    done    = backend.configured_codes()
    pending = [c for c in deployed if c["code"] not in done]
    if not pending:
        ok("Every deployed EOTor module is already configured in the panel.")
        pause()
        return
    chosen = _panel_select(pending, "DEPLOYED MODULES · NOT YET IN PANEL", "Module number(s)")
    if chosen:
        _panel_run_create(backend, chosen)


def panel_delete(backend, everything):
    present    = backend.present_codes()
    candidates = [c for c in panel_countries(extended=True) if c["code"] in present]
    if not candidates:
        info("Nothing to delete — no EOTor locations are configured in this panel.")
        pause()
        return
    targets = candidates if everything else _panel_select(
        candidates, "DELETE · SELECT LOCATIONS", "Location number(s) to delete")
    if not targets:
        return
    warn(f"{C.RED}This removes the inbound, SOCKS outbound and routing rule "
         f"for {len(targets)} location(s).{C.RESET}")
    if not confirm(f"Delete {len(targets)} location(s)?"):
        note("Cancelled.")
        time.sleep(1)
        return
    print()
    removed = 0
    for c, done, detail in backend.remove_many(targets):
        label = f"{c['flag']} {c['name']}"
        if done:
            print(f"  {C.RED}🗑{C.RESET}  {label}")
            removed += 1
        else:
            print(f"  {C.DIM}⏭  {label} — nothing to delete {detail}{C.RESET}")
    if removed:
        backend.finalize()
    print()
    ok(f"{removed} location(s) removed.")
    pause()


def panel_menu(backend):
    items = [
        ("1", "Batch create", "all primary locations"),
        ("2", "Custom create", "choose locations"),
        ("3", "Sync deployed modules", "EOTor nodes missing from the panel"),
        None,
        "Remove",
        ("4", "Delete all EOTor configurations", "", "danger"),
        ("5", "Delete selected configurations", "", "danger"),
        None,
        ("0", "Back"),
    ]
    run_menu(f"{backend.name.upper()} · CONTROL PANEL", items, {
        "1": lambda: panel_batch_create(backend),
        "2": lambda: panel_custom_create(backend),
        "3": lambda: panel_sync_deployed(backend),
        "4": lambda: panel_delete(backend, True),
        "5": lambda: panel_delete(backend, False),
    }, subtitle="Panel inbounds 3031+ ➔ local SOCKS 9080+")


def _connect_xui():
    info("Authenticating with the local 3X-UI database…")
    base_url, token = xui_generate_api_token()
    client = ThreeXUIClient(base_url, api_token=token)
    connected, error = client.test_connection()
    if not connected:
        run_cmd("systemctl restart x-ui")
        time.sleep(3)
        connected, error = client.test_connection()
    if not connected:
        raise PanelError(f"Cannot connect to 3X-UI: {error}\n     Try: systemctl restart x-ui")
    ok("Connected to 3X-UI.")
    return XUIBackend(client)


def _connect_pg():
    info("Connecting to PasarGuard…")
    url, user, password = pg_credentials()
    api = PasarGuardAPI(url, user, password)
    if not api.login():
        if os.path.isfile(PANEL_PG_CREDS) and confirm("Login failed. Delete the saved credentials?"):
            try:
                os.remove(PANEL_PG_CREDS)
                note("Saved credentials removed — choose the panel again to re-enter them.")
            except OSError:
                pass
        raise PanelError(f"PasarGuard login failed: {api.last_error}")
    ok("Logged in to PasarGuard.")
    return PGBackend(api)


def _enter_panel(connect):
    try:
        backend = connect()
    except PanelError as e:
        fail(str(e))
        pause()
        return
    time.sleep(0.8)
    panel_menu(backend)


def _marzban_soon():
    info("Marzban support is under development.")
    time.sleep(2)


def panel_integration_menu():
    detected = [name for name, found in detect_panels() if found]
    if detected == ["3X-UI"]:
        return _enter_panel(_connect_xui)
    if detected == ["PasarGuard"]:
        return _enter_panel(_connect_pg)
    state = dict(detect_panels())
    def hint(name):
        return "detected" if state[name] else "not found"
    items = [
        ("1", "3X-UI Panel", hint("3X-UI")),
        ("2", "PasarGuard Panel", hint("PasarGuard")),
        ("3", "Marzban Panel", "coming soon"),
        None,
        ("0", "Back"),
    ]
    run_menu("PANEL INTEGRATION · EZ-PANEL", items, {
        "1": lambda: _enter_panel(_connect_xui),
        "2": lambda: _enter_panel(_connect_pg),
        "3": _marzban_soon,
    }, subtitle="Route panel inbounds through your EOTor locations")

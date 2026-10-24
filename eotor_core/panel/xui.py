"""3X-UI API client and backend."""

import hashlib
import json
import os
import secrets
import sqlite3
import time

from ..panel.common import (
    json_field,
    load_requests,
    panel_countries,
    panel_inbound_tag,
    panel_outbound_tag,
    panel_outbound_tags,
    PANEL_TEST_URL,
    PANEL_XUI_DB,
    PANEL_XUI_TOKEN,
    PanelError,
    write_private,
)
from ..theme import C
from ..ui import ask, fail, info, note, ok, pause, screen_title, table_lines, warn


# ── 3X-UI ─────────────────────────────────────────────────────────────────────
class ThreeXUIClient:
    def __init__(self, base_url, api_token=None):
        requests = load_requests()
        self.base_url     = base_url.rstrip("/")
        self.api_base_url = self.base_url[:-6] if self.base_url.endswith("/panel") else self.base_url
        self.last_error   = ""
        self.session      = requests.Session()
        self.session.trust_env = False
        self.session.verify    = False
        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}",
                                         "Accept": "application/json"})

    def _call(self, method, path, **kw):
        """Returns decoded JSON (dict) on HTTP 200 with success, else None and sets last_error."""
        try:
            r = self.session.request(method, f"{self.api_base_url}{path}", timeout=10, **kw)
            data = r.json()
        except Exception as e:
            self.last_error = str(e)
            return None
        if r.status_code == 200 and data.get("success"):
            return data
        self.last_error = f"HTTP {r.status_code}: {data.get('msg') or r.text[:100]}"
        return None

    def test_connection(self):
        url = f"{self.api_base_url}/panel/api/inbounds/list"
        last_error = ""
        for method in ("POST", "GET"):
            try:
                r = self.session.request(method, url, timeout=10)
                if r.status_code != 200:
                    last_error = f"HTTP {r.status_code}: {r.text[:100]}"
                    continue
                try:
                    result = r.json()
                except ValueError:
                    return True, None
                if result.get("success") or "obj" in result:
                    return True, None
                last_error = f"Status 200 but success=False. Msg: {result.get('msg')}"
            except Exception as e:
                last_error = str(e)
        return False, last_error

    def get_inbounds(self):
        data = self._call("POST", "/panel/api/inbounds/list") or self._call("GET", "/panel/api/inbounds/list")
        return (True, data.get("obj") or []) if data else (False, [])

    def create_inbound(self, payload):
        data = self._call("POST", "/panel/api/inbounds/add", json=payload)
        return (True, data) if data else (False, None)

    def delete_inbound(self, inbound_id):
        return bool(self._call("POST", f"/panel/api/inbounds/del/{inbound_id}"))

    def get_xray_setting(self):
        data = self._call("POST", "/panel/api/xray/")
        return (True, data.get("obj") or {}) if data else (False, None)

    def update_xray_setting(self, xray_setting_str, outbound_test_url=PANEL_TEST_URL):
        return bool(self._call("POST", "/panel/api/xray/update",
                               data={"xraySetting": xray_setting_str,
                                     "outboundTestUrl": outbound_test_url}))

    def _xray_config(self):
        success, settings = self.get_xray_setting()
        if not success or not settings:
            return None, PANEL_TEST_URL
        settings = json_field(settings)
        config   = json_field(settings.get("xraySetting", "{}"))
        return config, settings.get("outboundTestUrl", PANEL_TEST_URL)

    def _edit_xray(self, mutate):
        """Read-modify-write of the xray config. `mutate` returns True when it changed anything."""
        try:
            config, test_url = self._xray_config()
            if config is None:
                return False
            if not mutate(config):
                return False
            return self.update_xray_setting(json.dumps(config, indent=2), test_url)
        except Exception as e:
            self.last_error = str(e)
            return False

    def remove_xray_entries(self, entries):
        """entries: [(outbound_tags, inbound_tags)]. Returns the indexes that had something to remove."""
        touched = set()

        def mutate(cfg):
            outs  = cfg.get("outbounds", [])
            rules = cfg.get("routing", {}).get("rules", [])
            for n, (out_tags, in_tags) in enumerate(entries):
                keep_o = [o for o in outs if o.get("tag") not in out_tags]
                keep_r = [r for r in rules if not (set(r.get("inboundTag", [])) & set(in_tags)
                                                   or r.get("outboundTag") in out_tags)]
                if len(keep_o) != len(outs) or len(keep_r) != len(rules):
                    touched.add(n)
                outs, rules = keep_o, keep_r
            if touched:
                cfg["outbounds"] = outs
                cfg.setdefault("routing", {})["rules"] = rules
            return bool(touched)

        if not self._edit_xray(mutate):
            touched.clear()
        return touched

    def restart_xray_service(self):
        return bool(self._call("POST", "/panel/api/server/restartXrayService"))


def xui_generate_api_token():
    """Create (or reuse) the 'EZ-Panel-Auto' API token in the local x-ui database."""
    if not os.path.exists(PANEL_XUI_DB):
        raise PanelError(f"Database not found at {PANEL_XUI_DB} — is 3X-UI installed?")
    requests = load_requests()
    try:
        conn   = sqlite3.connect(PANEL_XUI_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings WHERE key IN ('webPort', 'webBasePath')")
        port, path = "54321", ""
        for key, value in cursor.fetchall():
            if key == "webPort":
                port = value
            elif key == "webBasePath":
                path = value.strip("/")
        suffix     = f"{path}" if path else ""
        candidates = [f"http://127.0.0.1:{port}/{suffix}", f"https://127.0.0.1:{port}/{suffix}"]
        base_url   = candidates[0]
        probe = requests.Session()
        probe.trust_env, probe.verify = False, False
        for candidate in candidates:
            try:
                probe.get(f"{candidate.rstrip('/')}/panel/api/inbounds/list", timeout=5)
                base_url = candidate
                break
            except Exception:
                continue
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('api_tokens', 'api_token')")
        table_row = cursor.fetchone()
        if not table_row:
            conn.close()
            raise PanelError("API tokens table not found in the 3X-UI database.")
        table = table_row[0]
        saved_plain = saved_hash = None
        if os.path.exists(PANEL_XUI_TOKEN):
            try:
                with open(PANEL_XUI_TOKEN) as f:
                    saved = json.load(f)
                saved_plain, saved_hash = saved.get("plaintext_token"), saved.get("hashed_token")
            except (OSError, ValueError):
                pass
        if saved_plain and saved_hash:
            cursor.execute(f"SELECT token FROM {table} WHERE name = ? AND enabled = 1", ("EZ-Panel-Auto",))
            row = cursor.fetchone()
            if row and row[0] == saved_hash:
                conn.close()
                return base_url, saved_plain
        plain  = "3xui_" + secrets.token_hex(20)
        hashed = hashlib.sha256(plain.encode()).hexdigest()
        cursor.execute(f"DELETE FROM {table} WHERE name = ?", ("EZ-Panel-Auto",))
        cursor.execute(f"INSERT INTO {table} (name, token, enabled, created_at) VALUES (?, ?, ?, ?)",
                       ("EZ-Panel-Auto", hashed, 1, int(time.time() * 1000)))
        conn.commit()
        conn.close()
        write_private(PANEL_XUI_TOKEN, json.dumps({"plaintext_token": plain, "hashed_token": hashed}))
        return base_url, plain
    except sqlite3.Error as e:
        raise PanelError(f"3X-UI database error: {e}")


class XUIBackend:
    name = "3X-UI"

    def __init__(self, client):
        self.client = client

    def sources(self):
        success, inbounds = self.client.get_inbounds()
        return inbounds if success else []

    @staticmethod
    def _is_ours(ib, c):
        return panel_inbound_tag(c) in (ib.get("tag"), ib.get("remark"))

    def _snapshot(self):
        """(owned inbounds per code, outbound tags, rules) — None when the panel can't be read."""
        success, inbounds = self.client.get_inbounds()
        config, _ = self.client._xray_config()
        if not success or config is None:
            return None
        return inbounds, config

    def _scan(self, complete):
        snap = self._snapshot()
        if snap is None:
            return set()
        inbounds, config = snap
        out_tags = {o.get("tag") for o in config.get("outbounds", [])}
        rules    = config.get("routing", {}).get("rules", [])
        found = set()
        for c in panel_countries(extended=True):
            mine     = [ib for ib in inbounds if self._is_ours(ib, c)]
            wanted   = set(panel_outbound_tags(c))
            routed   = {panel_inbound_tag(c)} | {ib.get("tag") for ib in mine}
            wired    = any(r.get("outboundTag") in wanted and routed & set(r.get("inboundTag", []))
                           for r in rules)
            has_out  = bool(wanted & out_tags)
            if complete and mine and has_out and wired:
                found.add(c["code"])
            elif not complete and (mine or has_out or any(r.get("outboundTag") in wanted for r in rules)):
                found.add(c["code"])
        return found

    def configured_codes(self):
        """Locations that are fully wired: inbound + SOCKS outbound + routing rule."""
        return self._scan(complete=True)

    def present_codes(self):
        """Locations with any trace in the panel, including half-created ones."""
        return self._scan(complete=False)

    def is_configured(self, c):
        return c["code"] in self.configured_codes()

    def pick_source(self):
        inbounds = self.sources()
        if not inbounds:
            fail("No inbounds found to clone from.")
            pause()
            return None
        screen_title("📌", "SELECT INBOUND TO CLONE")
        rows = [[f"{C.ACCENT}{i}{C.RESET}", f"{C.TEAL}{ib.get('port', '?')}{C.RESET}",
                 str(ib.get("protocol", "?")), str(ib.get("remark") or "—")]
                for i, ib in enumerate(inbounds, 1)]
        print("\n".join(table_lines(["#", "Port", "Protocol", "Remark"], rows, ">>><")))
        note("\n0 = go back")
        while True:
            value = ask("Inbound port to clone from")
            if value in ("0", ""):
                return None
            try:
                match = next((ib for ib in inbounds if ib.get("port") == int(value)), None)
            except ValueError:
                match = None
            if match:
                return match
            fail("No inbound with that port.")

    def describe(self, source):
        return f"inbound port {source.get('port')}"

    def create(self, source, c):
        _, ok_, msg = self.create_many(source, [c])[0]
        return ok_, msg

    def create_many(self, source, countries):
        """Create every location, then edit the xray config once. [(country, ok, message)]"""
        cl = self.client
        success, current = cl.get_inbounds()
        if not success:
            return [(c, False, f"cannot read inbounds ({cl.last_error})") for c in countries]
        results, staged = {}, []
        for c in countries:
            inbound_tag = panel_inbound_tag(c)
            blocker = next((ib for ib in current
                            if ib.get("port") == c["in_port"] and not self._is_ours(ib, c)), None)
            if blocker:
                results[c["code"]] = (False, f"port {c['in_port']} in use by "
                                             f"'{blocker.get('remark') or blocker.get('tag')}'")
                continue
            stale = [ib for ib in current if self._is_ours(ib, c)]
            for ib in stale:
                cl.delete_inbound(ib.get("id"))
            created, response = cl.create_inbound({
                "enable": True, "remark": inbound_tag, "listen": source.get("listen", ""),
                "port": c["in_port"], "protocol": source.get("protocol"), "expiryTime": 0, "total": 0,
                "tag": inbound_tag,
                "settings": json_field(source.get("settings")),
                "streamSettings": json_field(source.get("streamSettings")),
                "sniffing": json_field(source.get("sniffing")),
            })
            if not created:
                results[c["code"]] = (False, f"inbound create failed on port {c['in_port']} ({cl.last_error})")
                continue
            real_tag = (response.get("obj") or {}).get("tag") or inbound_tag
            old_tags = {inbound_tag, real_tag} | {ib.get("tag") for ib in stale if ib.get("tag")}
            staged.append((c, real_tag, old_tags))
            results[c["code"]] = (True, f"in {c['in_port']} ➔ out {c['out_port']}")

        def mutate(cfg):
            outs  = cfg.setdefault("outbounds", [])
            rules = cfg.setdefault("routing", {}).setdefault("rules", [])
            for c, real_tag, old_tags in staged:
                out_tags = panel_outbound_tags(c)
                outs[:]  = [o for o in outs if o.get("tag") not in out_tags]
                rules[:] = [r for r in rules if not (set(r.get("inboundTag", [])) & old_tags
                                                     or r.get("outboundTag") in out_tags)]
                outs.append({"protocol": "socks", "tag": panel_outbound_tag(c),
                             "settings": {"servers": [{"address": "127.0.0.1", "port": c["out_port"]}]}})
                rules.append({"type": "field", "inboundTag": [real_tag],
                              "outboundTag": panel_outbound_tag(c)})
            return True

        if staged and not cl._edit_xray(mutate):
            for c, _, _ in staged:
                results[c["code"]] = (False, f"xray config update failed ({cl.last_error})")
        return [(c, *results[c["code"]]) for c in countries]

    def remove(self, c):
        _, done, detail = self.remove_many([c])[0]
        return done, detail

    def remove_many(self, countries):
        """Delete inbounds, then clean the xray config once. [(country, removed, detail)]"""
        cl = self.client
        success, inbounds = cl.get_inbounds()
        inbounds = inbounds if success else []
        deleted, entries = [], []
        for c in countries:
            mine = [ib for ib in inbounds if self._is_ours(ib, c)]
            gone = [cl.delete_inbound(ib.get("id")) for ib in mine]
            deleted.append(any(gone))
            in_tags = {panel_inbound_tag(c)} | {ib.get("tag") for ib in mine if ib.get("tag")}
            entries.append((set(panel_outbound_tags(c)), in_tags))
        touched = cl.remove_xray_entries(entries)
        return [(c, deleted[n] or n in touched, "") for n, c in enumerate(countries)]

    def finalize(self):
        info("Restarting Xray core…")
        if self.client.restart_xray_service():
            ok("Xray restarted.")
            return True
        warn("Saved, but the automatic Xray restart failed — restart it from the panel.")
        return False

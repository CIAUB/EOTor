"""PasarGuard API client and backend."""

import copy
import os

from ..panel.common import (
    load_requests,
    panel_countries,
    panel_inbound_tag,
    PANEL_PG_CREDS,
    PANEL_PG_PATHS,
    write_private,
)
from ..theme import C
from ..ui import ask, confirm, fail, info, note, pause, screen_title, table_lines, warn


# ── PasarGuard ────────────────────────────────────────────────────────────────
class PasarGuardAPI:
    def __init__(self, base_url, username, password, core_id=1):
        self.base_url   = base_url.rstrip("/")
        self.username   = username
        self.password   = password
        self.core_id    = core_id
        self.last_error = ""
        self.headers    = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def _request(self, method, path, **kw):
        requests = load_requests()
        try:
            r = requests.request(method, f"{self.base_url}{path}", headers=self.headers,
                                 timeout=15, **kw)
        except requests.exceptions.ConnectionError:
            self.last_error = "Cannot connect to the panel."
            return None
        except Exception as e:
            self.last_error = str(e)
            return None
        if r.status_code in (200, 201, 204):
            return r
        self.last_error = f"HTTP {r.status_code}: {r.text[:200]}"
        return None

    def login(self):
        r = self._request("POST", "/api/admin/token",
                          data={"username": self.username, "password": self.password})
        if r is None:
            if "401" in self.last_error:
                self.last_error = "Invalid username or password."
            return False
        data = r.json()
        self.headers.update({"Authorization": f"{data.get('token_type', 'Bearer')} {data.get('access_token')}",
                             "Content-Type": "application/json"})
        return True

    def get_core_config(self):
        r = self._request("GET", f"/api/core/{self.core_id}")
        if r is None:
            return None
        data = r.json()
        return data.get("config", data)

    def save_core_config(self, config, restart_nodes=True):
        return self._request("PUT", f"/api/core/{self.core_id}", json={"config": config},
                             params={"restart_nodes": str(restart_nodes).lower()}) is not None

    def list_inbounds_raw(self):
        config = self.get_core_config()
        return config.get("inbounds", []) if config else []

    def get_hosts(self):
        r = self._request("GET", "/api/hosts")
        return r.json() if r is not None else None

    def save_hosts(self, hosts):
        return self._request("PUT", "/api/hosts", json=hosts) is not None

    def delete_host(self, host_id):
        return self._request("DELETE", f"/api/host/{host_id}") is not None

    @staticmethod
    def flatten_hosts(data):
        flat = []
        if isinstance(data, dict):
            for group_tag, hosts in data.items():
                if isinstance(hosts, list):
                    flat += [(group_tag, h) for h in hosts]
                elif isinstance(hosts, dict):
                    flat.append((group_tag, hosts))
        elif isinstance(data, list):
            flat = [(h.get("inbound_tag") or h.get("tag") or h.get("inboundTag") or "—", h) for h in data]
        return flat

    def clone_hosts(self, source_index, tags):
        """Clone host #source_index once per tag (inbound tag == remark), saving a single time."""
        raw = self.get_hosts()
        if raw is None:
            return False
        data = copy.deepcopy(raw)
        flat = self.flatten_hosts(data)
        if not 1 <= source_index <= len(flat):
            self.last_error = "Invalid host index."
            return False
        if not isinstance(data, (list, dict)):
            self.last_error = "Unexpected /api/hosts format."
            return False
        template = flat[source_index - 1][1]
        for tag in tags:
            new_host = copy.deepcopy(template)
            new_host.pop("id", None)
            new_host["remark"], new_host["inbound_tag"] = tag, tag
            if "name" in new_host:
                new_host["name"] = tag
            if isinstance(data, list):
                data[:] = [h for h in data if not (h.get("inbound_tag") == tag and h.get("remark") == tag)]
                data.append(new_host)
            else:
                group = data.setdefault(tag, [])
                group = group if isinstance(group, list) else [group]
                data[tag] = [h for h in group if h.get("remark") != tag] + [new_host]
        return self.save_hosts(data)

    def remove_relays(self, tags):
        """Drop inbound/outbound/routing for every tag in one core save, then their hosts.
        Returns {tag: removed_anything}; None when the core config can't be read."""
        config = self.get_core_config()
        if config is None:
            return None
        tags, touched = set(tags), {}
        routing = config.setdefault("routing", {})
        rules = routing.get("rules", [])
        for key in ("inbounds", "outbounds"):
            for x in config.get(key, []):
                if x.get("tag") in tags:
                    touched[x["tag"]] = True
        for r in rules:
            for t in tags & (set(r.get("inboundTag", [])) | {r.get("outboundTag")}):
                touched[t] = True
        if touched:
            for key in ("inbounds", "outbounds"):
                config[key] = [x for x in config.get(key, []) if x.get("tag") not in tags]
            routing["rules"] = [r for r in rules if not (tags & set(r.get("inboundTag", []))
                                                         or r.get("outboundTag") in tags)]
            if not self.save_core_config(config):
                return None
        raw = self.get_hosts()
        for group_tag, h in (self.flatten_hosts(raw) if raw is not None else []):
            tag = h.get("inbound_tag") if h.get("inbound_tag") in tags else group_tag
            if tag in tags and h.get("id") is not None and self.delete_host(h["id"]):
                touched[tag] = True
        return {t: touched.get(t, False) for t in tags}


def _parse_env_file(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _detect_pg_url():
    for base in PANEL_PG_PATHS:
        path = os.path.join(base, ".env")
        if not os.path.isfile(path):
            continue
        try:
            env      = _parse_env_file(path)
            host     = env.get("UVICORN_HOST", "127.0.0.1").strip()
            port     = env.get("UVICORN_PORT", "8000").strip()
            certfile = env.get("UVICORN_SSL_CERTFILE", "").strip()
            connect  = "127.0.0.1" if host in ("0.0.0.0", "") else host
            domain   = next((part for part in certfile.replace("\\", "/").split("/")
                             if "." in part and not part.endswith(".pem")), "") if certfile else ""
            return f"{'https' if certfile else 'http'}://{domain or connect}:{port}"
        except OSError as e:
            warn(f"Could not parse {path}: {e}")
    return ""


def pg_credentials():
    import getpass
    if os.path.isfile(PANEL_PG_CREDS):
        try:
            env = _parse_env_file(PANEL_PG_CREDS)
            if env.get("URL") and env.get("USER") and env.get("PASS"):
                info(f"Using saved credentials  {C.DIM}{env['URL']} · {env['USER']}{C.RESET}")
                return env["URL"], env["USER"], env["PASS"]
        except OSError:
            pass
    detected = _detect_pg_url()
    if detected and confirm(f"Is this your PasarGuard address? {detected}"):
        url = detected
    else:
        url = ask("Panel URL (e.g. https://panel.example.com:8000)")
    user = ask("Admin username")
    print(f"\n  {C.ACCENT}❯{C.RESET} {C.YELLOW}Admin password:{C.RESET} ", end="", flush=True)
    password = getpass.getpass("")
    if confirm(f"Save these credentials to {PANEL_PG_CREDS} (owner-only) for next time?") \
            and write_private(PANEL_PG_CREDS, f"URL={url}\nUSER={user}\nPASS={password}\n"):
        note(f"Credentials saved to {PANEL_PG_CREDS}.")
    return url, user, password


class PGBackend:
    name = "PasarGuard"

    def __init__(self, api):
        self.api = api

    def sources(self):
        return self.api.list_inbounds_raw()

    def _scan(self, complete):
        config = self.api.get_core_config()
        if not config:
            return set()
        ib_tags = {x.get("tag") for x in config.get("inbounds", [])}
        ob_tags = {x.get("tag") for x in config.get("outbounds", [])}
        rules   = config.get("routing", {}).get("rules", [])
        ruled   = {t for r in rules for t in (*r.get("inboundTag", []), r.get("outboundTag"))}
        hosts   = set()
        if not complete:
            raw = self.api.get_hosts()
            hosts = {h.get("inbound_tag") or g for g, h in self.api.flatten_hosts(raw)} if raw is not None else set()
        found = set()
        for c in panel_countries(extended=True):
            tag = panel_inbound_tag(c)
            if complete and tag in ib_tags and tag in ob_tags and tag in ruled:
                found.add(c["code"])
            elif not complete and tag in ib_tags | ob_tags | ruled | hosts:
                found.add(c["code"])
        return found

    def configured_codes(self):
        """Locations that are fully wired: inbound + outbound + routing rule."""
        return self._scan(complete=True)

    def present_codes(self):
        """Locations with any trace in the panel, including half-created ones."""
        return self._scan(complete=False)

    def is_configured(self, c):
        return c["code"] in self.configured_codes()

    def pick_source(self):
        inbounds = self.sources()
        if not inbounds:
            fail(f"No inbounds available ({self.api.last_error or 'empty core config'}).")
            pause()
            return None
        screen_title("📌", "SELECT INBOUND TO CLONE")
        rows = []
        for i, ib in enumerate(inbounds, 1):
            ss = ib.get("streamSettings", {}) or {}
            rows.append([f"{C.ACCENT}{i}{C.RESET}", f"{C.TEAL}{ib.get('port', '?')}{C.RESET}",
                         str(ib.get("protocol", "?")), str(ss.get("network", "tcp")),
                         str(ss.get("security", "none")), str(ib.get("tag", "—"))])
        print("\n".join(table_lines(["#", "Port", "Protocol", "Network", "Security", "Tag"], rows, ">>><<<")))
        note("\n0 = go back")
        inbound = None
        while inbound is None:
            value = ask("Inbound #")
            if value in ("0", ""):
                return None
            if value.isdigit() and 1 <= int(value) <= len(inbounds):
                inbound = inbounds[int(value) - 1]
            else:
                fail(f"Enter a number from 1 to {len(inbounds)}.")

        flat = PasarGuardAPI.flatten_hosts(self.api.get_hosts())
        if not flat:
            fail("No hosts found to clone from.")
            pause()
            return None
        screen_title("📌", "SELECT HOST TO CLONE")
        rows = [[f"{C.ACCENT}{i}{C.RESET}", str(tag), str(h.get("remark") or h.get("name") or "—"),
                 str(h.get("address", "—")), str(h.get("port", "?"))]
                for i, (tag, h) in enumerate(flat, 1)]
        print("\n".join(table_lines(["#", "Inbound tag", "Remark", "Address", "Port"], rows, "><<<>")))
        note("\n0 = go back")
        while True:
            value = ask("Host #")
            if value in ("0", ""):
                return None
            if value.isdigit() and 1 <= int(value) <= len(flat):
                return {"inbound": inbound, "host_index": int(value)}
            fail(f"Enter a number from 1 to {len(flat)}.")

    def describe(self, source):
        ib = source["inbound"]
        return f"inbound {ib.get('tag', '?')} (port {ib.get('port', '?')}), host #{source['host_index']}"

    def create(self, source, c):
        _, ok_, msg = self.create_many(source, [c])[0]
        return ok_, msg

    def create_many(self, source, countries):
        """Edit the core config once and clone hosts once. [(country, ok, message)]"""
        api = self.api
        config = api.get_core_config()
        if config is None:
            return [(c, False, f"could not fetch core config ({api.last_error})") for c in countries]
        inbounds, outbounds = config.setdefault("inbounds", []), config.setdefault("outbounds", [])
        rules = config.setdefault("routing", {}).setdefault("rules", [])
        results, staged = {}, []
        for c in countries:
            tag = panel_inbound_tag(c)
            blocker = next((x for x in inbounds
                            if x.get("port") == c["in_port"] and x.get("tag") != tag), None)
            if blocker:
                results[c["code"]] = [False, f"port {c['in_port']} in use by '{blocker.get('tag')}'"]
                continue
            inbounds[:]  = [x for x in inbounds if x.get("tag") != tag]
            outbounds[:] = [x for x in outbounds if x.get("tag") != tag]
            rules[:]     = [r for r in rules if not (tag in r.get("inboundTag", [])
                                                     or r.get("outboundTag") == tag)]
            new_inbound = copy.deepcopy(source["inbound"])
            new_inbound["port"], new_inbound["tag"] = c["in_port"], tag
            inbounds.append(new_inbound)
            outbounds.append({"tag": tag, "protocol": "socks",
                              "settings": {"address": "127.0.0.1", "port": c["out_port"]}})
            rules.append({"type": "field", "inboundTag": [tag], "outboundTag": tag})
            staged.append(c)
            results[c["code"]] = [True, f"in {c['in_port']} ➔ out {c['out_port']}"]
        if staged and not api.save_core_config(config):
            for c in staged:
                results[c["code"]] = [False, f"saving core config failed ({api.last_error})"]
            staged = []
        if staged and not api.clone_hosts(source["host_index"], [panel_inbound_tag(c) for c in staged]):
            for c in staged:
                results[c["code"]][1] += f"  {C.YELLOW}(host clone failed: {api.last_error}){C.RESET}"
        return [(c, *results[c["code"]]) for c in countries]

    def remove(self, c):
        _, done, detail = self.remove_many([c])[0]
        return done, detail

    def remove_many(self, countries):
        """[(country, removed, detail)] — one core save for all of them."""
        touched = self.api.remove_relays([panel_inbound_tag(c) for c in countries])
        if touched is None:
            return [(c, False, f"({self.api.last_error})") for c in countries]
        return [(c, touched.get(panel_inbound_tag(c), False), "") for c in countries]

    def finalize(self):
        return True

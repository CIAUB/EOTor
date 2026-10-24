"""Branding, filesystem paths, tunables and state shared across modules."""

import threading
from collections import OrderedDict
from datetime import datetime


BRAND_NAME       = "EOTor Engine"
BRAND_VERSION    = "v4.1.0"
BRAND_TAGLINE    = "Enterprise Multi-Location Routing Manager"
BRAND_DEVELOPER  = "CIAUB"
BRAND_CONTACT    = "https://t.me/CIAUB"
BRAND_CHANNEL    = "https://t.me/CIAUB_CH"
BRAND_GITHUB     = "https://github.com/CIAUB/EOTor"
# ── Filesystem path mapping (internal paths stay unchanged; only display changes) ──
# Internal paths used by the underlying runtime:
INTERNAL_INSTANCE_DIR  = "/etc/tor/instances"
INTERNAL_VARLIB_DIR    = "/var/lib/tor-instances"
# Display aliases shown to the user:
DISPLAY_INSTANCE_DIR   = "/etc/eotor/instances"
_DISPLAY_VARLIB_DIR     = "/var/lib/eotor"
DISPLAY_CONF_NAME      = "eotor.conf"
_DISPLAY_PID_NAME       = "eotor.pid"
_DISPLAY_LOG_DIR        = "/var/log/eotor"
_DISPLAY_OPT_DIR        = "/opt/eotor"
_DISPLAY_LOCAL_DIR      = "/usr/local/eotor"
MIN_EXIT_NODES    = 3
LOW_EXIT_NODES    = 10
TIMEOUT_NORMAL    = 60
TIMEOUT_LOW       = 120
FAST_TIMEOUT      = 3
FAST_TIMEOUT_EXT  = 7
EXTEND_PCT        = 5
MAX_FAST_RETRIES  = 8
STABILITY_CHECKS  = 2
STABILITY_DELAY   = 1.5
PARALLEL_WORKERS  = 5
FINAL_VERIFY_WAIT = 3
_print_lock  = threading.Lock()
report_lock = threading.Lock()
report_data   = {"SUCCESS": [], "FAILED": [], "SKIPPED": [], "RETRIED": [], "WARNED": []}
SESSION_START = datetime.now()
exit_cache: dict = {}
ip_cache = OrderedDict()
ip_lock  = threading.Lock()


class _GuardianState:
    """CPU guardian state, shared by the dashboard and the guardian thread."""

    def __init__(self):
        self.thread = None
        self.active = False
        self.lock = threading.Lock()
        self.cooldowns = {}   # iso -> unix time when the location is re-enabled
        self.log = []         # (iso, cpu_pct, stopped_at) strings

    def running(self):
        return bool(self.thread and self.thread.is_alive())


guardian = _GuardianState()

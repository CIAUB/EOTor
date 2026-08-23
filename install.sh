#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
#  EOTor Engine — One-command Installer
# ══════════════════════════════════════════════════════════════════════════════
#  Developer  : CIAUB
#  Maintainer : CIAUB
#  Contact    : https://t.me/CIAUB  |  Channel: https://t.me/CIAUB_CH
#  GitHub     : https://github.com/CIAUB/EOTor
#  License    : MIT
#
#  This installer is intentionally minimal and frozen.
#  All updates ship inside eotor.py — this file is never touched again.
# ══════════════════════════════════════════════════════════════════════════════
set -e

RED='\e[1;31m'
NC='\e[0m'

REPO="CIAUB/EOTor"
RAW_BASE="https://raw.githubusercontent.com/${REPO}"
INSTALL_PATH="/usr/local/bin/EOTor"
TMP_PATH="/tmp/eotor.py"

DEVELOPER="CIAUB"
VERSION_TAG="${1:-}"   # optional: pass a tag (e.g. v3.4) to pin that version

# ── Root check ────────────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}[-] Please run as root (sudo).${NC}"
  exit 1
fi

echo -e "${RED}[*] Installing EOTor...${NC}"

# ── System packages ──────────────────────────────────────────────────────────
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y >/dev/null 2>&1 || true
  apt-get install -y python3 python3-pip curl >/dev/null 2>&1 || true
fi

pip3 install --break-system-packages requests urllib3 >/dev/null 2>&1 || \
pip3 install requests urllib3 >/dev/null 2>&1 || true

# ── Pick source: pinned tag or main branch ────────────────────────────────────
if [ -n "${VERSION_TAG}" ]; then
  SOURCE="${RAW_BASE}/${VERSION_TAG}/eotor.py"
else
  SOURCE="${RAW_BASE}/main/eotor.py?v=$(date +%s)"
fi

curl -fsSL "${SOURCE}" -o "${TMP_PATH}"

if [ ! -s "${TMP_PATH}" ]; then
  echo -e "${RED}[-] Download failed. Check tag/version or network.${NC}"
  exit 1
fi

# ── Restore shebang (raw GitHub strips it) ───────────────────────────────────
if ! head -n 1 "${TMP_PATH}" | grep -q "python"; then
  printf '%s\n%s\n' '#!/usr/bin/env python3' "$(cat "${TMP_PATH}")" > "${TMP_PATH}.tmp"
  mv "${TMP_PATH}.tmp" "${TMP_PATH}"
fi

mv "${TMP_PATH}" "${INSTALL_PATH}"
chmod +x "${INSTALL_PATH}"

echo -e "${RED}[+] Installed to ${INSTALL_PATH}${NC}"
echo -e "${RED}[+] Developer: ${DEVELOPER}${NC}"
echo -e "${RED}[+] Launching EOTor...${NC}"
echo
exec "${INSTALL_PATH}"

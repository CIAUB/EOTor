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
GREEN='\e[2;32m'
NC='\e[0m'

REPO="CIAUB/EOTor"
RAW_BASE="https://raw.githubusercontent.com/${REPO}"
INSTALL_PATH="/usr/local/bin/EOTor"
TMP_PATH="/tmp/eotor.py"

DEVELOPER="CIAUB"
VERSION_TAG="${1:-}"   # optional: pass a tag (e.g. v3.4 or 3.4) to pin that version

# Accept version from both forms:
#   bash install.sh 3.4          → $1 = 3.4
#   bash -c "$(curl ...)" 3.4    → $0 = 3.4 (bash -c name slot)
#   bash install.sh              → VERSION_TAG stays empty (latest from main)
if [ -z "${VERSION_TAG}" ] && [[ "${0}" =~ ^[vV]?[0-9]+(\.[0-9]+){1,2}$ ]]; then
  VERSION_TAG="${0}"
fi

# Normalize tag: prepend "v" if missing (GitHub tags use v-prefix)
if [ -n "${VERSION_TAG}" ] && [[ ! "${VERSION_TAG}" =~ ^v ]]; then
  VERSION_TAG="v${VERSION_TAG}"
fi

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

# ── Extract BRAND_VERSION from the downloaded file ───────────────────────────
INSTALLED_VERSION=$(awk -F'"' '/BRAND_VERSION[[:space:]]*=/{print $2; exit}' "${TMP_PATH}" | sed 's/^v//')
[ -z "${INSTALLED_VERSION}" ] && INSTALLED_VERSION="unknown"

echo -e "${RED}[+] Version: v${INSTALLED_VERSION}${NC}"

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

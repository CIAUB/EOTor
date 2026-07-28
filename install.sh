#!/bin/bash

set -e

RED='\e[1;31m'
NC='\e[0m'

INSTALL_PATH="/usr/local/bin/EOTor"
TMP_PATH="/tmp/eotor.py"

if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}[-] Please run as root (sudo).${NC}"
    exit 1
fi

echo -e "${RED}[*] Installing EOTor...${NC}"

if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y >/dev/null 2>&1 || true
    apt-get install -y python3 python3-pip curl >/dev/null 2>&1 || true
fi

pip3 install --break-system-packages requests urllib3 >/dev/null 2>&1 || \
pip3 install requests urllib3 >/dev/null 2>&1 || true

# Download directly from Raw Github URL
curl -fsSL "https://raw.githubusercontent.com/EOAMIR/EOTor/main/eotor.py?v=$(date +%s)" -o "${TMP_PATH}"

if [ ! -s "${TMP_PATH}" ]; then
    echo -e "${RED}[-] Download failed. Check GitHub raw URL.${NC}"
    exit 1
fi

if ! head -n 1 "${TMP_PATH}" | grep -q "python"; then
    printf '%s\n%s\n' '#!/usr/bin/env python3' "$(cat "${TMP_PATH}")" > "${TMP_PATH}.tmp"
    mv "${TMP_PATH}.tmp" "${TMP_PATH}"
fi

mv "${TMP_PATH}" "${INSTALL_PATH}"
chmod +x "${INSTALL_PATH}"

echo -e "${RED}[+] Installed to ${INSTALL_PATH}${NC}"
echo -e "${RED}[+] Launching EOTor...${NC}"
echo

exec "${INSTALL_PATH}"

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
#  Installs the whole project (eotor.py + eotor_core/) into /usr/local/lib/eotor
#  and puts the `EOTor` / `eotor` commands in /usr/local/bin.
#  Re-run it any time to update.
# ══════════════════════════════════════════════════════════════════════════════
set -e

RED='\e[1;31m'
NC='\e[0m'

REPO="CIAUB/EOTor"
LIB_DIR="${EOTOR_LIB_DIR:-/usr/local/lib/eotor}"
BIN_DIR="${EOTOR_BIN_DIR:-/usr/local/bin}"
MARK="# eotor-launcher"

VERSION_TAG="${1:-}"   # optional: pass a tag (e.g. v4.1 or 4.1) to pin that version

# bash -c "$(curl ...)" 4.1  puts the version in $0
if [ -z "${VERSION_TAG}" ] && [[ "${0}" =~ ^[vV]?[0-9]+(\.[0-9]+){1,2}$ ]]; then
  VERSION_TAG="${0}"
fi
if [ -n "${VERSION_TAG}" ] && [[ ! "${VERSION_TAG}" =~ ^v ]]; then
  VERSION_TAG="v${VERSION_TAG}"
fi

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}[-] Please run as root (sudo).${NC}"
  exit 1
fi

echo -e "${RED}[*] Installing EOTor...${NC}"

# ── Dependencies ──────────────────────────────────────────────────────────────
if [ -z "${EOTOR_SKIP_DEPS:-}" ]; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y >/dev/null 2>&1 || true
    apt-get install -y python3 python3-pip curl tar >/dev/null 2>&1 || true
  fi
  pip3 install --break-system-packages requests urllib3 >/dev/null 2>&1 || \
  pip3 install requests urllib3 >/dev/null 2>&1 || true
fi

# ── Download the project archive (pinned tag or main branch) ──────────────────
if [ -n "${EOTOR_ARCHIVE:-}" ]; then
  SOURCE="${EOTOR_ARCHIVE}"
elif [ -n "${VERSION_TAG}" ]; then
  SOURCE="https://github.com/${REPO}/archive/refs/tags/${VERSION_TAG}.tar.gz"
else
  SOURCE="https://github.com/${REPO}/archive/refs/heads/main.tar.gz"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

if ! curl -fsSL "${SOURCE}" -o "${WORK}/src.tar.gz" || ! tar -xzf "${WORK}/src.tar.gz" -C "${WORK}" --strip-components=1 2>/dev/null \
   || [ ! -f "${WORK}/eotor.py" ] || [ ! -d "${WORK}/eotor_core" ]; then
  echo -e "${RED}[-] Download failed. Check tag/version or network.${NC}"
  exit 1
fi

INSTALLED_VERSION=$(awk -F'"' '/BRAND_VERSION[[:space:]]*=/{print $2; exit}' "${WORK}/eotor_core/config.py" | sed 's/^v//')
[ -z "${INSTALLED_VERSION}" ] && INSTALLED_VERSION="unknown"
echo -e "${RED}[+] Version: v${INSTALLED_VERSION}${NC}"

# ── Install: replace the library directory, then write the launchers ──────────
mkdir -p "${LIB_DIR}" "${BIN_DIR}"
rm -rf "${LIB_DIR:?}/eotor_core"
cp -r "${WORK}/eotor_core" "${LIB_DIR}/eotor_core"
cp "${WORK}/eotor.py" "${LIB_DIR}/eotor.py"
chmod +x "${LIB_DIR}/eotor.py"

for name in EOTor eotor; do
  printf '#!/bin/sh\n%s\nexec python3 "%s/eotor.py" "$@"\n' "${MARK}" "${LIB_DIR}" > "${BIN_DIR}/${name}"
  chmod +x "${BIN_DIR}/${name}"
done

echo -e "${RED}[+] Installed to ${LIB_DIR}${NC}"
echo -e "${RED}[+] Developer: CIAUB${NC}"

if [ -z "${EOTOR_NO_LAUNCH:-}" ]; then
  echo -e "${RED}[+] Launching EOTor...${NC}"
  echo
  exec "${BIN_DIR}/EOTor"
fi

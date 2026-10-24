#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════════
#  EOTor Engine — Enterprise Multi-Location SOCKS5 Routing Manager
#  (includes EZ-Panel: 3X-UI / PasarGuard integration)
# ══════════════════════════════════════════════════════════════════════════════
#  Developer  : CIAUB
#  Maintainer : CIAUB
#  Contact    : https://t.me/CIAUB  |  Channel: https://t.me/CIAUB_CH
#  GitHub     : https://github.com/CIAUB/EOTor
#  License    : MIT
# ══════════════════════════════════════════════════════════════════════════════


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from eotor_core.app import main

if __name__ == "__main__":
    main()

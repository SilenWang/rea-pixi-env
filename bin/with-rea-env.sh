#!/usr/bin/env bash
# Single place that knows where the pinned Ghidra install and REA provider live.
# Usage: bash bin/with-rea-env.sh rea <args...>
set -euo pipefail

REA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GHIDRA_INSTALL_DIR="${GHIDRA_INSTALL_DIR:-$REA_ROOT/.tools/ghidra_12.1.4_PUBLIC}"
export REA_ANALYSIS_PROVIDER="${REA_ANALYSIS_PROVIDER:-ghidra}"
export GHIDRA_HEADLESS_MAXMEM="${GHIDRA_HEADLESS_MAXMEM:-4G}"
# ponytail: 10 min first-query budget; raise via env if a huge target needs more.
export REA_GHIDRA_STARTUP_TIMEOUT_MS="${REA_GHIDRA_STARTUP_TIMEOUT_MS:-600000}"
# Optional ELF/DOS providers: REA never installs Python or packages itself.
export REA_PWNTOOLS_PYTHON="${REA_PWNTOOLS_PYTHON:-$REA_ROOT/.pixi/envs/default/bin/python}"

exec "$@"

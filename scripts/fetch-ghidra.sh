#!/usr/bin/env bash
# REA's ghidra provider accepts an existing Ghidra 12.1.x install + 64-bit JDK 21+.
# conda-forge has no ghidra package, so pin the official release by size/digest.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VER=12.1.4
STAMP=20260921
ZIP="ghidra_${VER}_PUBLIC_${STAMP}.zip"
URL="https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${VER}_build/${ZIP}"
SHA256="ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db"
DEST="$ROOT/.tools"

if [ -d "$DEST/ghidra_${VER}_PUBLIC" ]; then
  echo "already present: $DEST/ghidra_${VER}_PUBLIC"
  exit 0
fi

mkdir -p "$DEST"
curl -fL --retry 3 -o "$DEST/$ZIP" "$URL"
echo "$SHA256  $DEST/$ZIP" | sha256sum -c -
unzip -q "$DEST/$ZIP" -d "$DEST"
rm -f "$DEST/$ZIP"
echo "GHIDRA_INSTALL_DIR=$DEST/ghidra_${VER}_PUBLIC"

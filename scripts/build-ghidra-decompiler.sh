#!/usr/bin/env bash
# REA's ghidra provider needs a native decompiler for the host platform.
# The official Ghidra release contains one for Linux and Windows only (Apple
# notarization blocks shipping a macOS binary), so on darwin we build it from the
# C++ sources that come inside the same zip and install it exactly where REA looks:
#   Ghidra/Features/Decompiler/os/mac_<arch>/decompile
# On other platforms the released decompiler is used and this is a no-op.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GHIDRA_DIR="$(ls -d "$ROOT"/.tools/ghidra_*_PUBLIC 2>/dev/null | head -1 || true)"

if [ -z "$GHIDRA_DIR" ]; then
  echo "Ghidra not found under $ROOT/.tools; run 'pixi run fetch-ghidra' first" >&2
  exit 1
fi

if [ "$(uname -s)" != "Darwin" ]; then
  echo "not macOS ($(uname -s)/$(uname -m)): the official Ghidra release already ships a decompiler"
  exit 0
fi

case "$(uname -m)" in
  arm64)  OSDIR=mac_arm_64;  ARCH=arm64 ;;
  x86_64) OSDIR=mac_x86_64; ARCH=x86_64 ;;
  *) echo "unsupported CPU: $(uname -m)" >&2; exit 1 ;;
esac

DEST_DIR="$GHIDRA_DIR/Ghidra/Features/Decompiler/os/$OSDIR"
DEST="$DEST_DIR/decompile"
if [ -x "$DEST" ]; then
  echo "already present: $DEST"
  exit 0
fi

SRC="$GHIDRA_DIR/Ghidra/Features/Decompiler/src/decompile/cpp"
if [ ! -d "$SRC" ]; then
  echo "decompiler sources missing: $SRC" >&2
  exit 1
fi

# The Makefile defaults to -arch x86_64 on Darwin and needs bison >= 3 (system bison is 2.x).
export PATH="$ROOT/.pixi/envs/default/bin:$PATH"
command -v bison >/dev/null || { echo "bison not found; run 'pixi install' first" >&2; exit 1; }

echo "building Ghidra decompiler for darwin/$ARCH (a few minutes)"
make -C "$SRC" ghidra_opt -j"$(sysctl -n hw.ncpu)" \
  OSDIR="$OSDIR" ARCH_TYPE="-arch $ARCH" ADDITIONAL_FLAGS="-mmacosx-version-min=11 -w"

mkdir -p "$DEST_DIR"
install -m 755 "$SRC/ghidra_opt" "$DEST"
file "$DEST"
echo "installed: $DEST"

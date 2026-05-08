#!/usr/bin/env bash
set -euo pipefail

OUT=firmware_package

rm -rf "$OUT"
mkdir -p "$OUT/src"

# All .py and .csv under src/, excluding tools/
find src \( -name "*.py" -o -name "*.csv" \) ! -path "*/tools/*" | while read -r f; do
    dst="$OUT/$f"
    mkdir -p "$(dirname "$dst")"
    cp "$f" "$dst"
done

cp flash.py "$OUT/"
cp docs/QUICK_START.md "$OUT/README.md"

uf2=$(ls ./*.uf2 2>/dev/null | head -1 || true)
if [ -n "$uf2" ]; then
    cp "$uf2" "$OUT/"
fi

cd "$OUT" && zip -r ../knife_level_firmware.zip .
echo "Built knife_level_firmware.zip"

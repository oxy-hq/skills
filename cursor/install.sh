#!/usr/bin/env bash
set -euo pipefail

# Install Oxy Cursor rules into a project
# Usage: ./install.sh [target-directory]

TARGET="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_SRC="$SCRIPT_DIR/rules"
RULES_DST="$TARGET/.cursor/rules"

if [ ! -d "$RULES_SRC" ]; then
  echo "Error: rules directory not found at $RULES_SRC"
  exit 1
fi

mkdir -p "$RULES_DST"

count=0
for file in "$RULES_SRC"/*.mdc; do
  [ -f "$file" ] || continue
  cp "$file" "$RULES_DST/"
  count=$((count + 1))
done

echo "Installed $count Oxy Cursor rules into $RULES_DST"
echo ""
echo "Rules installed:"
for file in "$RULES_DST"/oxy-*.mdc; do
  [ -f "$file" ] || continue
  echo "  - $(basename "$file")"
done
echo ""
echo "Open your project in Cursor to activate the rules."

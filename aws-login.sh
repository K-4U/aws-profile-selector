#!/usr/bin/env bash
if [[ "$0" == */* ]]; then
  SCRIPT_PATH="$0"
else
  SCRIPT_PATH="$(command -v "$0")"
fi
SCRIPT_PATH="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$SCRIPT_PATH")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
TEMP=$(mktemp)
python3 "$SCRIPT_DIR/main.py" "$TEMP"

source "$TEMP"
rm "$TEMP"
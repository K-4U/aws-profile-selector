TEMP=$(mktemp)
python3 main.py "$TEMP"

source "$TEMP"
rm "$TEMP"
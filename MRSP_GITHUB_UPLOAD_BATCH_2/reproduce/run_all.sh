#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then echo "Usage: $0 /path/to/CJ9"; exit 2; fi
python "$(dirname "$0")/run_full_reproduction.py" --cj9 "$1"

#!/usr/bin/env bash
# Run the whole pipeline end to end: extract -> transform -> dashboard.
# Usage:  ./run_all.sh        (uses the project venv if present)
set -euo pipefail
cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

"$PY" src/extract.py
"$PY" src/transform.py
"$PY" src/build_dashboard.py
echo "Done. Open output/index.html in a browser."

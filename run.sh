#!/usr/bin/env bash
# Clone, extract, compute, place in levels. About a minute on a Raspberry Pi.
set -euo pipefail
cd "$(dirname "$0")"
./scripts/00-clone.sh
python3 scripts/01-extract.py
python3 scripts/02-metrics.py
python3 scripts/03-tiers.py > /dev/null
./scripts/demo-date-rewrite.sh > results/demo-date-rewrite.txt
python3 scripts/check-method.py
echo "done: results/summary.md"

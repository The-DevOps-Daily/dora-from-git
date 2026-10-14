#!/usr/bin/env bash
# Record what a full run costs on this machine: hardware, wall time, clone size.
set -euo pipefail
cd "$(dirname "$0")/.."
{
  echo "date: $(date -u +%FT%TZ)"
  echo "machine: $(tr -d '\0' < /proc/device-tree/model 2>/dev/null || uname -m)"
  echo "kernel: $(uname -sr)"
  echo "git: $(git --version)"
  echo "python: $(python3 --version)"
  s=$(date +%s.%N)
  ./run.sh > /dev/null
  e=$(date +%s.%N)
  printf 'run.sh wall time: %.1f s\n' "$(echo "$e - $s" | bc -l)"
  echo "clone sizes:"
  du -sh data/repos/* | sed 's/^/  /'
  echo "  total: $(du -sh data/repos | cut -f1)"
} | tee results/benchmark.txt

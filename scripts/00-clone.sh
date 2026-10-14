#!/usr/bin/env bash
# Treeless clones: every commit and tag, no file contents. The metrics only read
# commit metadata, so history stays complete for the window at a fraction of the size.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/repos results
python3 - <<'PY' > /tmp/dora-repos.txt
import json
for r in json.load(open("repos.json"))["repos"]:
    print(r["name"], r["url"], r["branch"])
PY
echo "{" > results/clones.json.tmp
first=1
while read -r name url branch; do
  dir="data/repos/$name"
  if [ -d "$dir" ]; then
    git -C "$dir" fetch -q --tags origin "$branch"
  else
    git clone -q --filter=tree:0 --no-checkout "$url" "$dir"
  fi
  git -C "$dir" fetch -q --tags origin
  head=$(git -C "$dir" rev-parse "origin/$branch")
  commits=$(git -C "$dir" rev-list --count "origin/$branch")
  tags=$(git -C "$dir" tag | wc -l)
  [ $first -eq 1 ] || echo "," >> results/clones.json.tmp
  first=0
  printf '  "%s": {"url": "%s", "branch": "%s", "head": "%s", "commits_on_branch": %s, "tags": %s, "fetched_at": "%s"}' \
    "$name" "$url" "$branch" "$head" "$commits" "$tags" "$(date -u +%FT%TZ)" >> results/clones.json.tmp
  echo "$name: $head ($commits commits on $branch, $tags tags)"
done < /tmp/dora-repos.txt
echo "" >> results/clones.json.tmp
echo "}" >> results/clones.json.tmp
mv results/clones.json.tmp results/clones.json

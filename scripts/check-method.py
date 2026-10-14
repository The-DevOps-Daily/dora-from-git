#!/usr/bin/env python3
"""Cross-check stage 1 against plain git on random samples (seeded).

1. The side commits a merge brought in must equal
   `git rev-list --no-merges <first parent>..<merge>`.
2. The first final release that ships a commit must equal the earliest final
   tag that `git tag --contains` lists for it.
Output: results/method-checks.txt. Exits 1 on any mismatch.
"""
import gzip
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 7


def git(repo, *args):
    return subprocess.run(["git", "-C", str(ROOT / "data" / "repos" / repo), *args],
                          check=True, capture_output=True, text=True).stdout


def load(repo):
    with gzip.open(ROOT / "results" / "extract" / f"{repo}.json.gz", "rt") as f:
        return json.load(f)


def main():
    rng = random.Random(SEED)
    start = None
    lines, failures = [], 0
    for repo in ("kubernetes", "prometheus"):
        ex = load(repo)
        if start is None:
            from datetime import datetime
            start = int(datetime.fromisoformat(ex["window"]["start"]).timestamp())
        merges = [m for m in ex["landings"] if len(m["parents"]) > 1 and m["ct"] >= start]
        ok = 0
        for m in rng.sample(merges, 25):
            want = set(git(repo, "rev-list", "--no-merges", f"{m['parents'][0]}..{m['sha']}").split())
            got = {c["sha"] for c in m["brought"]}
            ok += want == got
        failures += 25 - ok
        lines.append(f"{repo}: side commits match git rev-list for {ok} of 25 random merges")
    for repo in ("kubernetes", "go", "uv"):
        ex = load(repo)
        finals = {t["name"]: t for t in ex["all_tags"] if not t["prerelease"]}
        pairs = [(c["sha"], d["name"]) for d in ex["deploys"] if not d["prerelease"]
                 for c in d["commits_vs_finals"] if len(c["parents"]) == 1]
        ok = 0
        for sha, name in rng.sample(pairs, 15):
            tags = [finals[t] for t in git(repo, "tag", "--contains", sha).split() if t in finals]
            first = min(tags, key=lambda t: (t["ts"], t["name"]))["name"] if tags else None
            ok += first == name
        failures += 15 - ok
        lines.append(f"{repo}: first final release matches git tag --contains for {ok} of 15 random commits")
    text = "\n".join(lines) + "\n"
    (ROOT / "results" / "method-checks.txt").write_text(text)
    print(text, end="")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

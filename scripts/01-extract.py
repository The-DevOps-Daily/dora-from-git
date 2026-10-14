#!/usr/bin/env python3
"""Stage 1: read commit metadata and tags from each clone into results/extract/<repo>.json.

Only plain git is used, so it works for any host. Nothing here decides what a
deploy or a failure is; stage 2 does that from this file.
"""
import gzip
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "repos.json").read_text())
OUT = ROOT / "results" / "extract"
SEP = "\x1f"
YEAR = 365 * 86400


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def iso_to_ts(value):
    return int(datetime.fromisoformat(value).timestamp())


def code_hash():
    h = hashlib.sha256()
    for f in (Path(__file__), ROOT / "repos.json", ROOT / "results" / "clones.json"):
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def read_tags(repo, pattern):
    fmt = SEP.join(["%(refname:short)", "%(objecttype)", "%(objectname)", "%(*objectname)", "%(creatordate:iso-strict)"])
    rx = re.compile(pattern)
    tags = []
    for line in git(repo, "for-each-ref", "refs/tags", f"--format={fmt}").splitlines():
        name, otype, obj, peeled, created = line.split(SEP)
        m = rx.match(name)
        if not m:
            continue
        nums = [int(g) if g else 0 for g in m.groups()[:3]]
        tags.append({
            "name": name,
            "annotated": otype == "tag",
            "commit": peeled if otype == "tag" else obj,
            # Annotated: the tagger date. Lightweight: the tagged commit's committer date.
            "ts": iso_to_ts(created),
            "major": nums[0], "minor": nums[1], "patch": nums[2],
            "prerelease": bool(m.groups()[3]),
        })
    tags.sort(key=lambda t: (t["ts"], t["name"]))
    return tags


def rev_list(repo, *args):
    """Commits as dicts: sha, parents, author ts, committer ts, subject."""
    fmt = SEP.join(["%H", "%P", "%at", "%ct", "%s"])
    rows = []
    for line in git(repo, "log", f"--format={fmt}", *args).splitlines():
        sha, parents, at, ct, subject = line.split(SEP, 4)
        rows.append({"sha": sha, "parents": parents.split(), "at": int(at), "ct": int(ct), "subject": subject})
    return rows


def shipped(repo, tag, earlier):
    """Commits reachable from tag and from none of the earlier tags."""
    if earlier:
        return rev_list(repo, tag["commit"], "--not", *[t["commit"] for t in earlier])
    return rev_list(repo, tag["commit"])


def landings_with_side_commits(repo, branch, since, until):
    """First-parent commits on the default branch, oldest first, each with the
    commits it brought in. A merge brings the commits of its second parent that
    no earlier landing brought; other commits bring only themselves."""
    graph = {c["sha"]: c for c in rev_list(repo, branch, f"--since={since - YEAR}")}
    firsts = rev_list(repo, "--first-parent", "--reverse", branch, f"--since={since}", f"--until={until}")
    mainline = {m["sha"] for m in firsts}
    # Everything already on the branch before the first landing counts as
    # landed, so the first merge in the slice does not absorb older history.
    assigned = set()
    if firsts:
        stack = list(firsts[0]["parents"][:1])
        while stack:
            sha = stack.pop()
            if sha in assigned or sha not in graph:
                continue
            assigned.add(sha)
            stack.extend(graph[sha]["parents"])
    out = []
    for m in firsts:
        brought = []
        if len(m["parents"]) > 1:
            stack = list(m["parents"][1:])
            while stack:
                sha = stack.pop()
                if sha in assigned or sha in mainline or sha not in graph:
                    continue
                assigned.add(sha)
                c = graph[sha]
                if len(c["parents"]) == 1:
                    brought.append({"sha": sha, "at": c["at"], "ct": c["ct"]})
                stack.extend(c["parents"])
        out.append({**m, "brought": brought})
    return out


def read_reverts(repo, since):
    fmt = SEP.join(["%H", "%at", "%ct", "%s", "%b"]) + "\x1e"
    reverts = []
    for rec in git(repo, "log", "--all", "-i", "--grep=^Revert", f"--since={since}", f"--format={fmt}").split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, at, ct, subject, body = rec.split(SEP, 4)
        target_sha = re.search(r"reverts? commit ([0-9a-f]{7,40})", body, re.I)
        target_cl = re.search(r"reverts? CL (\d+)", body, re.I)
        reverts.append({
            "sha": sha, "at": int(at), "ct": int(ct), "subject": subject,
            "target_sha": target_sha.group(1) if target_sha else None,
            "target_cl": target_cl.group(1) if target_cl else None,
        })
    return reverts


def gerrit_change_map(repo, since, wanted):
    """Gerrit only: change number -> commit, from the Reviewed-on trailer."""
    out = git(repo, "log", "--all", f"--since={since}",
              "--format=%H %(trailers:key=Reviewed-on,valueonly,separator=%x20)")
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            m = re.search(r"/\+/(\d+)", parts[1])
            if m and m.group(1) in wanted:
                found.setdefault(m.group(1), parts[0])
    return found


def main():
    start = iso_to_ts(CONFIG["window"]["start"])
    end = iso_to_ts(CONFIG["window"]["end"])
    OUT.mkdir(parents=True, exist_ok=True)
    clones = json.loads((ROOT / "results" / "clones.json").read_text())
    for r in CONFIG["repos"]:
        repo = ROOT / "data" / "repos" / r["name"]
        branch = f"origin/{r['branch']}"
        tags = read_tags(repo, r["tag_pattern"])

        # A final release also gets the set measured against earlier final
        # releases only, because a release candidate is not a production deploy.
        deploys = []
        for i, t in enumerate(tags):
            if not (start <= t["ts"] < end):
                continue
            entry = {**t, "commits": shipped(repo, t, tags[:i])}
            if not t["prerelease"]:
                entry["commits_vs_finals"] = shipped(repo, t, [p for p in tags[:i] if not p["prerelease"]])
            deploys.append(entry)

        # Landings from a year before the window: stage 2 needs them to know when
        # a change shipped early in the window first landed.
        landings = landings_with_side_commits(repo, branch, start - YEAR, end)
        reverts = read_reverts(repo, start - YEAR)
        wanted = {rv["target_cl"] for rv in reverts if rv["target_cl"]}
        cl_map = gerrit_change_map(repo, start - 2 * YEAR, wanted) if wanted else {}

        extract = {
            "repo": r["name"],
            "merge_style": r["merge_style"],
            "head": clones[r["name"]]["head"],
            "window": CONFIG["window"],
            "code_hash": code_hash(),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "all_tags": tags,
            "deploys": deploys,
            "landings": landings,
            "reverts": reverts,
            "cl_map": cl_map,
        }
        path = OUT / f"{r['name']}.json.gz"
        with gzip.open(path, "wt") as f:
            json.dump(extract, f)
        in_window = sum(start <= m["ct"] < end for m in landings)
        print(f"{r['name']}: {len(deploys)} tags in window ({sum(not d['prerelease'] for d in deploys)} final), "
              f"{in_window} landings on {r['branch']}, {len(reverts)} reverts since a year before -> "
              f"{path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

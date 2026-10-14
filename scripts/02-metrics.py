#!/usr/bin/env python3
"""Stage 2: compute the four DORA metrics from results/extract/*.json, once per definition.

Each metric has several defensible definitions. This script computes all of them
side by side, so the spread is visible. Output: results/metrics.json.
"""
import gzip
import hashlib
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "results" / "extract"
HOUR = 3600
DAY = 86400
HOTFIX_DAYS = 7  # a release followed this soon by the next patch on the same line counts as failed


def iso_to_ts(value):
    return int(datetime.fromisoformat(value).timestamp())


def pct(values, q):
    """Nearest-rank percentile; values need not be sorted."""
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, math.ceil(q / 100 * len(s)) - 1))
    return s[k]


def summary(values_seconds):
    if not values_seconds:
        return {"n": 0, "median_h": None, "p75_h": None}
    return {
        "n": len(values_seconds),
        "median_h": round(statistics.median(values_seconds) / HOUR, 2),
        "p75_h": round(pct(values_seconds, 75) / HOUR, 2),
    }


def metrics_for(ex):
    start = iso_to_ts(ex["window"]["start"])
    end = iso_to_ts(ex["window"]["end"])
    weeks = (end - start) / (7 * DAY)

    deploys = ex["deploys"]
    finals = [d for d in deploys if not d["prerelease"]]
    landings_all = ex["landings"]
    landings = [m for m in landings_all if start <= m["ct"] < end]

    # When each commit first landed on the default branch, and the landing it came with.
    landed = {}
    for m in landings_all:
        landed.setdefault(m["sha"], m)
        for c in m["brought"]:
            landed.setdefault(c["sha"], m)

    # ---- Deployment frequency -------------------------------------------------
    release_days = {datetime.fromtimestamp(d["ts"], timezone.utc).date() for d in finals}
    df = {
        "every_tag": len(deploys),
        "final_tags": len(finals),
        "release_days": len(release_days),
        "default_branch_landings": len(landings),
    }
    df = {k: {"count": v, "per_week": round(v / weeks, 4)} for k, v in df.items()}

    # ---- Change lead time (deploy = final release tag) ------------------------
    per_commit_author, per_commit_committer, per_commit_author_no_backports = [], [], []
    per_landing_from_landing, per_landing_from_first_commit = {}, {}
    backports = 0
    for d in finals:
        for c in d["commits_vs_finals"]:
            if len(c["parents"]) > 1:
                continue  # merge commits carry no change of their own
            per_commit_author.append(d["ts"] - c["at"])
            per_commit_committer.append(d["ts"] - c["ct"])
            m = landed.get(c["sha"])
            if m is not None:
                per_commit_author_no_backports.append(d["ts"] - c["at"])
            if m is None:
                # Never landed on the default branch: a backport or a release-branch commit.
                backports += 1
                key, land_ts, first_at = c["sha"], c["ct"], c["at"]
            else:
                key = m["sha"]
                land_ts = m["ct"]
                first_at = min([x["at"] for x in m["brought"]] or [m["at"]])
            # One value per landing (pull request or change), at its first release.
            if key not in per_landing_from_landing:
                per_landing_from_landing[key] = d["ts"] - land_ts
                per_landing_from_first_commit[key] = d["ts"] - first_at

    # Lead time if every tag counted, release candidates included: each commit at
    # the first tag that contained it.
    first_tag_author = [d["ts"] - c["at"] for d in deploys for c in d["commits"] if len(c["parents"]) == 1]

    # Lead time if every landing on the default branch counted as a deploy.
    landing_as_deploy, landing_merge, landing_single = [], [], []
    for m in landings:
        first_at = min([x["at"] for x in m["brought"]] or [m["at"]])
        landing_as_deploy.append(m["ct"] - first_at)
        (landing_merge if len(m["parents"]) > 1 else landing_single).append(m["ct"] - first_at)

    lt = {
        "commit_author_date_first_tag": summary(first_tag_author),
        "commit_author_date": summary(per_commit_author),
        "commit_committer_date": summary(per_commit_committer),
        "commit_author_date_without_backports": summary(per_commit_author_no_backports),
        "change_from_landing": summary(list(per_landing_from_landing.values())),
        "change_from_first_commit": summary(list(per_landing_from_first_commit.values())),
        "landing_is_deploy": summary(landing_as_deploy),
    }
    # The same measure split by how the change landed: a merge commit keeps the
    # side branch and its dates, a squash or rebase writes one new commit.
    landing_split = {
        "merge_commit_landings": summary(landing_merge),
        "single_commit_landings": summary(landing_single),
        # Squash and direct pushes: the author date is the landing time, to the minute.
        "single_commit_landings_author_within_60s_of_committer": sum(
            1 for m in landings if len(m["parents"]) == 1 and abs(m["ct"] - m["at"]) < 60),
    }

    # ---- Change failure rate and recovery (deploy = final release tag) --------
    # 1. Hotfix: the next release on the same major.minor line came within HOTFIX_DAYS.
    by_line = {}
    for t in ex["all_tags"]:
        if not t["prerelease"]:
            by_line.setdefault((t["major"], t["minor"]), []).append(t)
    hotfix_failed, hotfix_recovery = [], []
    for d in finals:
        line = sorted(by_line[(d["major"], d["minor"])], key=lambda t: (t["ts"], t["patch"]))
        # Only fixes released inside the window, like the revert rule.
        later = [t for t in line if t["patch"] > d["patch"] and d["ts"] <= t["ts"] < end]
        if later and later[0]["ts"] - d["ts"] <= HOTFIX_DAYS * DAY:
            hotfix_failed.append(d["name"])
            hotfix_recovery.append(later[0]["ts"] - d["ts"])

    # 2. The release ships at least one revert commit.
    has_revert = [d["name"] for d in finals
                  if any(c["subject"].lower().startswith("revert") for c in d["commits_vs_finals"])]

    # 3. A later release reverts a change this release shipped.
    shipped_in = {}
    for d in sorted(finals, key=lambda x: x["ts"]):
        for c in d["commits_vs_finals"]:
            shipped_in.setdefault(c["sha"], d)
    revert_shas = {rv["sha"]: rv for rv in ex["reverts"]}

    def resolve(rv):
        if rv["target_sha"]:
            for sha in shipped_in:
                if sha.startswith(rv["target_sha"]):
                    return sha
            return None
        if rv["target_cl"]:
            return ex["cl_map"].get(rv["target_cl"])
        return None

    reverted_failed, reverted_recovery = {}, []
    unresolved_by_parser, target_not_in_earlier_release = 0, 0
    for d in finals:
        for c in d["commits_vs_finals"]:
            rv = revert_shas.get(c["sha"])
            if not rv or len(c["parents"]) > 1 or not c["subject"].lower().startswith("revert"):
                continue  # same candidates as rule 2: a non-merge commit whose subject starts with Revert
            if not rv["target_sha"] and not rv["target_cl"]:
                unresolved_by_parser += 1
                continue
            target = resolve(rv)
            if target is None or target not in shipped_in or shipped_in[target]["ts"] >= d["ts"]:
                # Reverted before it reached a release in the window, or shipped earlier.
                target_not_in_earlier_release += 1
                continue
            origin = shipped_in.get(target)
            if origin is None or origin["ts"] >= d["ts"] or origin["name"] in reverted_failed:
                continue
            reverted_failed[origin["name"]] = d["name"]
            reverted_recovery.append(d["ts"] - origin["ts"])

    n = len(finals)
    cfr = {
        "hotfix_within_7_days": {"failed": len(hotfix_failed), "of": n,
                                 "rate": round(len(hotfix_failed) / n, 3) if n else None},
        "ships_a_revert": {"failed": len(has_revert), "of": n,
                           "rate": round(len(has_revert) / n, 3) if n else None},
        "shipped_change_later_reverted": {"failed": len(reverted_failed), "of": n,
                                          "rate": round(len(reverted_failed) / n, 3) if n else None,
                                          "reverts_unresolved_by_parser": unresolved_by_parser,
                                          "reverts_of_unreleased_or_older_changes": target_not_in_earlier_release},
    }
    recovery = {
        "hotfix_within_7_days": summary(hotfix_recovery),
        "shipped_change_later_reverted": summary(reverted_recovery),
    }

    return {
        "repo": ex["repo"],
        "merge_style": ex["merge_style"],
        "head": ex["head"],
        "code_hash": ex["code_hash"],
        "weeks": round(weeks, 2),
        "deployment_frequency": df,
        "lead_time": lt,
        "landing_is_deploy_by_style": landing_split,
        "backport_commits": backports,
        "change_failure_rate": cfr,
        "recovery_time": recovery,
        "details": {
            "hotfix_failed": hotfix_failed,
            "ships_a_revert": has_revert,
            "reverted": reverted_failed,
        },
    }


def main():
    results = []
    hashes = set()
    configured = [r["name"] for r in json.loads((ROOT / "repos.json").read_text())["repos"]]
    for name in configured:
        with gzip.open(EXTRACT / f"{name}.json.gz", "rt") as f:
            ex = json.load(f)
        hashes.add(ex["code_hash"])
        results.append(metrics_for(ex))
    if len(hashes) != 1:
        print(f"refusing: extracts come from different code versions {hashes}", file=sys.stderr)
        return 1
    out = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "extract_code_hash": hashes.pop(),
           "metrics_code_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16],
           "hotfix_days": HOTFIX_DAYS, "repos": results}
    (ROOT / "results" / "metrics.json").write_text(json.dumps(out, indent=2) + "\n")
    for r in results:
        print(f"== {r['repo']} ({r['merge_style']})")
        print("  deploys/week:", {k: v["per_week"] for k, v in r["deployment_frequency"].items()})
        print("  lead time median h:", {k: v["median_h"] for k, v in r["lead_time"].items()})
        print("  CFR:", {k: v["rate"] for k, v in r["change_failure_rate"].items()})
        print("  recovery median h:", {k: v["median_h"] for k, v in r["recovery_time"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())

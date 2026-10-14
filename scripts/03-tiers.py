#!/usr/bin/env python3
"""Stage 3: place each definition's result in the 2024 DORA performance levels.

The levels come from the 2024 Accelerate State of DevOps report (v. 2024.3,
page 13). They describe survey clusters, not official thresholds, so this is
the reading a dashboard would show, not a verdict on the projects.
Output: results/tiers.json and results/summary.md.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEEKS_PER_MONTH = 52.1775 / 12
WEEKS_PER_SIX_MONTHS = 52.1775 / 2

DF_LABELS = {
    "every_tag": "every tag (release candidates too)",
    "final_tags": "every final release tag",
    "release_days": "days with a final release",
    "default_branch_landings": "every landing on the default branch",
}
LT_LABELS = {
    "commit_author_date_first_tag": "commit author date to first tag (candidates too)",
    "commit_author_date": "commit author date to final release",
    "commit_committer_date": "commit committer date to final release",
    "commit_author_date_without_backports": "commit author date to final release, backports left out",
    "change_from_landing": "landing on default branch to final release (per change)",
    "change_from_first_commit": "first commit of the change to final release (per change)",
    "landing_is_deploy": "first commit to landing, if landing is the deploy (per change)",
}
CFR_LABELS = {
    "hotfix_within_7_days": "next patch on the same line within 7 days",
    "ships_a_revert": "release ships any revert commit",
    "shipped_change_later_reverted": "a later release reverts a change it shipped",
}


def df_level(per_week):
    if per_week > 7:
        return "Elite"
    if per_week >= 1:
        return "High"
    if per_week >= 1 / WEEKS_PER_MONTH:
        return "Medium"
    if per_week >= 1 / WEEKS_PER_SIX_MONTHS:
        return "Low"
    return "below Low"


def lt_level(hours):
    if hours is None:
        return "n/a"
    if hours < 24:
        return "Elite"
    if hours < 24 * 7:
        return "High"
    if hours < 24 * 30:
        return "Medium"
    if hours < 24 * 182.5:
        return "Low"
    return "below Low"


def fmt_hours(h):
    if h is None:
        return "n/a"
    if h < 48:
        return f"{h:.1f} h"
    return f"{h / 24:.1f} d"


def main():
    metrics = json.loads((ROOT / "results" / "metrics.json").read_text())
    out = {"source": "2024 Accelerate State of DevOps report, v. 2024.3, p. 13",
           "metrics_code_hash": metrics["metrics_code_hash"], "repos": []}
    md = ["# Results", "", f"Window: {metrics['repos'][0]['weeks']} weeks. "
          f"Levels: 2024 DORA report, p. 13. Code: extract {metrics['extract_code_hash']}, "
          f"metrics {metrics['metrics_code_hash']}.", ""]
    for r in metrics["repos"]:
        rec = {"repo": r["repo"], "merge_style": r["merge_style"], "df": {}, "lt": {}}
        md += [f"## {r['repo']} ({r['merge_style']}, head {r['head'][:12]})", "",
               "| Deploy means | Deploys | Per week | Level |", "| --- | ---: | ---: | --- |"]
        for k, v in r["deployment_frequency"].items():
            lvl = df_level(v["per_week"])
            rec["df"][k] = {**v, "level": lvl}
            md.append(f"| {DF_LABELS[k]} | {v['count']} | {v['per_week']:.2f} | {lvl} |")
        md += ["", "| Lead time measured from | Changes | Median | p75 | Level (median) |",
               "| --- | ---: | ---: | ---: | --- |"]
        for k, v in r["lead_time"].items():
            lvl = lt_level(v["median_h"])
            rec["lt"][k] = {**v, "level": lvl}
            md.append(f"| {LT_LABELS[k]} | {v['n']} | {fmt_hours(v['median_h'])} | {fmt_hours(v['p75_h'])} | {lvl} |")
        md += ["", "| A release failed if | Failed | Of | Rate |", "| --- | ---: | ---: | ---: |"]
        for k, v in r["change_failure_rate"].items():
            md.append(f"| {CFR_LABELS[k]} | {v['failed']} | {v['of']} | {v['rate'] * 100:.1f}% |")
        rec["cfr"] = r["change_failure_rate"]
        rec["recovery"] = r["recovery_time"]
        md += ["", "Recovery time (median): " + ", ".join(
            f"{CFR_LABELS[k]}: {fmt_hours(v['median_h'])} (n={v['n']})" for k, v in r["recovery_time"].items()), ""]
        df_levels = sorted({v["level"] for v in rec["df"].values()})
        lt_levels = sorted({v["level"] for v in rec["lt"].values()})
        rec["df_levels_reached"] = df_levels
        rec["lt_levels_reached"] = lt_levels
        md += [f"Deployment frequency levels reached: {', '.join(df_levels)}. "
               f"Lead time levels reached: {', '.join(lt_levels)}.", ""]
        out["repos"].append(rec)
    (ROOT / "results" / "tiers.json").write_text(json.dumps(out, indent=2) + "\n")
    (ROOT / "results" / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())

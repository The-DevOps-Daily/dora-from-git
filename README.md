# dora-from-git

```bash
./run.sh
```

Compute the four DORA metrics (deployment frequency, change lead time, change failure rate, recovery time) from plain Git history, once per definition, and see how far the definition alone moves the result. It needs `git`, `python3` (standard library only) and `bc`. A run took 56 seconds on a Raspberry Pi 5, and the treeless clones of the four repos take 134 MB.

The repos it measures, one per merge style, over 1 October 2025 to 1 October 2026:

| Repo | Merge style | Deploy record |
| --- | --- | --- |
| kubernetes/kubernetes | merge commits | `vX.Y.Z` tags, alpha, beta and rc tags |
| astral-sh/uv | squash | `X.Y.Z` tags |
| golang/go (go.googlesource.com) | rebase through Gerrit, linear history | `goX.Y.Z` tags, beta and rc tags |
| prometheus/prometheus | mixed: about half merge commits, half squash | `vX.Y.Z` tags and rc tags |

Edit `repos.json` to point it at your own repositories. Any Git host works: nothing here calls a forge API.

## What each script does

| Script | Reads | Writes |
| --- | --- | --- |
| `scripts/00-clone.sh` | `repos.json` | treeless clones in `data/repos/` (commits and tags, no file contents), `results/clones.json` with the head of each |
| `scripts/01-extract.py` | the clones | `results/extract/<repo>.json.gz`: tags and the commits each one shipped, every first-parent commit on the default branch with the commits it brought in, and every revert with the commit or Gerrit change it names |
| `scripts/02-metrics.py` | the extracts | `results/metrics.json`: every metric under every definition |
| `scripts/03-tiers.py` | `results/metrics.json` | `results/tiers.json` and `results/summary.md`: each result placed in the 2024 DORA performance levels |
| `scripts/demo-date-rewrite.sh` | nothing | `results/demo-date-rewrite.txt`: one change landed three ways (merge commit, squash, rebase) and the lead time each one leaves in Git |
| `scripts/check-method.py` | the extracts and the clones | `results/method-checks.txt`: stage 1 cross-checked against plain git on seeded random samples |

Each stage stamps its output with a hash of its own code and inputs. `02-metrics.py` refuses to mix extracts from different extract code.

## The definitions

- **Deploy:** every tag, release candidates included; every final release tag; days with a final release; or every first-parent commit on the default branch ("merge to main is a deploy").
- **Lead time:** from the commit author date, the committer date, the time the change landed on the default branch, or the first commit of the change; to the first tag or to the first final release that contains it. Per commit or per change (one landing on the default branch).
- **Failure:** the next patch on the same `major.minor` line came within 7 days; the release ships any commit whose subject starts with "Revert"; or a later release reverts a change this release shipped.
- **Recovery:** from the failed release to the release that fixed it, for the two failure rules that name one.

The performance levels come from the 2024 Accelerate State of DevOps report (v. 2024.3, page 13). They describe survey clusters, not official thresholds, and the report gives single values for change failure rate (5%, 20%, 10%, 40%), so `03-tiers.py` only places deployment frequency and lead time.

## Results

See `results/summary.md` for every number, and the post for what they mean. In short: each repo reaches two or three different levels for the same metric depending on the definition, and the merge button decides whether Git still knows when the work started.

## Checks done on the method

`scripts/check-method.py` (seeded) compares stage 1 with plain git: the side commits each merge brought in against `git rev-list --no-merges <first-parent>..<merge>` on 50 random merges, and the first final release that ships a commit against `git tag --contains` on 45 random commits. All 95 match; see `results/method-checks.txt`.

## License

MIT

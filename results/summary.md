# Results

Window: 52.14 weeks. Levels: 2024 DORA report, p. 13. Code: extract ce8e4cd646665feb, metrics 4261685f5886049a.

## go (rebase (Gerrit, linear), head e60b4c37fa34)

| Deploy means | Deploys | Per week | Level |
| --- | ---: | ---: | --- |
| every tag (release candidates too) | 36 | 0.69 | Medium |
| every final release tag | 30 | 0.57 | Medium |
| days with a final release | 15 | 0.29 | Medium |
| every landing on the default branch | 3422 | 65.63 | Elite |

| Lead time measured from | Changes | Median | p75 | Level (median) |
| --- | ---: | ---: | ---: | --- |
| commit author date to first tag (candidates too) | 3878 | 69.1 d | 117.9 d | Low |
| commit author date to final release | 3878 | 127.5 d | 175.2 d | Low |
| commit committer date to final release | 3878 | 112.0 d | 159.1 d | Low |
| commit author date to final release, backports left out | 3415 | 138.0 d | 182.8 d | Low |
| landing on default branch to final release (per change) | 3521 | 110.0 d | 153.7 d | Low |
| first commit of the change to final release (per change) | 3521 | 125.3 d | 172.4 d | Low |
| first commit to landing, if landing is the deploy (per change) | 3422 | 4.1 d | 15.0 d | High |

| A release failed if | Failed | Of | Rate |
| --- | ---: | ---: | ---: |
| next patch on the same line within 7 days | 4 | 30 | 13.3% |
| release ships any revert commit | 2 | 30 | 6.7% |
| a later release reverts a change it shipped | 1 | 30 | 3.3% |

Recovery time (median): next patch on the same line within 7 days: 6.0 d (n=4), a later release reverts a change it shipped: 189.9 d (n=1)

Deployment frequency levels reached: Elite, Medium. Lead time levels reached: High, Low.

## kubernetes (merge commits, head 1c99cdec1bfc)

| Deploy means | Deploys | Per week | Level |
| --- | ---: | ---: | --- |
| every tag (release candidates too) | 63 | 1.21 | High |
| every final release tag | 42 | 0.81 | Medium |
| days with a final release | 15 | 0.29 | Medium |
| every landing on the default branch | 3286 | 63.02 | Elite |

| Lead time measured from | Changes | Median | p75 | Level (median) |
| --- | ---: | ---: | ---: | --- |
| commit author date to first tag (candidates too) | 6812 | 25.9 d | 51.0 d | Medium |
| commit author date to final release | 6091 | 76.6 d | 112.8 d | Low |
| commit committer date to final release | 6091 | 63.1 d | 98.5 d | Low |
| commit author date to final release, backports left out | 5486 | 81.9 d | 117.5 d | Low |
| landing on default branch to final release (per change) | 3734 | 60.6 d | 95.6 d | Low |
| first commit of the change to final release (per change) | 3734 | 77.0 d | 113.0 d | Low |
| first commit to landing, if landing is the deploy (per change) | 3286 | 5.2 d | 22.5 d | High |

| A release failed if | Failed | Of | Rate |
| --- | ---: | ---: | ---: |
| next patch on the same line within 7 days | 0 | 42 | 0.0% |
| release ships any revert commit | 4 | 42 | 9.5% |
| a later release reverts a change it shipped | 1 | 42 | 2.4% |

Recovery time (median): next patch on the same line within 7 days: n/a (n=0), a later release reverts a change it shipped: 125.9 d (n=1)

Deployment frequency levels reached: Elite, High, Medium. Lead time levels reached: High, Low, Medium.

## prometheus (mixed: merge commits and squash, head 6f01fa9c5ffc)

| Deploy means | Deploys | Per week | Level |
| --- | ---: | ---: | --- |
| every tag (release candidates too) | 39 | 0.75 | Medium |
| every final release tag | 26 | 0.50 | Medium |
| days with a final release | 24 | 0.46 | Medium |
| every landing on the default branch | 1241 | 23.80 | Elite |

| Lead time measured from | Changes | Median | p75 | Level (median) |
| --- | ---: | ---: | ---: | --- |
| commit author date to first tag (candidates too) | 1936 | 31.9 d | 45.3 d | Low |
| commit author date to final release | 1936 | 40.0 d | 54.1 d | Low |
| commit committer date to final release | 1936 | 39.0 d | 50.7 d | Low |
| commit author date to final release, backports left out | 1889 | 40.5 d | 54.2 d | Low |
| landing on default branch to final release (per change) | 1305 | 36.4 d | 47.1 d | Low |
| first commit of the change to final release (per change) | 1305 | 39.6 d | 51.3 d | Low |
| first commit to landing, if landing is the deploy (per change) | 1241 | 0.3 h | 2.0 d | Elite |

| A release failed if | Failed | Of | Rate |
| --- | ---: | ---: | ---: |
| next patch on the same line within 7 days | 5 | 26 | 19.2% |
| release ships any revert commit | 7 | 26 | 26.9% |
| a later release reverts a change it shipped | 1 | 26 | 3.8% |

Recovery time (median): next patch on the same line within 7 days: 5.2 d (n=5), a later release reverts a change it shipped: 14.9 d (n=1)

Deployment frequency levels reached: Elite, Medium. Lead time levels reached: Elite, Low.

## uv (squash, head a79aac95dc8f)

| Deploy means | Deploys | Per week | Level |
| --- | ---: | ---: | --- |
| every tag (release candidates too) | 101 | 1.94 | High |
| every final release tag | 101 | 1.94 | High |
| days with a final release | 93 | 1.78 | High |
| every landing on the default branch | 3132 | 60.07 | Elite |

| Lead time measured from | Changes | Median | p75 | Level (median) |
| --- | ---: | ---: | ---: | --- |
| commit author date to first tag (candidates too) | 3126 | 30.1 h | 3.4 d | High |
| commit author date to final release | 3126 | 30.1 h | 3.4 d | High |
| commit committer date to final release | 3126 | 28.6 h | 3.3 d | High |
| commit author date to final release, backports left out | 3126 | 30.1 h | 3.4 d | High |
| landing on default branch to final release (per change) | 3126 | 28.6 h | 3.3 d | High |
| first commit of the change to final release (per change) | 3126 | 30.1 h | 3.4 d | High |
| first commit to landing, if landing is the deploy (per change) | 3132 | 0.0 h | 0.0 h | Elite |

| A release failed if | Failed | Of | Rate |
| --- | ---: | ---: | ---: |
| next patch on the same line within 7 days | 88 | 101 | 87.1% |
| release ships any revert commit | 20 | 101 | 19.8% |
| a later release reverts a change it shipped | 5 | 101 | 5.0% |

Recovery time (median): next patch on the same line within 7 days: 2.9 d (n=88), a later release reverts a change it shipped: 34.5 h (n=5)

Deployment frequency levels reached: Elite, High. Lead time levels reached: Elite, High.


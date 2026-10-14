#!/usr/bin/env bash
# One change, three merge buttons, three lead times.
# Two commits are written on Monday and Wednesday, and the change lands on
# Friday. Every date is fixed, so the output is the same on every machine.
set -euo pipefail
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null

at() { GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" "${@:2}"; }

setup() {
  git init -q -b main "$1"
  cd "$1"
  git config user.name dev
  git config user.email dev@example.com
  echo base > README && git add README
  at "2026-09-07T09:00:00Z" git commit -q -m "base"
  git checkout -q -b feature
  echo one > feature.txt && git add feature.txt
  at "2026-09-07T10:00:00Z" git commit -q -m "feature: part 1"
  echo two >> feature.txt && git add feature.txt
  at "2026-09-09T15:00:00Z" git commit -q -m "feature: part 2"
  git checkout -q main
  # Something else lands first, so the branch is behind.
  echo fix > fix.txt && git add fix.txt
  at "2026-09-10T12:00:00Z" git commit -q -m "unrelated fix"
}

land="2026-09-11T16:00:00Z"   # Friday: the change lands on main

lead() {
  # The commits the change put on main, then lead time from the earliest
  # author date and from the earliest committer date to the landing.
  local style=$1 range=$2 last
  last=$(git log -1 --format=%ct main)
  echo "$style:"
  git log --no-merges --format='  %s | author %aI | committer %cI' "$range"
  local a c
  a=$(git log --no-merges --format=%at "$range" | sort -n | head -1)
  c=$(git log --no-merges --format=%ct "$range" | sort -n | head -1)
  printf '  lead time from author date %5.1f h, from committer date %5.1f h\n\n' \
    "$(echo "($last - $a) / 3600" | bc -l)" "$(echo "($last - $c) / 3600" | bc -l)"
}

( setup "$tmp/merge"
  at "$land" git merge -q --no-ff feature -m "Merge feature"
  lead "merge commit" "main^1..main" )

( setup "$tmp/squash"
  at "$land" git merge -q --squash feature >/dev/null 2>&1
  at "$land" git commit -q -m "feature (squashed)"
  lead "squash" "main~1..main" )

( setup "$tmp/rebase"
  git checkout -q feature
  GIT_COMMITTER_DATE="$land" git rebase -q main
  git checkout -q main
  git merge -q --ff-only feature
  lead "rebase" "main~2..main" )


#!/bin/bash
# Calculate sort twice

cd "$(dirname "$0")" || exit 1

[ -z "$PASH_TOP" ] && {
  echo "PASH_TOP not set, maybe $(git rev-parse --show-toplevel)?"
  exit
}

IN=${IN:-$PASH_TOP/evaluation/benchmarks/oneliners/inputs/1G.txt}

cat "$IN" | tr A-Z a-z | sort | sort -r > ${OUT}stdout.txt

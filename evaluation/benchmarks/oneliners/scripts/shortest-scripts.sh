#!/bin/bash
# Find the shortest scripts
# From "Wicked Cool Shell Scripts", 2nd Ed., pg. 7
# +p.95 multiple sed
# +p.XX crawler

# FIX: Input here should be a set of commands, more precisely, the ones on this specific machine.

cd "$(dirname "$0")" || exit 1

[ -z "$PASH_TOP" ] && {
  echo "PASH_TOP not set, maybe $(git rev-parse --show-toplevel)?"
  exit
}

IN=${IN:-$PASH_TOP/evaluation/benchmarks/oneliners/inputs/all_cmds.txt}
# cat "$IN" | xargs file | grep "shell script" | cut -d : -f 1 | xargs -L 1 wc -l | grep -v '^0$' | sort -n | head -n 15 > ${OUT}stdout.txt
cat "$IN" | xargs file > ${OUT}stdout.txt
# cat "$IN" | xargs file | grep "shell script" 
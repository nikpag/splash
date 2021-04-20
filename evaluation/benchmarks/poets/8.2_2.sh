#!/bin/bash 
# tag: bigrams_appear_twice.sh
# set -e

# Bigrams that appear twice
IN=${IN:-$PASH_TOP/evaluation/benchmarks/poets/input/pg/}
cat ${IN}* | awk "\$1 == 2 {print \$2, \$3}" 

#!/bin/bash

# tag: wav-to-mp3
set -e
IN=${WAV:-$PASH_TOP/evaluation/benchmarks/for-loops/input/wav}
OUT=${OUT:-$PASH_TOP/evaluation/benchmarks/for-loops/output/mp3}
mkdir -p ${OUT}
for FILE in $IN/*.wav ; 
do 
    ffmpeg -y -i $FILE -f mp3 -ab 192000 $OUT/$(basename $FILE).mp3 > '$OUT'/'$(basename $FILE).log'; 
done
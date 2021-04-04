#!/bin/bash

# time: print real in seconds, to simplify parsing
TIMEFORMAT="%3R" # %3U %3S"

if [[ -z "$PASH_TOP" ]]; then
  echo "Need to provide PASH_TOP, possibly $(git rev-parse --show-toplevel)" 1>&2
  exit 1
fi

oneliners_pash(){
  par_times_file="par.res"
  par_outputs_suffix="par.out"
  outputs_dir="outputs"
  pash_logs_dir="pash_logs"
  width=16
  if [ -e "oneliners/$par_times_file" ]; then
    echo "skipping oneliners/$par_times_file"
    return 0
  fi
  
  cd oneliners/

  cd ./input/
  ./setup.sh --full
  cd ..

  mkdir -p "$outputs_dir"
  mkdir -p "$pash_logs_dir"

  scripts_inputs=(
    "nfa-regex;100M.txt"
    "sort;3G.txt"
    "top-n;1G.txt"
    "wf;3G.txt"
    "spell;1G.txt"
    "diff;3G.txt"
    "bi-grams;1G.txt"
    "set-diff;3G.txt"
    "sort-sort;1G.txt"
    "shortest-scripts;all_cmdsx100.txt"
  )

  touch "$par_times_file"
  echo executing one-liners with pash $(date) | tee -a "$par_times_file"
  echo '' >> "$par_times_file"

  for script_input in ${scripts_inputs[@]}
  do
    IFS=";" read -r -a script_input_parsed <<< "${script_input}"
    script="${script_input_parsed[0]}"
    input="${script_input_parsed[1]}"
    export IN="$PASH_TOP/evaluation/benchmarks/oneliners/input/$input"
    printf -v pad %30s
    padded_script="${script}.sh:${pad}"
    padded_script=${padded_script:0:30}

    par_outputs_file="${outputs_dir}/${script}.${par_outputs_suffix}"
    pash_log="${pash_logs_dir}/${script}.pash.log"

    echo "${padded_script}" $({ time "$PASH_TOP/pa.sh" --r_split --dgsh_tee -d 1 -w "${width}" --log_file "${pash_log}" ${script}.sh > "$par_outputs_file"; } 2>&1) | tee -a "$par_times_file"
  done

  cd ..
}

unix50(){
  times_file="par.res"
  outputs_suffix="par.out"
  outputs_dir="outputs"
  pash_logs_dir="pash_logs"
  width=16
  if [ -e "unix50/${times_file}" ]; then
    echo "skipping unix50/${times_file}"
    return 0
  fi

  cd unix50/

  cd input/
  ./setup.sh
  cd ..

  mkdir -p "$outputs_dir"
  mkdir -p "$pash_logs_dir"

  touch "$times_file"
  echo executing Unix50 $(date) | tee -a "$times_file"
  echo '' >> "$times_file"

  # FIXME this is the input prefix; do we want all to be IN 
  export IN_PRE=$PASH_TOP/evaluation/benchmarks/unix50/input

  for number in `seq 36`
  do
    script="${number}.sh"
    
    printf -v pad %20s
    padded_script="${script}:${pad}"
    padded_script=${padded_script:0:20}

    outputs_file="${outputs_dir}/${script}.${outputs_suffix}"
    pash_log="${pash_logs_dir}/${script}.pash.log"

    echo "${padded_script}" $({ time "$PASH_TOP/pa.sh" --r_split --dgsh_tee -d 1 -w "${width}" --log_file "${pash_log}" ${script}.sh > "$outputs_file"; } 2>&1) | tee -a "$times_file"
  done  
  cd ..
}

poets_pash(){
  times_file="par.res"
  outputs_suffix="par.out"
  outputs_dir="outputs"
  pash_logs_dir="pash_logs"
  width=16
  if [ -e "poets/${times_file}" ]; then
    echo "skipping poets/${times_file}"
    return 0
  fi

  cd poets/

  cd input/
  ./setup.sh
  cd ..

  mkdir -p "$outputs_dir"
  mkdir -p "$pash_logs_dir"

  names_scripts=(
    "1syllable_words;6_4"
    "2syllable_words;6_5"
    "4letter_words;6_2"
    "bigrams_appear_twice;8.2_2"
    "bigrams;4_3"
    "compare_exodus_genesis;8.3_3"
    "count_consonant_seq;7_2"
    # "count_morphs;7_1"
    "count_trigrams;4_3b"
    "count_vowel_seq;2_2"
    "count_words;1_1"
    "find_anagrams;8.3_2"
    "merge_upper;2_1"
    "sort;3_1"
    "sort_words_by_folding;3_2"
    "sort_words_by_num_of_syllables;8_1"
    "sort_words_by_rhyming;3_3"
    # "trigram_rec;6_1"
    "uppercase_by_token;6_1_1"
    "uppercase_by_type;6_1_2"
    "verses_2om_3om_2instances;6_7"
    "vowel_sequencies_gr_1K;8.2_1"
    "words_no_vowels;6_3"
  )

  touch "$times_file"
  echo executing Unix-for-poets with pash $(date) | tee -a "$times_file"
  echo '' >> "$times_file"

  for name_script in ${names_scripts[@]}
  do
    IFS=";" read -r -a name_script_parsed <<< "${name_script}"
    name="${name_script_parsed[0]}"
    script="${name_script_parsed[1]}"
    export IN="$PASH_TOP/evaluation/benchmarks/poets/input/genesis"
    printf -v pad %30s
    padded_script="${name}.sh:${pad}"
    padded_script=${padded_script:0:30}

    outputs_file="${outputs_dir}/${script}.${outputs_suffix}"
    pash_log="${pash_logs_dir}/${script}.pash.log"

    echo "${padded_script}" $({ time "$PASH_TOP/pa.sh" --r_split --dgsh_tee -d 1 -w "${width}" --log_file "${pash_log}" ${script}.sh > "$outputs_file"; } 2>&1) | tee -a "$times_file"
  done
  cd ..
}
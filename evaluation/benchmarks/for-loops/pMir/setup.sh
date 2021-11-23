#!/usr/bin/env bash
#
# Parse the provided file, install packages
#
install() {
  
  file=$1
  while IFS= read -r package
  do
    echo "Installing $package..."
    npm list $package >/dev/null 2>/dev/null || npm install $package >/dev/null 2>error.log
    #if grep -q "ERR!" error.log; then
    #  echo "$1" >> ../$package.results/errOnInstall 
    #fi
    #rm error.log
  done < "$file"
}

npm i -g @andromeda/mir-sa

if [ "$#" -eq 1 ]; then
  mkdir -p $1.results
  install $1
else
  echo "You need to provide an input file..."
fi
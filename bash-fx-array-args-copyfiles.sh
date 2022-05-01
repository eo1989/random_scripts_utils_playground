#!/usr/local/bin/bash

function copyFiles() {
	local msg="$1"   # Save 1st arg in a var
	shift            # shift all args left (orig $1 is lost)
	local arr=("$@") # rebuild array with rest args
	for i in "${arr[@]}"; do
		echo "$msg $i"
	done
}

array=("one" "two" "three")

copyFiles "Copying" "${array[@]}"

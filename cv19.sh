#!/usr/bin/env bash

# @description: Simple script to get the death percentage (maybe others in the future)
#               for covid-19

read -rp "Enter Country: " country
stats=$(curl -s "https://corona-stats.online/${country}/?source=2&format=json" | jq '.data[]')
deaths=$(echo "${stats}" | jq '.deaths')
cases=$(echo "${stats}" | jq '.cases')
deathrate=''$(echo "(${deaths}" / "${cases}) * 100" | bc -l | cut -c -3)'%'
deathrate=$(printf "😷 Cases:  %s
Deaths: %s
%s 💀/😷 in ${country}
form COVID-19" "${cases}" "${deaths}" "${deathrate}")
# notify-send "${deathrate}"
echo "${deathrate}"

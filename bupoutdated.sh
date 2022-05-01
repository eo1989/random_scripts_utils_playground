#! /usr/bin/env bash

for item in $(brew outdated); do brew upgrade "${item}"; done

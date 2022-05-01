# for d in *; do
#   if [[ -d "$d"/.git ]]; then
#     (cd $d; git pull)
#   fi
# done
realpath () {
  [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

for d in *; do
  if [[ -d "${d}"/.git ]]; then
    (cd $d; echo `realpath` && git pull)
  fi
done

# orrrr


# for d in */; do [[ -d "$d/.git" ]] && (cd $d && git pull); done


# orrrrr

# for d in $(find $HOME/ -type d -name .git); do
#   (cd "$d"/..; git pull);
# done

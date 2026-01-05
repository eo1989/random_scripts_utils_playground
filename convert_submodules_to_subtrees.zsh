#!/usr/bin/env zsh
set -euo pipefail

# Converts all git submodules (from .gitmodules) into git subtrees at the same paths.
# Default behavior: uses --squash and detects remote default branch via ls-remote.
#
# Usage:
#   ./convert_submodules_to_subtrees.zsh
#
# Optional env vars:
#   SQUASH=1|0        (default 1)
#   DRY_RUN=1|0       (default 0)
#   KEEP_WORKTREE=1|0 (default 0)  # if 1, does not rm -rf the path after git rm --cached

SQUASH="${SQUASH:-1}"
DRY_RUN="${DRY_RUN:-0}"
KEEP_WORKTREE="${KEEP_WORKTREE:-0}"

run() {
    if [[ "$DRY_RUN" == "1" ]]; then
        print -r -- "[dry-run] $*"
    else
        "$@"
    fi
}

die() {
    print -r -- "ERROR: $*" >&2
    exit 1
}

# Ensure we're in a git repo
git rev-parse --show-toplevel >/dev/null 2>&1 || die "Not inside a git repository."

TOP="$(git rev-parse --show-toplevel)"
cd "$TOP"

[[ -f .gitmodules ]] || die "No .gitmodules found at repo root ($TOP). Nothing to convert."

# Safety: do not proceed if parent repo has unstaged/staged changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    die "Parent repo has uncommitted changes. Commit or stash them first, then rerun."
fi

# Collect submodule names and paths from .gitmodules:
# lines like: "<name>\t<path>"
typeset -a MODS
MODS=("${(@f)$(git config -f .gitmodules --get-regexp '^submodule\..*\.path$' \
  | sed -E 's/^submodule\.([^.]*)\.path[[:space:]]+/\1\t/' \
  | awk 'NF==2{print}')}")
(( ${#MODS} > 0 )) || die ".gitmodules exists but contains no submodule.*.path entries."

# Sort by path depth (deepest-first) to avoid nested path issues.
typeset -a MODS_SORTED
MODS_SORTED=("${(@f)$(print -r -- "${(j:\n:)MODS}" \
  | awk -F'\t' '{p=$2; n=gsub(/\//,"/",p); print n "\t" length($2) "\t" $0}' \
  | sort -nr -k1,1 -k2,2 \
  | cut -f3-)}")

detect_default_branch() {
    local url="$1"
    git ls-remote --symref "$url" HEAD 2>/dev/null \
        | awk '/^ref: refs\/heads\// {sub("refs/heads/","",$2); print $2; exit}'
}

print -r -- "Repository: $TOP"
print -r -- "Found ${#MODS_SORTED} submodule(s) in .gitmodules"
print -r -- "SQUASH=$SQUASH DRY_RUN=$DRY_RUN KEEP_WORKTREE=$KEEP_WORKTREE"
print -r -- ""

for entry in "${MODS_SORTED[@]}"; do
    local name path url branch
    name="${entry%%$'\t'*}"
    path="${entry#*$'\t'}"

    url="$(git config -f .gitmodules --get "submodule.${name}.url" 2>/dev/null || true)"
    [[ -n "$url" ]] || die "Missing url for submodule '$name' (path '$path') in .gitmodules."

    # If .gitmodules specifies a branch, use it; else detect default; else fallback to main then master.
    branch="$(git config -f .gitmodules --get "submodule.${name}.branch" 2>/dev/null || true)"
    if [[ -z "$branch" ]]; then
        branch="$(detect_default_branch "$url" || true)"
    fi
    [[ -n "$branch" ]] || branch="main"

    print -r -- "== Converting submodule =="
    print -r -- "name : $name"
    print -r -- "path : $path"
    print -r -- "url  : $url"
    print -r -- "ref  : $branch"
    print -r -- ""

    # 1) Deinit (removes per-submodule config association)
    run git submodule deinit -f -- "$path" || true

    # 2) Remove gitlink from index
    run git rm -f --cached -- "$path" || true

    # 3) Remove module gitdir metadata
    run rm -rf ".git/modules/$path" || true

    # 4) Optionally remove the worktree directory
    if [[ "$KEEP_WORKTREE" != "1" ]]; then
        run rm -rf "$path" || true
    fi

    # 5) Add subtree at same prefix
    # Try with branch; if fails and branch was main, try master.
    if [[ "$DRY_RUN" == "1" ]]; then
        if [[ "$SQUASH" == "1" ]]; then
            print -r -- "[dry-run] git subtree add --prefix=$path $url $branch --squash"
        else
            print -r -- "[dry-run] git subtree add --prefix=$path $url $branch"
        fi
    else
        set +e
        if [[ "$SQUASH" == "1" ]]; then
            git subtree add --prefix="$path" "$url" "$branch" --squash
            rc=$?
        else
            git subtree add --prefix="$path" "$url" "$branch"
            rc=$?
        fi
        set -e

        if [[ $rc -ne 0 && "$branch" == "main" ]]; then
            print -r -- "Subtree add failed with branch 'main'. Trying 'master'..."
            if [[ "$SQUASH" == "1" ]]; then
                git subtree add --prefix="$path" "$url" master --squash
            else
                git subtree add --prefix="$path" "$url" master
            fi
        elif [[ $rc -ne 0 ]]; then
            die "Subtree add failed for '$path' from '$url' ref '$branch'."
        fi
    fi

    print -r -- ""
done

# After conversion, .gitmodules entries are no longer needed.
# Remove .gitmodules if it has no remaining submodule.* keys.
if git config -f .gitmodules --get-regexp '^submodule\.' >/dev/null 2>&1; then
    print -r -- "Note: .gitmodules still has submodule entries. Leaving it in place."
else
    print -r -- "Removing empty .gitmodules ..."
    run rm -f .gitmodules
    run git add -A
fi

print -r -- ""
print -r -- "Conversion complete."
print -r -- "Next steps:"
print -r -- "  git status"
print -r -- "  git commit -m \"Convert submodules to subtrees\""
print -r -- "  git push"

# vim: set ft=zsh ts=8 sw=4 sts=4 tw=100

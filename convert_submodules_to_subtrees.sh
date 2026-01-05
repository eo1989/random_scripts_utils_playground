#!/usr/bin/env bash
set -euo pipefail

# Converts all git submodules (from .gitmodules) into git subtrees at the same paths.
# Default behavior: uses --squash and detects remote default branch via ls-remote.
#
# Usage:
#   ./convert_submodules_to_subtrees.sh
#
# Optional env vars:
#   SQUASH=1|0        (default 1)
#   DRY_RUN=1|0       (default 0)
#   KEEP_WORKTREE=1|0 (default 0)  # if 1, does not rm -rf the path after git rm --cached (rarely useful)

SQUASH="${SQUASH:-1}"
DRY_RUN="${DRY_RUN:-0}"
KEEP_WORKTREE="${KEEP_WORKTREE:-0}"

run() {
    if [[ "$DRY_RUN" == "1" ]]; then
        printf '[dry-run] %q ' "$@"
        printf '\n'
    else
        "$@"
    fi
}

die() {
    echo "ERROR: $*" >&2
    exit 1
}

# Ensure we're in a git repo root-ish
git rev-parse --show-toplevel >/dev/null 2>&1 || die "Not inside a git repo"

TOP="$(git rev-parse --show-toplevel)"
cd "$TOP"

if [[ ! -f .gitmodules ]]; then
    die "No .gitmodules fouond at repo root ($TOP). Nothing to convert."
fi

# Safety: do not proceed if parent repo has unstaged/staged changes (subtree add is noisy)
if ! git diff --quiet || ! git diff --cached --quiet; then
    die "Parent repo has uncommitted changes. Commit or stash them first, then rerun."
fi

# Collect submodule names and paths from .gitmodules
# Output lines like: "<name>\t<path>"
mapfile -t MODS < <(
    git config -f .gitmodules --get-regexp '^submodule\..*\.path$' |
        sed -E 's/^submodule\.([^.]*)\.path[[:space:]]+/\1\t/' |
        awk 'NF==2{print}'
)

if [[ ${#MODS[@]} -eq 0 ]]; then
    die ".gitmodules exists but contains no submodule.*.path entries."
fi

# Sort by path depth (deepest-first) to avoid nested path issues.
# We sort by number of slashes descending, then by length descending.
mapfile -t MODS_SORTED < <(
    printf '%s\n' "${MODS[@]}" |
        awk -F'\t' '{path=$2; n=gsub(/\//,"/",path); print n "\t" length($2) "\t" $0}' |
        sort -nr -k1,1 -k2,2 |
        cut -f3-
)

detect_default_branch() {
    # Best-effort default branch detection using remote HEAD symref
    # Prints branch name (without refs/heads/) or empty on failure.
    local url="$1"
    git ls-remote --symref "$url" HEAD 2>/dev/null |
        awk '/^ref: refs\/heads\// {sub("refs/heads/","",$2); print $2; exit}'
}

subtree_add_cmd() {
    local prefix="$1"
    local url="$2"
    local branch="$3"
    if [[ "$SQUASH" == "1" ]]; then
        echo git subtree add --prefix="$prefix" "$url" "$branch" --squash
    else
        echo git subtree add --prefix="$prefix" "$url" "$branch"
    fi
}

echo "Repository: $TOP"
echo "Found ${#MODS_SORTED[@]} submodule(s) in .gitmodules"
echo "SQUASH=$SQUASH DRY_RUN=$DRY_RUN KEEP_WORKTREE=$KEEP_WORKTREE"
echo

for entry in "${MODS_SORTED[@]}"; do
    name="$(awk -F'\t' '{print $1}' <<<"$entry")"
    path="$(awk -F'\t' '{print $2}' <<<"$entry")"

    url="$(git config -f .gitmodules --get "submodule.${name}.url" || true)"
    if [[ -z "$url" ]]; then
        die "Missing url for submodule '$name' (path '$path') in .gitmodules."
    fi

    # If .gitmodules specifies a branch, use it; else detect default
    branch="$(git config -f .gitmodules --get "submodule.${name}.branch" || true)"
    if [[ -z "$branch" ]]; then
        branch="$(detect_default_branch "$url" || true)"
    fi
    if [[ -z "$branch" ]]; then
        # Fallback heuristics
        branch="main"
        # We'll later try master if main fails.
    fi

    echo "== Converting submodule =="
    echo "name : $name"
    echo "path : $path"
    echo "url  : $url"
    echo "ref  : $branch"
    echo

    # 1) Deinit (removes per-submodule config)
    run git submodule deinit -f -- "$path" || true

    # 2) Remove gitlink from index
    run git rm -f --cached -- "$path" || true

    # 3) Remove module gitdir metadata
    # Note: modules are stored under .git/modules/<path> preserving path components
    run rm -rf ".git/modules/$path" || true

    # 4) Optionally remove the worktree directory (recommended, avoids collisions)
    if [[ "$KEEP_WORKTREE" != "1" ]]; then
        run rm -rf "$path" || true
    fi

    # 5) Add subtree at same prefix
    # Try with detected/fallback branch; if fails and branch was main, try master.
    set +e
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "[dry-run] $(subtree_add_cmd "$path" "$url" "$branch")"
        rc=0
    else
        if [[ "$SQUASH" == "1" ]]; then
            git subtree add --prefix="$path" "$url" "$branch" --squash
            rc=$?
        else
            git subtree add --prefix="$path" "$url" "$branch"
            rc=$?
        fi
    fi
    set -e

    if [[ $rc -ne 0 && "$branch" == "main" ]]; then
        echo "Subtree add failed with branch 'main'. Trying 'master'..."
        if [[ "$DRY_RUN" == "1" ]]; then
            echo "[dry-run] $(subtree_add_cmd "$path" "$url" "master")"
        else
            if [[ "$SQUASH" == "1" ]]; then
                git subtree add --prefix="$path" "$url" master --squash
            else
                git subtree add --prefix="$path" "$url" master
            fi
        fi
    elif [[ $rc -ne 0 ]]; then
        die "Subtree add failed for '$path' from '$url' ref '$branch'."
    fi

    echo
done

# After conversion, .gitmodules entries are no longer needed.
# Remove .gitmodules if it has no remaining submodule.* keys.
if git config -f .gitmodules --get-regexp '^submodule\.' >/dev/null 2>&1; then
    echo "Note: .gitmodules still has submodule entries. Leaving it in place."
else
    echo "Removing empty .gitmodules ..."
    run rm -f .gitmodules
    run git add -A
fi

echo
echo "Conversion complete."
echo "Next steps:"
echo "  git status"
echo "  git commit -m \"Convert submodules to subtrees\""
echo "  git push"

# vim: set ft=sh ts=8 sw=4 sts=4 tw=100 et ai smarttab

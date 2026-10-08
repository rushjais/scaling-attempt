#!/bin/sh
# Fetch Pelican at the pinned commit into $1 (default: ./upstream). Not vendored in this repo.
set -e
. "$(dirname "$0")/PIN"
dest="${1:-$(dirname "$0")/upstream}"
rm -rf "$dest"
git clone -q --filter=blob:none "$repo" "$dest"
git -C "$dest" checkout -q "$commit"
echo "pelican @ $(git -C "$dest" log -1 --format='%h %cs') -> $dest"

#!/bin/sh
# Build local tools from the exact sources used in the recorded experiment.
set -eu
cd "$(dirname "$0")/../../.."
mkdir -p .benchmark-tools
git diff --quiet 4d462c8f7883f4e08d3d0e151de0374a6150ea22 -- src weights Makefile release.json || {
    echo "Target engine differs from the measured revision" >&2; exit 1;
}
clone_at() {
    url=$1
    directory=$2
    revision=$3
    if [ ! -d "$directory/.git" ]; then
        git clone "$url" "$directory"
        git -C "$directory" checkout --detach "$revision"
    fi
    actual=$(git -C "$directory" rev-parse HEAD)
    [ "$actual" = "$revision" ] || { echo "Wrong revision in $directory" >&2; exit 1; }
    [ -z "$(git -C "$directory" status --porcelain --untracked-files=no)" ] || {
        echo "Tracked source modifications in $directory" >&2; exit 1;
    }
}
clone_at https://github.com/official-stockfish/Stockfish.git .benchmark-tools/Stockfish 03e27488f3d21d8ff4dbf3065603afa21dbd0ef3
clone_at https://github.com/Disservin/fastchess.git .benchmark-tools/fastchess ebfd64cb7fac80d4822c50b07dca4fe934779d21
clone_at https://github.com/mhouppin/stash-bot.git .benchmark-tools/Stash 7d17ff80eb53b9d4808fd285c7439e641f1c5a3b
clone_at https://github.com/Warpten/Fruit-2.1.git .benchmark-tools/Fruit-2.1 09627df3835f205c92ece013219c7a99ac4a023a

python3 -m venv .benchmark-tools/venv
.benchmark-tools/venv/bin/python -m pip install -r requirements-dev.txt -c benchmarks/chromatique-v4/data/python-constraints.txt
make JOBS=4 GIT_SHA=4d462c8f GIT_DATE=20261019
if [ "$(uname -s)" = Darwin ]; then
    make -C .benchmark-tools/Stockfish/src -j4 build ARCH=apple-silicon COMP=clang EXE=stockfish-17.1
else
    make -C .benchmark-tools/Stockfish/src -j4 build ARCH=native COMP=gcc EXE=stockfish-17.1
fi
make -C .benchmark-tools/fastchess -j4 CXX=c++
make -C .benchmark-tools/Stash/src -j4 CC=cc
make -C .benchmark-tools/Fruit-2.1/src -j4 CXX=c++ LDFLAGS=-lm
curl --fail --location --output .benchmark-tools/8moves_v3.pgn.zip \
    https://raw.githubusercontent.com/official-stockfish/books/a804a97e709f40aa75a00f9d19e84915b7a3a45c/8moves_v3.pgn.zip
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/prepare_openings.py
.benchmark-tools/venv/bin/python -m unittest discover -s tests -v
.benchmark-tools/venv/bin/python -m unittest discover -s benchmarks/chromatique-v4/scripts -p 'test_*.py' -v

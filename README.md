# Chromatique

**Chromatique: an imaginative chess engine currently embracing romantic chess--tactics, sacrifices, and zero positional play.**

The project chases initiative, forcing lines, and the kind of combinations that make a position worth remembering. Quiet positional refinement is work for future versions.

This is **pure v4**, packaged as a standalone **UCI chess engine**. Its own 820 → 512 → 32 neural network supplies the static evaluation and a learned policy head guides move ordering. The search and move-generation core is derived from **Stockfish 19**. Chromatique does not use Stockfish's NNUE evaluation, a classical evaluation blend, or a fixed material score.

## Play

Download and extract the [latest release](https://github.com/lusolitaire-dot/Chromatique/releases/latest). The first binary package is for **Apple Silicon macOS**. Keep its folders together, then add `bin/chromatique-v4` as a UCI engine in your chess GUI. The executable finds its bundled weights even when the GUI starts it from another directory.

From a terminal:

```sh
./bin/chromatique-v4
```

Example UCI conversation:

```text
uci
isready
ucinewgame
position startpos moves e2e4 e7e5
go movetime 3000
```

The engine replies with analysis and `bestmove`. Send `stop` to interrupt a search and `quit` to exit. Send the complete move history when setting a position so repetition and other state are preserved.

The usual UCI controls include `Threads`, `Hash`, `MultiPV`, and `Ponder`. `ChromatiqueModel` selects another compatible CHROMA3 model. The bundled v4 model is selected automatically; `CHROMATIQUE_NATIVE_MODEL` can override it before startup. The learned policy is enabled by default. This release uses no opening book.

## Build from source

You need GNU Make and a C++17 compiler: Clang on macOS or GCC/Clang on Linux. Python is not needed to run or build the engine.

```sh
git clone https://github.com/lusolitaire-dot/Chromatique.git
cd Chromatique
make -j2
./bin/chromatique-v4
```

The build detects the local CPU. For a portable Linux x86-64 binary:

```sh
make ARCH=x86-64 COMP=gcc
```

The complete modified C++ source is in `src/`. Upstream attribution, license, pinned commit, and the complete source changes are included in [NOTICE](NOTICE), [AUTHORS](AUTHORS), and [docs/stockfish-changes.patch](docs/stockfish-changes.patch).

## Network and verification

`weights/chromatique-v4.json.gz` contains the editable, complete model as gzip-compressed JSON; decompress it before editing. `weights/chromatique-v4.native` is its lossless float32 runtime export. Both are the unchanged pure-v4 release artifacts; their SHA-256 checksums are recorded in [release.json](release.json). No pruning, quantization, model blending, or replacement network is used.

To regenerate the runtime model or run the release checks:

```sh
python3 -m pip install -r requirements-dev.txt
python3 tools/export_native.py weights/chromatique-v4.json.gz /tmp/chromatique-v4.native
python3 -m unittest discover -s tests -v
```

The checks cover byte-identical model export, 120 positions of Python/native feature, value and legal-move-policy parity, UCI search and interruption, special-move legality, relocation, and failure when weights are missing. The feature reference and optional PyTorch network definition are in `python/`; those modules are not part of runtime inference.

V4 scored 92/128 complete published solutions and 105/128 correct first moves in the latest local development benchmark at 0.5 seconds per solver move. The puzzles were rated 2202–3011. This is a reused development panel, not an Elo estimate or a final holdout result. The engine's style and overall playing strength remain experimental.

See the [v4 benchmark](benchmarks/chromatique-v4/README.md) for paired UCI matches, confidence intervals, PGNs, style observations, and calibration limits.

## License

Chromatique is distributed under **GPL-3.0-or-later**, including this Stockfish-derived engine and the bundled Chromatique model. See [LICENSE](LICENSE). The original Stockfish copyright notices and authors are retained; the bundled `src/incbin` helper has its own retained [UNLICENCE](src/incbin/UNLICENCE).

If you distribute a binary, preserve the license and provide its complete corresponding source, including the model and build files. See [Stockfish's distribution terms](https://stockfishchess.org/about/).

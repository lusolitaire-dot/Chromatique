# Chromatique

**Chromatique: an imaginative chess engine currently embracing romantic chess--tactics, sacrifices, and zero positional play.**

The project chases initiative, forcing lines, and the kind of combinations that make a position worth remembering. A well-rounded Chromatique remains the longer-term goal; the project is still in development.

The current default is the **v4 pilot checkpoint**, an experimental continuation of pure v4, packaged as a standalone **UCI chess engine**. Its own 820 → 512 → 32 neural network supplies the static evaluation; its learned policy head orders the initial root moves. The search and move-generation core is derived from **Stockfish 19**. Chromatique does not use Stockfish's NNUE evaluation, a classical evaluation blend, or a fixed material score. The original pure-v4 model is preserved alongside the pilot.

The retained pilot scored **25 wins, 14 draws and 21 losses** against pure v4 in 60 development games, with 20,000 nodes per move on both sides and reversed colours over 30 openings. Its 53.3% score has a descriptive opening-pair bootstrap 95% interval of 41.7–65.0%. This is a small observed edge, not an established strength or Elo improvement. See the [checkpoint notes and games](docs/v4-pilot/README.md).

## Play

Build the current checkout using the instructions below to use the updated pilot. Existing [tagged binary releases](https://github.com/lusolitaire-dot/Chromatique/releases) retain their original pure-v4 weights; they are not silently replaced by this repository update. The standalone executable is `bin/chromatique-v4`; add it as a UCI engine in your chess GUI and keep its `bin/` and `weights/` folders together. It finds the bundled default model even when the GUI starts it from another directory.

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

The usual UCI controls include `Threads`, `Hash`, `MultiPV`, and `Ponder`. `ChromatiqueModel` selects another compatible CHROMA3 model. The bundled v4 pilot is selected automatically; `CHROMATIQUE_NATIVE_MODEL` can override it before startup. To run the original pure v4, select the absolute path to `weights/pure-v4.native` with `ChromatiqueModel`, or launch from the repository root with:

```sh
CHROMATIQUE_NATIVE_MODEL="$PWD/weights/pure-v4.native" ./bin/chromatique-v4
```

The learned policy is enabled by default. Neither bundled model uses an opening book.

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

`weights/chromatique-v4.json.gz` contains the editable, complete pilot model as gzip-compressed JSON; decompress it before editing. `weights/chromatique-v4.native` is its lossless float32 runtime export. The original pure-v4 artifacts are retained byte-for-byte as `weights/pure-v4.json.gz` and `weights/pure-v4.native`. All four SHA-256 checksums are recorded in [release.json](release.json). The network architecture, shared features, C++ search and inference remain unchanged. This update publishes trained policy/value parameters without pruning, quantization or runtime model blending.

To regenerate the runtime model or run the release checks:

```sh
python3 -m pip install -r requirements-dev.txt
python3 tools/export_native.py weights/chromatique-v4.json.gz /tmp/chromatique-v4.native
python3 -m unittest discover -s tests -v
```

The checks cover byte-identical export for both bundled models, 120 positions of Python/native feature, value and legal-move-policy parity per model, UCI model switching, search and interruption, special-move legality, relocation, and failure when weights are missing. The feature reference and optional PyTorch network definition are in `python/`; those modules are not part of runtime inference.

On a separate 128-puzzle development panel at 100,000 nodes per solver decision, pure v4 scored 95 complete lines and the retained pilot scored 97. The pilot's larger fresh-SF19 score gain was measured against an intermediate jointly fine-tuned checkpoint, not against pure v4. These comparisons do not establish an overall ranking against v10 or the E4_Pb hybrid. The engine's style and playing strength remain experimental.

See the [original pure-v4 benchmark](benchmarks/chromatique-v4/README.md) for paired UCI matches, confidence intervals, PGNs, style observations, and calibration limits. Those historical benchmark results belong to the original model; they are not measurements of the new pilot.

## License

Chromatique is distributed under **GPL-3.0-or-later**, including this Stockfish-derived engine and the bundled Chromatique model. See [LICENSE](LICENSE). The original Stockfish copyright notices and authors are retained; the bundled `src/incbin` helper has its own retained [UNLICENCE](src/incbin/UNLICENCE).

If you distribute a binary, preserve the license and provide its complete corresponding source, including the model and build files. See [Stockfish's distribution terms](https://stockfishchess.org/about/).

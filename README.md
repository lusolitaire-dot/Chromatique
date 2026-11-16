# Chromatique

**Chromatique: an imaginative chess engine currently embracing romantic chess--tactics, sacrifices, and zero positional play.**

This is **v4.1.0**, packaged as a standalone **UCI chess engine**. Its fully neural 820 → 512 → 32 value branch and a learned policy head guide evaluation and move ordering; the value and policy branches use independently learned 512-neuron encoders. The search and move-generation core is derived from **Stockfish 19**. Chromatique does not use Stockfish's NNUE evaluation, a classical evaluation blend, or a fixed material score.

## Play

Download and extract the [latest release](https://github.com/lusolitaire-dot/Chromatique/releases/latest). The binary package is for **Apple Silicon macOS**. Keep its folders together, then add `bin/chromatique-v4.1.0` as a UCI engine in your chess GUI. The executable finds its bundled weights even when the GUI starts it from another directory.

From a terminal:

```sh
./bin/chromatique-v4.1.0
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

The usual UCI controls include `Threads`, `Hash`, `MultiPV`, and `Ponder`. `ChromatiqueModel` selects another compatible CHROMA3 or CHROMA4 model. The bundled v4.1.0 model is selected automatically; `CHROMATIQUE_NATIVE_MODEL` can override it before startup. The learned policy is enabled by default. This release uses no opening book.

## Build from source

You need GNU Make and a C++17 compiler: Clang on macOS or GCC/Clang on Linux. Python is not needed to run or build the engine.

```sh
git clone https://github.com/lusolitaire-dot/Chromatique.git
cd Chromatique
git checkout v4.1.0
make -j2
./bin/chromatique-v4.1.0
```

The build detects the local CPU. For a portable Linux x86-64 binary:

```sh
make ARCH=x86-64 COMP=gcc
```

The complete modified C++ source is in `src/`. Upstream attribution, license, pinned commit, and the complete source changes are included in [NOTICE](NOTICE), [AUTHORS](AUTHORS), and [docs/stockfish-changes.patch](docs/stockfish-changes.patch).

## Network and verification

`weights/chromatique-v4.1.0.json.gz` contains the complete editable model as gzip-compressed JSON; decompress it before editing. `weights/chromatique-v4.1.0.native` is its lossless float32 runtime export. Their SHA-256 checksums are recorded in [release.json](release.json). No pruning, quantization, model blending, or Stockfish evaluator fallback is used.

To regenerate the runtime model or run the release checks:

```sh
python3 -m pip install -r requirements-dev.txt
python3 tools/export_native.py weights/chromatique-v4.1.0.json.gz /tmp/chromatique-v4.1.0.native
python3 -m unittest discover -s tests -v
```

The checks cover byte-identical model export, Python/native feature, value and legal-move-policy parity, UCI search and interruption, special-move legality, relocation, and failure when weights are missing. The feature reference and optional PyTorch network definition are in `python/`; those modules are not part of runtime inference.

This release does not establish an official Elo rating. Chromatique's style and practical strength should be evaluated by users on their own hardware and time controls.

## License

Chromatique is distributed under **GPL-3.0-or-later**, including this Stockfish-derived engine and the bundled Chromatique model. See [LICENSE](LICENSE). The original Stockfish copyright notices and authors are retained; the bundled `src/incbin` helper has its own retained [UNLICENCE](src/incbin/UNLICENCE).

If you distribute a binary, preserve the license and provide its complete corresponding source, including the model and build files. See [Stockfish's distribution terms](https://stockfishchess.org/about/).

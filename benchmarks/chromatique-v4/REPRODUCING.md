# Reproducing the benchmark

Run commands from the repository root. Use Python 3.14.7 with the existing
`requirements-dev.txt` pins and [package constraints](data/python-constraints.txt)
to reproduce the recorded analysis environment. The constraints also fix the
transitive `chess` library at 1.11.2; `python-chess==1.999` alone permits any 1.x
release. New matches on other Python/platform versions are fresh experiments
rather than byte-identical build reproductions.

## Verify the retained evidence

Install the repository's declared development requirements in a local venv,
or use the setup script below. Then run:

```sh
.benchmark-tools/venv/bin/python -m pip install -r requirements-dev.txt -c benchmarks/chromatique-v4/data/python-constraints.txt
.benchmark-tools/venv/bin/python -m unittest discover -s tests -v
.benchmark-tools/venv/bin/python -m unittest discover -s benchmarks/chromatique-v4/scripts -p 'test_*.py' -v
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/analyze.py benchmarks/chromatique-v4/pilot.json --output /tmp/chromatique-pilot-replayed.json
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/analyze.py benchmarks/chromatique-v4/pilot-refine.json --output /tmp/chromatique-refine-replayed.json
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/analyze.py benchmarks/chromatique-v4/schedule.json --output /tmp/chromatique-main-replayed.json
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/analyze.py benchmarks/chromatique-v4/anchor-schedule.json --output /tmp/chromatique-anchor-replayed.json
```

The PGN analysis needs python-chess and NumPy but does **not** start an engine.
It checks every recorded legal move, rules-terminal result, complete opening
history, time-control header, expected opponent, exact reversed-color pair
count, opening-file hash and PGN hash. It then recomputes W/D/L, all pair
scores and the reported uncertainty. Match failures remain part of W/D/L;
the termination table identifies them separately.

`results/summary.json` and `results/anchor-summary.json` are the machine-readable
fixed-schedule results. Compare the replayed JSON with those files. Pilot and
main estimates are separate. The ordinary 95% intervals are conditional on
this opening population, machine,
time control and engine configuration. The distribution-free intervals are
more conservative. None includes external rating-anchor uncertainty.

To recompute style summaries from the retained probe choices and judge data:

```sh
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/style.py benchmarks/chromatique-v4/schedule.json --central-match main-sf2400 --summarize-only
```

This rewrites the derived style-summary JSON only. It does not repeat judge
searches. Inspect `results/style-probes.jsonl` for every position, history,
selected move, search budget, judge score and principal variation. Mate
transitions have their own record and are excluded from centipawn-loss
comparisons. Style differences use one source position per opening pair.
The derived `game-style.csv` is stored with LF line endings in Git; a local
Python CSV writer can emit CRLF. Compare parsed rows for CSV regeneration
checks.
`results/style-positions.json` records the PGN, model, binary and script hashes
prepared immediately before probing, the source engine settings and the
actual judge options. Either existing style evidence file blocks a new probe
run before any output is written; use a fresh results directory to repeat it.

After the timed matches finish, inspect the predeclared examples with:

```sh
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/inspect_examples.py
```

The script uses two million Stockfish nodes per search. It selects the two
lowest-loss and the highest-loss target offer candidates from the original
probe estimates, without filtering source-game results. It preserves both
choices and complete source histories in JSON and an annotated PGN. These
PGN variations are analysis continuations, not new match results.

## Build the measured engines and tools

```sh
sh benchmarks/chromatique-v4/scripts/setup.sh
```

The setup script downloads source into ignored `.benchmark-tools/`, checks
exact revisions, installs only the repository's existing Python development
requirements, builds local binaries, downloads the checksum-pinned CC0
opening archive, verifies/regenerates the four original panels and the new
disjoint anchor panel, and runs the tests.
It does not change the system package manager or engine source. Network
access, GNU Make and a C/C++ compiler are required. The recorded Apple
Silicon build used Apple Clang 21. The complete setup passed in a fresh
checkout of `7d8c7dc`; [its receipt](results/setup-receipt.json) and
[compressed output](results/setup-output.txt.gz) retain the commands, source
revisions, installed versions, hashes and both passing test suites. The
Linux build path is supplied but was not run in this experiment. No binaries
or external source trees are distributed in this PR.

`data/environment.json` records all source revisions, model, binary and
Stockfish-network hashes, compiler commands and hardware. The target build
preserves its original embedded revision/date. The setup guard rejects
changes to the target source or weights relative to the measured revision.
Exact binary hashes can differ with compiler, linker, platform or build
metadata; retain new hashes with any new results.
On the measured host, the fresh target, model and all reference-engine
binaries matched the measured hashes; the fresh Fastchess binary differed.
Fastchess includes its compilation date in the CLI version information.
Both sets are retained in the receipts. No new matches were run with the
rebuilt tools.

The measured long-clock runner uses the built-in macOS `caffeinate` utility
for an idle-sleep assertion scoped to its lifetime. Its verified attachment
time and execution limits are recorded in [the notes](EXECUTION-NOTES.md).

Fruit 2.1 is a source-mirror build used only in the selection pilot. The
original distributor archive returned HTTP 404, so identity with its original
archive was not established. The pinned mirror identifies itself as Fruit
2.1. Stash 15.3 comes from its author's exact release tag. Their historical
public ratings and the reference Stockfish calibration are described in
[SOURCES.md](SOURCES.md); they are not ratings awarded by these matches.

## Repeat matches without overwriting the record

```sh
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/run_matches.py benchmarks/chromatique-v4/schedule.json --results-dir .benchmark-tools/reproduction-results
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/run_matches.py benchmarks/chromatique-v4/anchor-schedule.json --results-dir .benchmark-tools/reproduction-results
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/analyze.py benchmarks/chromatique-v4/schedule.json --results-dir .benchmark-tools/reproduction-results --output .benchmark-tools/reproduction-results/summary.json
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/analyze.py benchmarks/chromatique-v4/anchor-schedule.json --results-dir .benchmark-tools/reproduction-results --output .benchmark-tools/reproduction-results/anchor-summary.json
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/style.py benchmarks/chromatique-v4/schedule.json --results-dir .benchmark-tools/reproduction-results --central-match main-sf2400
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/inspect_examples.py --results-dir .benchmark-tools/reproduction-results
```

The original schedule contains 2,300 games. The separately predeclared
validations add 200 games each against Stockfish's 2400 setting and Stash
15.3 at **120+1**, the historical clock of the fit inherited by Stockfish.
See [the extensions and external-rating limits](CALIBRATION-VALIDATION.md).
`5+0.05` means **five seconds initially plus
50 milliseconds per move**, not five seconds per move. The slower check is
30 seconds initially plus 300 milliseconds per move. It remains below the
120+1 setting used in Stockfish's published calibration. Allow substantial
wall time and keep the host's load stable; do not run parallel builds or
engine judging during the timed matches. Six games are concurrent, each
engine uses one search thread, and fresh processes start each game.

Repeated games need not reproduce identical moves: the reference deliberately
randomizes weakened play, and wall-clock searches depend on scheduling.
Reproducibility here means exact inputs, settings, complete evidence and
rerunnable calculations, not a promise of identical future outcomes.

Every run writes a receipt with the command, input hashes, process IDs,
timestamps, exit code and PGN checksum, plus the full Fastchess log and its
recovery state. An existing interrupted or changed run is rejected. Inspect
the actual live process and state before recovering a run; never start a
replacement merely because an observation timed out. A recovered run must
retain all earlier games and pass exact pair/count validation before it can
be reported as the fixed sample.

Fastchess reports many bestmove/PV mismatch warnings from weakened Stockfish:
its selected weaker move can differ from its strongest reported principal
variation. These warnings are retained. Legality comes from independent PGN
replay. Score-based resign/draw adjudication is disabled; the two evaluators
have different score meanings. Administrative 300-move draws, clock losses,
crashes and illegal moves must be counted and disclosed from the results.

After the new scheduled matches finish, archive their output directory:

```sh
.benchmark-tools/venv/bin/python benchmarks/chromatique-v4/scripts/archive_logs.py --results-dir .benchmark-tools/reproduction-results
```

The script verifies a byte-exact decompression roundtrip and records raw and
compressed SHA-256 hashes in the selected directory's `log-archives.json`. Raw logs and states
remain on disk and are ignored by Git; their lossless `.gz` copies are the
review artifacts. PGNs remain ordinary, uncompressed `.pgn` files. An archive-only
published checkout has no raw inputs; the script rejects that case before
writing a manifest, preserving the retained provenance. Omitting `--results-dir`
is appropriate only when archiving raw runs in the original `results/` directory.
When only some raw inputs are present, retained archive records are validated
and preserved while new records are added. Corrupt or changed retained evidence
is rejected, and the manifest is replaced atomically after validation succeeds.

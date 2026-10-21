# Chromatique v4 benchmark protocol

Target: unmodified `4d462c8f7883f4e08d3d0e151de0374a6150ea22`, bundled v4
weights, learned policy on, full strength. This protocol was written before
pilot or measurement games. The final schedule will be frozen separately
after the pilot, before measurement games.

## Question and scope

Estimate match strength on this machine at specified time controls, and test
observable implications of the advertised romantic style. Puzzle ratings,
Stockfish ancestry and inherited UCI options do not establish playing Elo.
Do not describe a relative match rating as a FIDE, Lichess or calibrated CCRL
rating. No engine source, weights or playing parameters will be tuned.

## Design

1. Build the pinned target and Stockfish 17.1; retain source revisions,
   compiler, platform, binary/model checksums and UCI settings. Run the
   existing release tests before matches. Use only the repository's existing
   Python development dependencies; Fastchess and reference engines are local
   benchmark tools, not runtime dependencies of Chromatique.
2. Use a seeded sample without replacement of distinct final positions from
   the CC0 Stockfish `8moves_v3.pgn` book. Every opening is played twice with
   colors reversed. Keep the pilot, main and slower panels disjoint. Preserve
   the opening moves and history in the PGNs. No target-dependent filtering.
3. Pilot: small matches against a grid of Stockfish 17.1 `UCI_Elo` settings,
   solely to avoid floor/ceiling scores. Pilot data is excluded from all
   confirmatory estimates. Select a central level and its two neighboring
   levels; if a grid endpoint saturates, extend the pilot before freezing.
4. Main: **400 games (200 opening pairs) per selected reference**, fixed in
   advance, at **5 seconds + 0.05 seconds/move**. No significance or precision
   stopping. A full-strength, independently authored UCI engine with a
   documented public rating is added if a suitable build is available.
5. Calibration checks: fixed matches between neighboring limited Stockfish
   levels test whether their nominal spacing holds locally. A separate
   **100-game (50-pair), 30+0.3** target match against the central reference
   checks time-control sensitivity. This smaller sensitivity panel has wider
   uncertainty and cannot by itself calibrate an absolute rating.
6. One engine thread, 32 MiB hash where supported, pondering off, no opening
   book in the engines and no tablebases. Bound total game concurrency to six
   on the 15-logical-CPU host. Do not run builds or analysis during timed
   measurements. Record exceptional load or interruptions. Clear game state
   with fresh engine processes for each final-schedule game (`restart=on`),
   including `ucinewgame`; preserve genuine crashes, illegal moves and time
   losses. Pilot games reused engine processes; they are selection data only.
7. Use Fastchess's rules draws (including repetition and fifty-move rule).
   Disable score-based resign/draw adjudication: the two evaluators do not
   share a centipawn scale. A 300-move maximum is an explicit administrative
   draw; count and disclose every such termination. No manual game exclusions
   or result-dependent restarts. Incomplete runs are not complete samples.

## Statistical analysis

For each reference, report W/D/L, score, color split, opening-pair
pentanomial counts and logistic Elo difference
`400 * log10(score / (1 - score))`. The independent sampling unit is the
opening pair, not each game. A pair's normalized score is in
`{0, 0.25, 0.5, 0.75, 1}`. Use the unbiased sample variance of pair scores to
form a 95% normal interval for mean score, then transform its endpoints to
Elo. Report a seeded 20,000-resample pair bootstrap as a sensitivity check;
neither interval includes systematic calibration error. Boundary estimates
are unbounded, not artificially clipped. For degenerate empirical samples,
report a conservative bounded-score Hoeffding interval instead of zero
uncertainty. Also publish that distribution-free interval for every match.

These are individual, approximate 95% intervals, not simultaneous coverage
across opponents. Selection uses pilot games only. A nominal-reference-plus-
delta number is at most a local **Stockfish-setting equivalent**; bridge
matches and slow matches can reveal disagreement, not erase it. Do not pool
nominal anchors as if they were independently known population ratings.

## Style analysis, separate from strength

Use the fixed main PGNs for descriptive move/game rates: checks, captures,
quiet moves, queen trades, game length and material deficits (pawn=1,
knight/bishop=3, rook=5, queen=9). Book plies are excluded. Compare both
participants within reversed-color opening pairs; game length, forced
responses and opponent strength remain confounders. Material loss alone is
not evidence of an intentional or sound sacrifice.

Add a fixed, deterministic sample of main-game positions (independent of
the move chosen) for a common-position comparison. For each central-match
opening pair, SHA-256 of its UCI opening chooses one game. Rotate the candidate
plies 24, 32 and 40 using the next hash byte, adding one ply when the target
plays Black. Take the first candidate that exists, is not check, has at least
three legal moves and is not already a claimable draw. Record exclusions.
Ask Chromatique and the
central, approximately strength-matched reference for moves under equal
**0.25 seconds per move**. A full-strength Stockfish 17.1 analysis uses
**200,000 nodes per search**, once unrestricted and once restricted to each
distinct selected move, with fresh game/hash state. Its evaluator is separate
from Chromatique's but shares the reference engine's evaluation family.
This judge scores the
choices. Record forcing-move rate, quiet-move rate, material offered to legal
captures, and analysis loss against the same judge. Publish all positions,
moves, scores and budgets. These are operational proxies, not a validated
classifier of romantic chess. Inspect a few mechanically selected examples
and distinguish sound initiative from a blunder. Do not claim that a neural
evaluator lacks positional knowledge merely because no hand-written material
term exists.

The material-offer proxy is net material conceded if the opponent legally
captures a non-pawn, allowing the best immediate legal material recapture on
that square. It excludes an equal queen trade. A concession of at least one
pawn-equivalent is a candidate; judge loss at most 50 centipawns is a separate
low-loss label. The judge's unrestricted and forced searches allocate work
differently, so negative estimated losses are retained in raw data. Game
length and both-queens-absent-by-move-40 are descriptive game context.
Style comparisons are exploratory and their intervals are not corrected for
multiple comparisons. A degenerate bootstrap is marked unavailable.
Mate-valued searches are recorded as mate transitions and excluded from
ordinary centipawn-loss thresholds and medians.

For example inspection, rejudge the two lowest nonnegative estimated-loss
target offer candidates and the highest-loss candidate, ranking negative
estimates as zero, breaking ties by probe index and removing duplicates.
Exclude mate-valued ordinary losses.
There is no source-game-outcome filter. Use 2,000,000 judge nodes per search
and publish both engines' choices, full source histories and analysis PVs.
These are selected examples, not a representative sacrifice success rate.

## Deliverables and acceptance

- Reproducible setup/run/analysis commands; pinned source and input hashes.
- Complete PGNs and logs for pilot, fixed main matches and calibration checks.
- Independent PGN replay/legality and exact schedule/pair validation.
- Machine-readable results; hand-checkable statistics; focused analysis tests.
- Source-backed methodology, limitations and a plain-English strength/style
  assessment, with explicit external-calibration limits.
- GitHub PR containing those artifacts, verified open and left for review.

Implementation order: environment/release checks; opening preparation and
pilot runner; freeze schedule; run fixed matches; validate PGNs and paired
statistics; style probes; review/reproduce artifacts; open and verify PR.

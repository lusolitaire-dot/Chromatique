# Chromatique v4: playing strength and style

**All 2,700 fixed-schedule games and the 200-position style panel are complete.
All 2,868 match games, including 168 excluded selection games, passed independent
legal replay.** PGNs, probe records and run receipts are retained in
[`results/`](results/).

## Measured strength

At **120 seconds + 1 second/move**, Chromatique scored **85.50% against
Stash 15.3**: **+308 relative logistic Elo, 95% interval +255 to +377**.
Adding Stash’s published 2174 gives a conditional point near **2480**. At
**5+0.05**, it scored **67.00%**, or **+123 [+90, +158]**, giving an illustrative
point near **2300**. These are clock-specific measurements on this host;
external rating transfer remains uncertain. A single calibrated CCRL, FIDE
or online rating is not established.

| Match, first engine’s perspective | Clock | Games | W/D/L | Score | Relative logistic Elo, 95% interval |
|---|---|---:|---:|---:|---:|
| Chromatique vs SF17.1 E2200 | 5+0.05 | 400 | 280/18/102 | 72.25% | +166 [+131, +205] |
| Chromatique vs SF17.1 E2400 | 5+0.05 | 400 | 222/17/161 | 57.63% | +53 [+20, +88] |
| Chromatique vs SF17.1 E2600 | 5+0.05 | 400 | 132/28/240 | 36.50% | -96 [-131, -64] |
| Chromatique vs Stash 15.3 | 5+0.05 | 400 | 246/44/110 | 67.00% | +123 [+90, +158] |
| SF17.1 E2200 vs E2400 | 5+0.05 | 200 | 56/17/127 | 32.25% | -129 [-183, -81] |
| SF17.1 E2400 vs E2600 | 5+0.05 | 200 | 38/23/139 | 24.75% | -193 [-242, -151] |
| Stash 15.3 vs SF17.1 E2400 | 5+0.05 | 200 | 87/14/99 | 47.00% | -21 [-68, +25] |
| Chromatique vs SF17.1 E2400 | 30+0.3 | 100 | 76/4/20 | 78.00% | +220 [+147, +315] |
| Chromatique vs SF17.1 E2400 | 120+1 | 200 | 171/5/24 | 86.75% | +326 [+266, +408] |
| Chromatique vs Stash 15.3 | 120+1 | 200 | 161/20/19 | 85.50% | +308 [+255, +377] |

Clock values are initial seconds plus seconds per move. Intervals above use
complete opening pairs and the normal approximation.
[Original results](results/summary.json) and
[long-clock results](results/anchor-summary.json) also retain the seeded pair
bootstrap, conservative Hoeffding intervals, pair variances and exact hashes.
The Stash–SF2400 bridge was nearly even (47%–53%), so the printed Stockfish
setting does not independently establish the opponent’s local external rating.
The longer-clock results were stronger than the fast results against the same
opponents. Clocks and disjoint opening panels both differ, so this sensitivity
comparison does not isolate the causal effect of thinking time.

Each long-clock comparison has 100 complete opening pairs. Its alternative
intervals show the practical limits of precision:

| 120+1 opponent | Pair bootstrap 95% Elo | Conservative Hoeffding 95% Elo |
|---|---:|---:|
| SF17.1 E2400 | [+266, +402] | [+174, +∞] |
| Stash 15.3 | [+255, +372] | [+163, +813] |

Every recorded move passed legal replay and every expected opening appeared
exactly twice with colors reversed. The fixed schedule retains one Stockfish
time-forfeit win for Chromatique, three Stash disconnect wins for Chromatique
(two fast, one long), and one Stash disconnect loss in the bridge. Their
underlying causes are undiagnosed. No game reached the 300-move administrative
cap; the longest was 245 moves.

| Match | Pair counts: LL, LD, DD/WL, WD, WW | White W/D/L | Black W/D/L |
|---|---|---:|---:|
| Chromatique vs SF17.1 E2200 (5+0.05) | 15, 1, 72, 15, 97 | 135/7/58 | 145/11/44 |
| Chromatique vs SF17.1 E2400 (5+0.05) | 32, 6, 92, 9, 61 | 114/7/79 | 108/10/82 |
| Chromatique vs SF17.1 E2600 (5+0.05) | 70, 17, 84, 9, 20 | 67/14/119 | 65/14/121 |
| Chromatique vs Stash 15.3 (5+0.05) | 15, 12, 70, 28, 75 | 125/26/49 | 121/18/61 |
| SF17.1 E2200 vs E2400 (5+0.05) | 43, 7, 36, 6, 8 | 28/11/61 | 28/6/66 |
| SF17.1 E2400 vs E2600 (5+0.05) | 44, 17, 36, 2, 1 | 22/11/67 | 16/12/72 |
| Stash 15.3 vs SF17.1 E2400 (5+0.05) | 25, 5, 44, 9, 17 | 46/7/47 | 41/7/52 |
| Chromatique vs SF17.1 E2400 (30+0.3) | 2, 1, 15, 3, 29 | 38/2/10 | 38/2/10 |
| Chromatique vs SF17.1 E2400 (120+1) | 1, 1, 21, 4, 73 | 91/1/8 | 80/4/16 |
| Chromatique vs Stash 15.3 (120+1) | 0, 3, 16, 17, 64 | 84/7/9 | 77/13/10 |

## Completed style observations

The common-position panel supports a **capture-seeking tendency in this
sample**. It does not clearly show more checks or more low-loss material
offers. Most Chromatique choices were quiet. These observations do not
establish the advertised “zero positional play” or a general tendency toward
sound sacrifices.

| Common-position measure | Chromatique | SF17.1 E2400 | Difference in percentage points, bootstrap 95% | Positions |
|---|---:|---:|---:|---:|
| Check | 3.5% | 2.5% | +1.0 [-1.5, +4.0] | 200 |
| Capture | 35.0% | 19.0% | +16.0 [+10.0, +22.0] | 200 |
| Quiet | 64.0% | 80.5% | -16.5 [-23.0, -10.5] | 200 |
| Material-offer proxy | 11.0% | 9.0% | +2.0 [-1.5, +5.5] | 200 |
| Offer proxy with estimated loss ≤50 cp | 6.5% | 4.5% | +2.0 [-1.0, +5.0] | 199 |
| Estimated loss ≥100 cp | 11.6% | 15.1% | -3.5 [-9.5, +2.5] | 199 |

These are exploratory, individual percentile-bootstrap intervals. The more
conservative Hoeffding intervals include zero for every difference; all are
published in [the complete style summary](results/style-probe-summary.json).
One mate-valued position is excluded from ordinary centipawn thresholds.
Both engines chose the same move in 58/200 positions. The median of
`max(0, estimated judge loss)` was 9 cp for Chromatique and 16 cp for the
reference over 199 non-mate positions each.

The full-game descriptive data are separate from this matched-position
comparison. Chromatique’s quiet-move fraction varied from 63.6% to 75.3%
across main opponents; game trajectories and opponent strength confound those
rates. [Per-game rows](results/game-style.csv) and [all descriptive summaries](results/game-style-summary.json)
retain the denominators.

Three examples were selected by the predeclared loss-ranking rule and
rejudged at two million nodes per search:

- **Probe 27, 13.Bxe6:** a credible tactical offer. The legal acceptance line
  `Bxe6 fxe6 Qxe6+` concedes one pawn-equivalent net material. The retained
  stronger-judge line instead declines with `...Qe7`; the forced-choice score
  remains +234 cp, 24 cp below the unrestricted estimate.
- **Probe 102, 17.Nxc7:** a temporary knight offer. The recorded line
  `Nxc7 Nxc7 Nxd6 Ne6 Rxc8+ Rxc8 Nxc8` recovers material and leaves White
  two pawn-equivalents better than before the sequence. Both engines chose
  this move. Its −6 cp estimated loss is small search noise, not proof of
  improvement over the best move.
- **Probe 143, 13.h4:** a large estimated error. The move leaves Black’s d4-pawn
  fork on Nc3 and Be3 unaddressed; the baseline move `Bxd4` removes that pawn.
  The stronger judge changes from +73 cp at baseline to −355 cp after `h4`,
  a 428 cp loss. The reference’s `Ne2` also loses an estimated 231 cp. This
  case shows how the offer proxy can count an already hanging piece.

[Example JSON](results/style-examples.json) and [annotated analysis PGNs](results/style-examples.pgn)
retain full histories and PVs. These are selected illustrations, not a
representative sacrifice success rate or a claim to know the engine’s intent.

## What is measured

The target is unmodified revision
[`4d462c8f`](https://github.com/lusolitaire-dot/Chromatique/tree/4d462c8f7883f4e08d3d0e151de0374a6150ea22),
with its bundled v4 model, learned policy enabled and full-strength settings.
Chromatique's inherited `UCI_Elo` control is disabled; it does not calibrate
the replacement evaluator. Puzzle ratings are not playing ratings.

The measured host is an Apple M5 Pro with 15 logical CPUs and 24 GiB RAM,
running macOS 27.0.1. Builds use Apple Clang 21. Each engine uses one search
thread and 32 MiB hash where supported, with pondering and tablebases off.
Six games run concurrently. Fresh engine processes start every measurement
game. Source revisions, binary/model/network hashes, build commands and
hardware are in [`data/environment.json`](data/environment.json); actual
commands and input hashes are in each `.run.json` receipt.

## Fixed match design

| Purpose | Opponent(s) | Games | Initial time + increment |
|---|---|---:|---|
| Main strength | Stockfish 17.1 settings 2200, 2400, 2600 | 400 each | 5 seconds + 0.05 seconds/move |
| Independent engine | Stash 15.3 | 400 | 5 + 0.05 |
| Local calibration checks | SF2200–SF2400, SF2400–SF2600, Stash–SF2400 | 200 each | 5 + 0.05 |
| Clock sensitivity | SF2400 | 100 | 30 + 0.3 |
| Separate long-clock validation | SF2400 and Stash 15.3 | 200 each | 120 + 1 |

The original 2,300-game schedule was committed before the first measurement
game. A separate 168-game selection pilot is retained and excluded from all
fixed-schedule estimates. Its closest-to-even setting, SF2400, became the
central reference; Fruit's 0/24 pilot was too strong for efficient precision
matches. The two 120+1 extensions total 400 games. Their source-based triggers
and prospective declaration times are documented in
[`CALIBRATION-VALIDATION.md`](CALIBRATION-VALIDATION.md).

Every opening is played twice with colors reversed. The checksum-pinned
CC0 Stockfish `8moves_v3` book supplies 16-ply histories. Deterministic hash
ranking selects distinct final positions without reference to Chromatique's
choices or outcomes. Pilot, main, bridge, slower and anchor panels are
disjoint; the same main panel is reused across main opponents. Color pairing
does not establish that individual starting positions are evaluation-balanced.

No score-based resignation or draw adjudication is used: the engines' scores
have different meanings. Rule draws and a declared 300-move administrative
draw limit apply. Genuine clock losses, crashes and illegal moves stay in the
result. The runner uses a 100 ms time margin and refuses changed or unfinished
existing artifacts. Compiler builds and engine-based judging run outside
timed matches; practical load-control limits are recorded in
[`EXECUTION-NOTES.md`](EXECUTION-NOTES.md).

## Elo and uncertainty

For score fraction `s = (wins + draws/2) / games`, the reported relative
logistic Elo is `400 log10(s / (1-s))`. The sampling unit is a complete
opening pair. Its normalized score is one of `0, 0.25, 0.5, 0.75, 1`; five
counts preserve the full pentanomial distribution.

The primary 95% interval uses the unbiased variance of those pair scores,
a normal interval for their mean, and transformed Elo endpoints. A seeded
20,000-resample pair bootstrap supplies a sensitivity check. A conservative
Hoeffding interval is also retained for every match and replaces the primary
interval when empirical variance is zero. Boundary Elo estimates remain
unbounded. These are individual, conditional intervals, not simultaneous
coverage across all opponents or a measure of external calibration error.
Shared openings correlate opponent-specific results, so nominal anchors are
not pooled as independent ratings. See [`PROTOCOL.md`](PROTOCOL.md) and
the [primary methodology sources](SOURCES.md).

Independent replay checks every recorded legal move, rules-terminal result,
opponent, time control, complete opening history and exact reversed-color
pair count. It verifies receipt and PGN/book checksums before recomputing
W/D/L, color splits, terminations, pair counts and confidence intervals.

## External rating limits

Stockfish 17.1 inherits the polynomial from a historical Stash calibration
at 120+1. No fresh calibration specific to 17.1 was located. The old fit's
roughly 100-Elo discrepancy with CCRL is historical context, not a present
uncertainty bound. A nominal setting plus our relative Elo is a conditional
Stockfish-setting equivalent.

CCRL's list computed on 2026-10-17 rates **Stash 15.3 64-bit at 2174,
+19/−19 (95%), from 982 games**. Its official archive dates those games to
May 2020 and omits their time controls. Present scaled 2+1 policy does not
establish their historical clock or hardware. Tested-binary identity and
equal strength with our same-release ARM64 build are unverified. CCRL uses
BayesElo; this study uses a logistic score transform. Adding our match delta
to 2174 assumes transfer across models, builds, clocks and pools. Keep the
published rating interval separate from our match interval; the remaining
transfer uncertainty is unknown. [Primary references and capture
provenance](SOURCES.md), [structured source receipt](data/rating-sources.json).

For scale, the 120+1 nominal Stockfish-setting equivalent is `2400 + 326 =
2726`, while the Stash illustration is `2174 + 308 = 2482`. Their roughly
244-point difference is not resolved by the match sampling intervals. The
source rating’s ±19 interval and the unmeasured transfer error remain separate
from our relative-match intervals. Averaging these numbers would conceal the
calibration disagreement.

Neither comparison awards Chromatique a CCRL, human FIDE or online rating.

## Evaluating the romantic-style claim

The fixed main PGNs supply descriptive check, capture, quiet-move and
material-deficit rates after the forced book moves, plus game-length and
queenless-game context. They do not isolate style from differing positions,
opponent strength or forced defense.

A separate common-position panel selects at most one eligible position per
central-match opening pair, using the predeclared hash/ply rule. Both engines
choose from the identical board and full history with 0.25 seconds each.
Full-strength Stockfish 17.1 judges the position and each distinct choice at
200,000 nodes per search. Checks, quiet moves, material-offer proxies and
estimated evaluation loss are compared in opening-paired observations.
Mate-valued searches are retained separately from ordinary centipawn losses.

The offer proxy measures exposure of a non-pawn to a legal capture, allowing
an immediate recapture; it can include an already hanging piece. Low estimated
judge loss does not prove intent, soundness or a sacrifice. The predeclared
two lowest-loss and one highest-loss target offer examples receive separate
two-million-node inspection, without filtering source-game outcomes. All
histories, moves and analysis continuations are retained. These examples are
selected illustrations, not a sacrifice success rate.

The judge shares Stockfish's evaluation family with the comparator. Probe
positions come from Chromatique's central-match trajectories, omit checks and
positions with few legal choices, and use a different clock from the games.
Style comparisons are exploratory and have no multiple-comparison correction.
Quiet moves alone cannot establish positional understanding; a neural
evaluator's lack of a hand-written material term cannot establish “zero
positional play.”

## Reproduce and inspect

[`REPRODUCING.md`](REPRODUCING.md) gives setup, match, replay, style and
example-inspection commands, with fresh output directories for new matches.
The scripts use only the repository's declared Python development
requirements. External UCI engines and Fastchess are local benchmark tools;
their source trees and binaries are not redistributed here. PGNs remain
plain text. All 34 completed match logs and recovery states are retained in
lossless gzip archives with raw/compressed checksums and verified roundtrips
in [the archive manifest](results/log-archives.json). The
[fresh-checkout setup receipt](results/setup-receipt.json) and its compressed
output retain the actual build and test result; Linux remains untested.
The [final data-verification receipt](results/verification.json) records
identical recomputed summaries, unchanged measured inputs, legal style
histories/choices/PVs and the completed-run guards. The fresh setup passed all
seven release tests and eight benchmark tests.
The subsequent [review fix and final verification](results/review-verification.json)
add an archive-preservation regression; the final suites pass seven release
tests and nine benchmark tests. The measured results remain unchanged.

Rerunning the same wall-clock searches need not reproduce the same moves.
Reproducibility means pinned inputs, explicit controls, complete retained
evidence and rerunnable calculations.

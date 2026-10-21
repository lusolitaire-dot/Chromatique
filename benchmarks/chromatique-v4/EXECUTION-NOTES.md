# Execution notes

The target's C++ source and weights remain unchanged from the pinned v4
revision. The initial seven release tests passed. The benchmark's nine focused
tests cover score orientation, opening-pair uncertainty, degenerate samples,
replayed result/color/pair validation, material-offer accounting and exclusion
of mate scores from centipawn loss, predeclared low/high-loss example selection,
and archive-manifest preservation. A CLI regression also checks that rejected style reruns preserve
all existing files without starting an engine. Other CLI checks verified
lossless log archiving, rejection of
unfinished runs, and rejection of partial style panels before example judging.

The complete main schedule, sampled opening panels and initial scripts were
committed as `28ce97f` before the first measurement game started. All 168 pilot
games are excluded from the fixed-schedule estimates. The 2200 setting's small
pilot was noisy; the 2400 setting was closest to a 50% score and was selected
as the central reference. The main opponents are its two 200-point neighbors
and Stash 15.3. Fruit's 0/24 pilot is retained, and Fruit is excluded from the
precision matches because it was too strong for an efficient estimate.

The original 2,300-game runner process loaded the code from `28ce97f`.
While it was running, `13dbda1` added an alternate output-directory argument
for later reproductions; the default Fastchess command construction did not
change. Each receipt retains the actual command. The original live process
was not restarted to pick up that CLI change.

Final-schedule games use `restart=on`, confirmed in Fastchess's implementation
to discard and recreate each engine process after a game. This limits state
carryover between openings. Pilot processes were reused. Fastchess printed
warnings for the pilot Stash `Ponder` option, which Stash does not expose;
its search was not given `go ponder`. The final Stash configuration omits
that unsupported option. The runner now checks advertised options before a
new match starts.

A separate research review checked the paired-score standard error,
multinomial pair bootstrap and bounded Hoeffding intervals against primary
sources and found no blocking formula error. It identified mate-to-centipawn
mixing in the initial style implementation. Before any style probes ran, the
script was changed to report mate transitions separately. A focused test
demonstrated the missing behavior and then passed with the correction.
This review preceded the separate final code/results review reported below.

The deterministic low/high-loss example-selection rule was committed in
`f36cb72`, after the first main match but before any common-position style
probe existed. It uses the previously unseen probe estimates and has no
source-game-outcome filter. Its timing is separate from the original match
schedule's freeze.

Before any style probes ran, rerun testing exposed writes to the position
manifest and descriptive outputs before the script refused existing probe
evidence. The guard now runs before those writes. The retained expected-failure
logs demonstrate the defect; the updated eight-test suite passes all three
existing-file cases. Tests used temporary fixtures and blocked engine startup.

During timed matches, the agent inspected progress, edited documentation and
scripts, and ran brief focused script tests (under one second of measured
wall time for the last suite). No compiler builds or engine-based style/judge
analysis ran alongside final timed matches. This is the practical execution
interpretation of the protocol's load control; background OS activity, CPU
affinity and thermal conditions were not measured or controlled.

The underlying official Fruit archive returned HTTP 404. The retained source
mirror builds and identifies as Fruit 2.1; byte identity with the original
author archive remains unverified. No current external rating was inferred
from the download failure. The dated CCRL snapshot is context, not a
calibration of this Apple Silicon build or time control.

The complete original 2,300-game schedule passed independent legal replay,
exact opening-pair checks and receipt checksums. It retains one Stockfish time
forfeit and three reported Stash crash/disconnect losses; their underlying
causes remain undiagnosed. No game reached the administrative 300-move limit
(maximum 245). All 200 style source histories/FENs, 400 legal choices,
SAN/check/capture/quiet flags, mate-aware losses and 600 recorded judge PVs were
checked against the source PGN and position manifest. Repeated choices share
a judge search. The three predeclared examples were rejudged at two million
nodes before long-clock matches began; their analysis histories and PVs
passed legality checks.

The four original opening panels remained byte-identical when the new
100-position anchor panel was generated. All five panels are disjoint. The
anchor inputs were committed as `55e879d` before the 120+1 runner started at
2026-10-20 16:00:04 UTC. An explicit macOS idle-sleep assertion was attached to
that runner and verified at 16:06:27 UTC with `caffeinate -i -w <runner PID>`.
Its configured lifetime follows the fixed 400-game runner. Power conditions
were not continuously logged before that assertion; CPU affinity, frequency
and thermals remain uncontrolled.

The two 120+1 matches completed with Fastchess exit status zero: SF2400 at
2026-10-20 18:49:01 UTC and Stash at 21:27:11 UTC. The queued independent
analysis then passed legal replay, exact opening-pair checks and receipt
checksums for all 400 games. Chromatique W/D/L is 171/5/24 against SF2400 and
161/20/19 against Stash. One Stash Black disconnect loss is retained (PGN
Round 85, Fastchess game 169, ply 229); its cause is unknown. The other 399
termination tags are normal. Neither match reached the administrative cap.
The explicit idle-sleep guard exited normally at 21:27:11 UTC; its completed
lifecycle receipt is retained in `results/anchor-idle-guard.json`.

All 17 match receipts, including the seven selection pilots, have exit status
zero and matching PGN checksums/counts. All 34 raw logs and recovery states
were retained locally and losslessly archived after the last timed game.
The archive manifest records compressed and original byte counts and SHA-256
hashes; every decompressed byte was compared with its original.

The complete setup script passed in a fresh temporary checkout of `7d8c7dc`,
with pinned public-source downloads and the existing constrained Python
requirements, from 21:29:08 to 21:30:05 UTC. All seven release tests and eight
benchmark tests passed there; both suites also passed in the measured checkout
after the timed matches. The target, model, all reference-engine binaries and
opening manifest reproduced byte-for-byte on this host. Fastchess's fresh
binary hash differed; its source revision and both binary hashes are retained.
The original measured binaries were preserved. Linux was not exercised.

The final data audit recomputed all 17 match summaries identically and all
style summaries from retained records. Ten fixed-run receipt guards returned
`Already complete` without new games. The seven historical pilot commands
precede `restart=on`, and the Stash pilot retains its unsupported `Ponder`
warning; they passed replay and input-hash checks rather than a false claim
of identity with the current runner command. An initial audit incorrectly
treated judge node limits as minimum work. Probe 142's shared mate-in-three
choice search ended at 21,917 nodes; both logical records remain in the data.
The corrected audit checks those mate records separately.

A fresh whole-branch review of `66a725f` independently replayed all 2,868 games,
reproduced all 17 summaries, checked all 34 archives, measured input hashes,
style records and source captures, and found no blocking scientific error.
It found one Important/P2 custody defect: invoking the archiver in a published
checkout without raw logs replaced its retained manifest with an empty one.
The archiver now rejects empty raw input before writing, and reproduction
instructions point to the new run directory. The public-CLI regression failed
before the fix and passed afterward; the final suites passed seven release
tests and nine benchmark tests. Rerunning archival with the actual raw evidence
verified all 34 archives and left the manifest byte-identical. The review had
no Critical findings, deferred minors or declined-to-judge items. The fix and
its evidence are in `results/review-verification.json`; no new games or judge
searches were needed.

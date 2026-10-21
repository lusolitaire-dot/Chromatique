# Additional validation at 120+1

This extension is declared while the first fixed main match is still running,
before inspecting its aggregate score. It does not change the original
schedule or stop rule. The trigger is the source review: the historical
strength-setting fit inherited by Stockfish 17.1 used **120 seconds +
1 second/move**, and the original schedule uses shorter clocks. No fresh
Stockfish 17.1 calibration experiment was located.

Run **200 games (100 reversed-color opening pairs)** against Stockfish 17.1
`UCI_Elo=2400`, at **120+1**, with the same one-thread, 32 MiB hash,
no-tablebase and fresh-process controls. The central setting is the one
selected by the original short-clock pilot. It will not be retuned from the
long-match result. A boundary score yields a one-sided/unbounded relative
estimate rather than a result-dependent extension.

The new `anchor` panel is the next 100 distinct positions after the original
four panels in the same checksum-pinned book's deterministic hash ordering.
It is disjoint from all earlier panels. Generate it after the running timed
schedule has finished. The preparation script refuses to alter any existing
panel with different content. Retain all input hashes before launching this
validation matches. Its exact schedule is `anchor-schedule.json`.

A second extension was declared at the additional UTC timestamp recorded in
`anchor-schedule.json`, after the two
short-clock main matches against settings 2200 and 2400 had completed, while
the 2600 match was running, and before the main Stash match or either 120+1
match started. It adds **200 games (100 pairs) against Stash 15.3 at 120+1**,
using the same anchor panel and controls. The trigger is newly retrieved
primary evidence: the current CCRL Blitz list publishes Stash 15.3 64-bit at
2174, with a 95% interval of +19/−19 from 982 games. This match count will not
change in response to its score. The original 2,300-game schedule is unchanged;
the two separate extensions total 400 games.

The official archive dates all 982 Stash games to May 2020 and omits their
time-control tags. CCRL's current policy is scaled 2+1, but that does not
establish the literal clock, hardware or hash used in those historical
games. The list names a 64-bit build but gives no tested-binary checksum;
identity or equal strength with our same-release ARM64 build is unverified.
See [source evidence](SOURCES.md). This provides a conditional external
comparison, not a reproduction of the CCRL rating experiment.

Compute the same pair-level score, logistic Elo and uncertainty as the main
matches. Report each match separately. The two extensions share opening
positions, so their estimates are correlated. Adding the relative logistic
Elo difference to a Stockfish setting or Stash's published BayesElo rating
assumes transfer across clocks, builds and opponent pools, and for Stash also
across rating models. Show that assumption explicitly and retain the source
rating interval separately from our match interval.

The historical Stockfish fit's author described an approximately 100-Elo
discrepancy with the then-current CCRL Stash values. That is not a quantified
uncertainty bound for Stockfish 17.1, a Gaussian error bar, or evidence of a
fresh calibration. Present external-anchor uncertainty remains unknown.
Neither extension awards a CCRL or human rating.

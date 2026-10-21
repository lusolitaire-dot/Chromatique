# Chromatique benchmark evidence note

Reviewed 2026-10-20. Use paired openings, a predeclared final sample, and intervals computed from complete game pairs. Report relative match Elo as the main result. Treat a Stockfish strength setting or a historical rating-list value as a conditional anchor, with its calibration limits visible.

This note supplies source evidence and analysis recommendations. It contains no match results. The suggested build commands below were inspected against source but were not executed by this researcher.

**What is being tested**

The inspected Chromatique revision is `4d462c8f7883f4e08d3d0e151de0374a6150ea22`. Its README describes an independent neural evaluator and learned policy over a Stockfish 19 search and move-generation core. Its reused puzzle panel is explicitly a development benchmark, not an Elo estimate or final holdout. The romantic-style description is a claim to test. [Pinned README](https://github.com/lusolitaire-dot/Chromatique/blob/4d462c8f7883f4e08d3d0e151de0374a6150ea22/README.md), [pinned attribution](https://github.com/lusolitaire-dot/Chromatique/blob/4d462c8f7883f4e08d3d0e151de0374a6150ea22/NOTICE).

Chromatique exposes `Skill Level`, `UCI_LimitStrength`, and `UCI_Elo`; its inherited conversion still cites the Stockfish/Stash calibration. That conversion does not calibrate the replacement evaluator. Set Chromatique to full strength (`Skill Level=20`, `UCI_LimitStrength=false`) and record the actual UCI transcript. [Pinned controls](https://github.com/lusolitaire-dot/Chromatique/blob/4d462c8f7883f4e08d3d0e151de0374a6150ea22/src/engine.cpp#L109), [pinned inherited conversion](https://github.com/lusolitaire-dot/Chromatique/blob/4d462c8f7883f4e08d3d0e151de0374a6150ea22/src/search.h#L247).

**Match design and statistical interpretation**

- Cutechess documents `-repeat` as replaying an opening with exchanged colors. Fastchess documents two games per round, opening-file selection, a randomization seed, PGN export, and pentanomial reporting. Pin the runner revision, opening file and seed. Preserve opening identity so pair reconstruction is auditable. [Cutechess manual](https://github.com/cutechess/cutechess/blob/master/docs/cutechess-cli.6), [Fastchess manual](https://github.com/Disservin/fastchess/blob/master/man.md).
- Fishtest uses five pair outcomes: `LL`, `LD`, `DD/WL`, `WD`, `WW`. The statistical unit is the complete reversed-color pair, with total scores 0, 0.5, 1, 1.5, or 2. The original implementation explains why ignoring pairing changes interval estimates. [Fishtest mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html), [author's pentanomial implementation](https://github.com/vdbergh/pentanomial).
- SPRT tests predeclared hypotheses using a sequential stopping rule; it is not a target-precision rating experiment. Fishtest uses separate machinery to estimate Elo after sequential tests. For this report, choose opponents with a pilot, then freeze a separate final schedule and sample before seeing its results. Avoid repeatedly extending the final run until an ordinary fixed-sample interval excludes zero. This fixed-sample recommendation is our study-design choice. [Fishtest sequential methodology](https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics), [Fishtest implementation](https://raw.githubusercontent.com/official-stockfish/fishtest/master/server/fishtest/stats/stat_util.py).

For ordinary logistic Elo, score fraction `s = (W + D/2) / N` maps to `400 log10(s/(1-s))` Elo relative to that opponent under these match conditions. Fishtest implements this score transform. Its fixed-sample interval uses score variance and a normal approximation; its sequential estimator is separate. Label the Elo model: logistic Elo, BayesElo and normalized Elo are different quantities. [Fishtest statistical source](https://raw.githubusercontent.com/official-stockfish/fishtest/master/server/fishtest/stats/stat_util.py).

Recommended reporting calculations, derived for this study:

- Divide each pair's total score by two. The resulting observation is in `{0, 0.25, 0.5, 0.75, 1}`. Estimate the mean and its uncertainty across pairs, then transform the score interval endpoints to Elo. A normal or pair-bootstrap interval is approximate; state the method.
- Do not treat draws as two independent half-point trials or bootstrap individual games. If the same openings recur against several opponents, preserve that opening cluster when pooling across opponents. Report opponent-specific results first.
- A sample with no pair-score variance needs special treatment; a zero-width bootstrap interval would be misleading. At score 0 or 1 the raw logistic estimate is unbounded. Show the boundary and uncertainty rather than silently clamping it to a finite rating.
- As a planning approximation near a 50% score, the worst-variance normal half-width is about `681/sqrt(M)` Elo for `M` independent pairs. Thus 200 pairs gives roughly ±48 Elo and 1,000 gives roughly ±22 Elo. This calculation excludes calibration, book-selection and model errors; actual pair variance determines the reported interval.

Retain crashes, illegal moves, time forfeits, unfinished games, pair completeness, and termination reasons in the primary record. If a documented scheduling fault motivates a sensitivity analysis, show both totals and the exclusion rule. A changed control or excluded game must not silently replace the original result.

**Stockfish 17.1 calibration is approximate**

The `sf_17.1` source converts `UCI_Elo` through a fit against versions of Stash and describes its range as approximately 1320–3190 CCRL Blitz Elo. [Stockfish 17.1 source](https://github.com/official-stockfish/Stockfish/blob/sf_17.1/src/search.h#L170).

The calibration commit referenced by that source used 120 seconds plus a 1-second increment. Its author says the Stash ratings in the fit agreed with CCRL only within about ±100 Elo, probably because of opponent-pool effects. Older 60+0.6 wording was replaced in that same commit. That ±100 is an author's calibration caveat, not an independent Gaussian standard deviation to add mechanically to a match error bar. [Original calibration commit and README change](https://github.com/vondele/Stockfish/commit/a08b8d4e9711c2).

Stockfish's official FAQ explains that weaker play deliberately selects suboptimal moves, and that Elo depends on time control, openings, hardware and opponent pool. Therefore a match against `Stockfish 17.1 UCI_Elo=2000` at another time control establishes performance against that configured engine. Adding 2000 to the measured Elo difference produces a nominal estimate on the settings ladder, not an independently verified CCRL or human FIDE rating. [Official Stockfish FAQ](https://official-stockfish.github.io/docs/stockfish-wiki/Stockfish-FAQ.html#the-elo-rating-of-stockfish).

**Small public opening book**

The official Stockfish book repository publishes `8moves_v3.pgn.zip` under CC0-1.0. Its metadata lists 34,700 entries, each 16 plies deep; GitHub reports the ZIP as 789 KB. [Repository and license](https://github.com/official-stockfish/books), [book metadata](https://github.com/official-stockfish/books/blob/master/books.json), [archive](https://github.com/official-stockfish/books/blob/master/8moves_v3.pgn.zip), [raw download](https://raw.githubusercontent.com/official-stockfish/books/master/8moves_v3.pgn.zip).

Use a pinned repository revision and record the archive and extracted-file hashes. Select a reproducible sample without repeating an opening within a final matchup. The metadata's `white` count denotes side to move, not proof of evaluation balance. The Stockfish team's book comparison measured nonzero opening bias for this book, so describe color-balanced pairing separately from positional balance. [Primary book comparison](https://github.com/official-stockfish/Stockfish/issues/3323).

**Independent native opponents: verified published snapshots**

The accessible CCRL pages below identify their snapshot as **2024-11-16**. Their ratings are historical selection guidance. CCRL 40/15 uses time scaled to an Intel i7-4770k, ponder off, a shared generic book up to 12 moves, specified hash and tablebase conditions. An Apple Silicon fast match does not reproduce those conditions. [CCRL testing conditions](https://computerchess.org/about.html).

| Candidate | Published CCRL 40/15 snapshot | Source and practical limit |
|---|---:|---|
| Pigeon 1.5.1 64-bit | 1753, +24/−24; 502 games | [CCRL row](https://computerchess.org/cgi/engine_details.cgi?each_game=0&eng=Pigeon+1.5.1+64-bit&print=Details). [Author repository](https://github.com/StuartRiffle/pigeon), MIT and UCI. CMake identifies 1.5.1, but the source assumes x86 intrinsics and CPU detection; this is a poor candidate for a small ARM-native build. [Version](https://github.com/StuartRiffle/pigeon/blob/master/CMakeLists.txt), [platform assumptions](https://github.com/StuartRiffle/pigeon/blob/master/src/platform.h). |
| Vice 1.0 64-bit | 1995, +22/−22; 639 games | [CCRL row](https://computerchess.org/cgi/engine_details.cgi?each_game=0&eng=Vice+1.0+64-bit&print=Details). The [author repository](https://github.com/bluefeversoft/vice) now points to instructional chapter branches and latest 1.1. No exact rated-1.0 source match was verified here. Do not label a current branch with the 1.0 rating. |
| Fruit 2.1 | 2693, +22/−22; 518 games | [CCRL row](https://www.computerchess.org/cgi/engine_details.cgi?eng=Fruit+2.1&print=Details). Fabien Letouzey's original release README identifies UCI-only, portable C++ source and GPL-2.0-or-later. It names WBEC as official distributor. [Original distribution page](https://www.wbec-ridderkerk.nl/html/details1/Fruit.html), [retained original README in mirror](https://github.com/Warpten/Fruit-2.1/blob/master/readme.txt). |
| Texel 1.03 64-bit | 2946, +21/−21; 538 games | [CCRL row](https://www.computerchess.org/cgi/engine_details.cgi?eng=Texel+1.03+64-bit&print=Details). The [author's exact release](https://github.com/peterosterlund2/texel/releases/tag/1.03) identifies tag `1.03`, commit beginning `ed426c5`. This supplies a stronger native candidate; its ARM build path was not inspected. |

Fruit's official archive discovery URL is `https://www.wbec-ridderkerk.nl/html/download/fruit/fruit_21.zip`. The WBEC page fetched once but timed out on subsequent access; the archive itself was not downloaded here. The GitHub mirror's [Makefile](https://github.com/Warpten/Fruit-2.1/blob/master/src/Makefile) suggests `make -C src CXX=clang++ LDFLAGS=-lm`; overriding the link flags removes an old strip option. This command remains unexecuted. If using that mirror, record its full commit and retain the unverified archive-identity limitation. Disable Fruit's own opening book and use the default evaluation parameters.

For an intermediate opponent, the author-owned [Stash v15.3 release](https://github.com/mhouppin/stash-bot/releases/tag/v15.3) supplies C source, UCI and GPL-3.0-or-later. Its [tagged README](https://github.com/mhouppin/stash-bot/blob/v15.3/README.md) self-reports around 2160 Elo. The [tagged Makefile](https://github.com/mhouppin/stash-bot/blob/v15.3/src/Makefile) has a generic path when `ARCH` is unset; candidate command `make -C src CC=clang` is unexecuted. A matching independent CCRL row was not retrieved. The Stockfish calibration fit fixed this version at 2200 locally; that is a fit anchor, not fresh external verification.

**Testing the style claim**

The following are proposed operational measures, not a recognized rating scale for romantic chess. Exclude forced opening plies, preserve the denominator of freely chosen moves, and compare engines from matched positions or equivalent paired schedules.

| Measure | Reproducible definition | Interpretation limit |
|---|---|---|
| Checks and captures | Fraction of chosen moves giving check; fraction capturing | Forced defense and tactical necessity can produce both. |
| Quiet moves | Fraction that are neither captures, checks, nor promotions | A quiet move can prepare a combination; this cannot establish “zero positional play.” |
| Material-deficit episodes | Declare piece weights, loss threshold and persistence window; count episodes rather than each deficit ply | Material loss can be an exchange, forced defense, or blunder. Call these candidates, not sacrifices. |
| Sacrifice candidates | Preserve the move, FEN, legal alternatives, ensuing material change, and full continuation | A later opponent mistake does not prove the original offer was sound. |
| Soundness review | Reanalyze candidates and alternatives with a pinned stronger evaluator at a fixed analysis budget | Search is an estimate. Report evaluation loss and analysis settings; inspect promotion, mate and tablebase cases separately. |
| Outcome context | Give candidate counts by game result, opponent and color | Winning games alone select flattering examples. |

Use simple piece weights only as an accounting rule; never equate material points to either engine's reported centipawns. Stockfish's normalized evaluation and WDL model depend on self-play conditions, and it does not itself assign “brilliant” move labels. [Official evaluation and annotation explanation](https://official-stockfish.github.io/docs/stockfish-wiki/Stockfish-FAQ.html#interpretation-of-the-stockfish-evaluation).

A defensible conclusion can say that the tested build produced more checks or more inspected sound sacrifice candidates than its comparator in this sample. A few striking wins, high puzzle accuracy, or frequent material losses alone cannot establish the advertised style.

**Access and remaining uncertainty**

CCRL's current `.org.uk` full pages repeatedly failed to open; shell `curl` also failed DNS with exit 6. Accessible `.org` engine-detail pages supplied the explicitly dated snapshots above. Fruit's current homepage returned 502, WBEC was intermittent, and SourceForge could not be opened. A potential style-measurement paper encountered a browser challenge and was not used. No source-access failure was treated as evidence about an engine's strength or availability.

**Read-only scientific review of the frozen implementation — 2026-10-20**

Reviewed `PROTOCOL.md`, `schedule.json`, `scripts/analyze.py`, `scripts/style.py`, and the opening-preparation and runner code under `Chromatique/benchmarks/chromatique-v4`. No engine, build, test, statistical script, or match was run during this review. The running measurements were left untouched.

**Verdict: no scientific blocker to completing the frozen matches.** The strength formulas implement the stated analysis. One conditional style-summary defect needs checking after the probe data exists.

- **Strength uncertainty is consistent.** In `analyze.py:25–49`, `statistics.variance` supplies the unbiased pair variance, and the score standard error is its square root divided by the square root of the pair count. The categorical multinomial bootstrap is equivalent to resampling complete pairs. Transforming interval endpoints with the increasing logistic Elo function preserves interval coverage in the interior. Boundary estimates remain unbounded; the fallback avoids zero uncertainty in constant samples. These choices agree with the pair-based model and separate fixed-sample calculation in the [primary Fishtest statistical source](https://raw.githubusercontent.com/official-stockfish/fishtest/master/server/fishtest/stats/stat_util.py).
- **The conservative bounds use the correct ranges.** The strength bound has half-width `sqrt(log(40)/(2n))` for pair scores in `[0,1]`. The style difference uses twice that width because each paired binary difference lies in `[-1,1]`. These are fixed-sample bounds under independent opening-pair sampling. Shared openings make different matchup estimates correlated; the protocol already avoids treating them as independent calibrated anchors.
- **Conditional defect: mate surrogates enter centipawn summaries.** `style.py:139–185` maps mate scores to approximately ±100,000, then subtracts them into `judge_loss_cp`. Lines 207–223 can consequently mix mate surrogates into the 100-centipawn error bucket and the median loss. The low-loss-offer rule excludes a mate-valued selected move but leaves a mate-valued baseline eligible. If such rows occur, classify mate transitions separately and calculate ordinary centipawn thresholds and medians only where both scores are centipawns. Publish the affected count. This is an analysis/reporting repair, not a reason to restart timed games.
- **The material-offer definition matches its code, with a narrow meaning.** It measures exposure to a legal capture after the chosen move, net of an immediate recapture. It can count a piece already hanging before the move, and ignores compensation realized after that short material sequence. Use “material-offer proxy”; a “sound sacrifice” needs separate continuation review. The protocol already distinguishes the proxy from intent and soundness.
- **Style inference stays conditional on this panel.** Probe positions all occur on Chromatique's turns in its central-match games. Both engines receive identical boards, but the distribution reflects those game trajectories and excludes checks, short games and positions with few legal moves. Equal 0.25-second searches also define a different condition from the match time control. Report this sampled-position comparison; it does not establish a universal engine personality.

The already-disclosed normal/bootstrap approximation, individual rather than simultaneous intervals, evaluator-family dependence, unequal unrestricted/forced judge searches, exploratory style metrics and external-rating uncertainty remain limitations. They are not additional reasons to stop the fixed experiment. Queenless-by-move-40 and game length describe the shared game; neither supplies an engine-specific style effect on its own.

Implementation follow-up: the mate-handling finding above was repaired in `13dbda1` before any style probes ran. The completed panel contains one mate-valued position, excluded from ordinary centipawn statistics. See [execution notes](EXECUTION-NOTES.md) and the [retained results](results/style-probe-summary.json).

**Verified Stash reference and inherited Stockfish calibration — update 2026-10-20**

This update supersedes the earlier missing-Stash-row statement and the blanket CCRL access-failure statement. Normal sandbox DNS and web opens failed, but authorized public `curl` reads subsequently returned HTTP 200 and the expected rating content. The following are directly retained primary-source captures, rather than search snippets.

**Stash 15.3 64-bit has a verified CCRL Blitz rating of 2174, +19/−19, from 982 games**, in the list computed on **2026-10-17**. CCRL's own column explanation identifies these bars as **95% confidence intervals**. Its detailed record gives 496 wins, 151 draws and 335 losses. [Complete list and column definitions](https://computerchess.org.uk/404/rating_list_all.html), [exact engine record](https://computerchess.org.uk/404/cgi/engine_details.cgi?print=Details&each_game=1&eng=Stash%2015.3%2064-bit).

The [official 982-game archive](https://computerchess.org.uk/404/games-by-engine/Stash_15_3_64-bit.bare.%5B982%5D.pgn.7z) contains games dated **2020-05-12 through 2020-05-29**. All 982 lack a `TimeControl` tag; the bare PGNs also lack CPU, hash, ponder and thread-option tags. The archive's current `Event` and Elo tags reflect the present Blitz publication. They do not establish the historical clocks or hardware.

The [current Blitz conditions](https://computerchess.org.uk/404/about.html) specify time equivalent to **2+1 on an Intel i7-4770K**, using Stockfish 10 to scale machine speed. Present policy also specifies ponder off, 128 or 256 MB shared hash, tablebases and a shared generic opening book limited to 12 moves. These are present-policy facts, not verified conditions for those May 2020 games. The [2026-10-16 complete 40/15 snapshot](https://computerchess.org.uk/4040/rating_list_all.html) contains no Stash 15.3 entry; an earlier 40/15 rating was not established.

The [author's pinned commit](https://github.com/mhouppin/stash-bot/commit/7d17ff80eb53b9d4808fd285c7439e641f1c5a3b) sets the release version to 15.3. This matches CCRL's named release. The public rating entry supplies no tested-binary hash, so release identity does not establish binary identity or equal strength between its 64-bit build and the local ARM-native build. The rating is a BayesElo pool estimate; adding our logistic match delta to 2174 is an illustrative anchored performance estimate, not a recomputed CCRL rating. Publish the two uncertainty sources separately. [BayesElo author's model description](https://www.remi-coulom.fr/Bayesian-Elo/).

**Stockfish 17.1 inherits a historical calibration.** The [official Stockfish 16 announcement, dated 2023-06-30](https://stockfishchess.org/blog/2023/stockfish-16/), links the original calibration change. The [Stockfish 16 polynomial](https://github.com/official-stockfish/Stockfish/blob/sf_16/src/search.cpp#L89) and [Stockfish 17.1 polynomial](https://github.com/official-stockfish/Stockfish/blob/sf_17.1/src/search.h#L170) have identical coefficients. The latter explicitly calls its CCRL Blitz mapping approximate and references the older fit. No fresh empirical calibration specific to 17.1 was located. The original fit's roughly 100-Elo disagreement with CCRL is historical context, **not a quantified current error bound or confidence interval for Stockfish 17.1**. A prospective 120+1 match aligns the clock format with that historical fit; hardware, build, model and pool transfer remain uncertain.

A short [retained publisher excerpt](data/ccrl-stash153-excerpt.txt) preserves the dated row, rating model and interval definition, tied to the full response hash.

Capture provenance is below. Times are UTC from each response's HTTP `Date` header, all on 2026-10-20. Files are retained under workspace `tmp/`.

| Capture | UTC | Bytes | SHA-256 |
|---|---|---:|---|
| `ccrl-blitz-all.html` — complete list URL above | 14:26:34 | 2398391 | `951db112489df56fc2849cc19d9ce2c43bd890e19fbb849f040d87877eaacb26` |
| `ccrl-4015-all.html` — 40/15 URL above | 14:28:31 | 3883455 | `4880f2e392b99d12eb8cca6b5acb927c68d0f18eba776ce945f5b89e8acd5ece` |
| `ccrl-blitz-about.html` — conditions URL above | 14:29:35 | 6670 | `908cf7f1c981112cf08c483a7881a0d8777d8fb99fb359089a065d4bc80f08a4` |
| `ccrl-stash153-detail.html` — engine-record URL above | 14:31:20 | 38267 | `bb67ae23e4ada0ffee7c55fce4ec608cf9399ba254b1972ff711033d52964994` |
| `ccrl-stash153.pgn.7z` — archive URL above | 14:32:46 | 199108 | `a6639d03114c4f4085b182c9c5abf8cef540addccdc8f00f06c4f5c02519b338` |

The archive's single decompressed PGN is 992755 bytes, SHA-256 `3a0e9c848bd58300ec76b327e50fd0ed0ce92ff08d576a943b83f787364ecc53`. Only source-header metadata was inspected; no engines, builds, tests or match analysis ran during this lookup. No 403, 429 or browser challenge was bypassed.

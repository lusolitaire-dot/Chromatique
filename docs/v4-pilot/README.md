# V4 pilot checkpoint update

The default model is the retained **v4 result-learning pilot, epoch 1**, trained on 25 October 2026. It continues the selected epoch-one joint policy/value fine-tune of the original pure-v4 network. It is an experimental candidate with a small observed development-match edge, not a certified strength upgrade or a finished positional engine.

The original pure-v4 model is preserved as `weights/pure-v4.native` and `weights/pure-v4.json.gz`. Previous tagged releases and the `benchmarks/chromatique-v4/` evidence remain historical pure-v4 results. This update does not reattribute those results to the pilot.

## Exact model identities

| Model | Native SHA-256 |
|---|---|
| Default v4 pilot | `ffcffd32b3995fca5b01dc4c620f609af607ec21c4e1abcb7c1c4d5a9dd43b82` |
| Original pure v4 | `d6d70e384036e1101274268a900e42b133772470f56da3895c28ed2e7845ea56` |

The pilot checkpoint SHA-256 is `b86379b18968835b516c5c6122e78bd78fbf426e9ff4828a44486f3e003c9559`. The serialized native model is byte-identical to the retained research artifact. Both models use the same 820 → 512 → 32 float32 architecture, shared feature weights and 1,968-move policy vocabulary. No quantization, pruning, classical blending or Stockfish NNUE fallback is introduced. The C++ source is unchanged by this update. In this native adapter the policy orders the initial legal root moves; it does not order moves throughout the search tree.

## Training scope

The preceding joint continuation used 8,000 tactical puzzle examples and 16,000 general SF19-labelled positions. The retained pilot then collected 200 scheduled games (160 training and 40 development validation), obtaining 194 completed results and six censored games. Positions were sampled only from completed games for outcome learning; the pilot used at most 16 sampled states per game.

Each pilot minibatch mixed equal thirds of tactical replay, existing general static/policy replay and new game positions. Both policy and value parameters were trained. The hybrid objective combined actual SF19 static side-to-move targets, searched policy targets, policy/value retention terms, a small game-score loss and a small conditional clipped policy-gradient term. In-check static targets were masked. The retained epoch-one checkpoint kept the shared 512-neuron feature layer frozen.

Collection used 10,000 nodes per Chromatique move and calibrated 128/512-node SF19 opponents, with logged exploration. These collection games and their outcomes are not a matched strength test. This is not the later Dragon-assisted candidate or a candidate from the rejected five-generation experiment. No external puzzle/game dataset or third-party engine binary is bundled.

## Direct comparison with original pure v4

The completed five-generation experiment also contained deterministic gate games between the retained pilot and the frozen original pure v4. Extracting this matchup across the five generations yields:

| Pilot result | Count |
|---|---:|
| Wins | 25 |
| Draws | 14 |
| Losses | 21 |
| Score | 32/60 = 53.3% |

There are 30 distinct source-game openings, each played with colours reversed. Both sides received 20,000 nodes per searched move, one thread and 32 MiB hash. Exploration was disabled. All 60 games completed to legal rule results; none were censored or administratively adjudicated. All histories, model identities, requested node budgets and results were reverified for publication. Node accounting permits the runner's bounded search-stop overshoot; the requested budgets are equal.

Resampling the 30 complete opening pairs gives a descriptive 95% score interval of **41.7–65.0%**. This includes equality. These are existing development-opening games, not a newly sealed independent tournament, an established Elo gain, or proof of superiority over v10/E4_Pb. The game starts are midgame positions after the recorded forced history; this is not a match from 30 untouched initial opening positions.

- [Comparison details, source-record hashes and uncertainty](pilot-vs-pure-v4.json)
- [All 60 legally replayed PGNs](pilot-vs-pure-v4.pgn)

On the common 100,000-node tactical development panel, pure v4 solved 95/128 full lines; the intermediate joint checkpoint and retained pilot each solved 97/128. General-position development checks recorded 10 errors of at least 100 cp for pure v4, seven for the intermediate checkpoint and six for the pilot. The general counts come from successive teacher-scored continuation evaluations rather than a new three-arm match; small finite-search differences should not be overinterpreted.

The pilot's earlier fresh evaluation against limited SF19 recorded 21 wins, eight draws and three losses, compared with the intermediate checkpoint's 11 wins, nine draws, ten losses and two unfinished games. That positive result is **not** a direct comparison with pure v4, and does not isolate the game-outcome loss from the other training objectives. Later continuation attempts did not pass every development gate, so this earlier checkpoint remains retained.

## Selecting either model

After building the current checkout, `bin/chromatique-v4` loads the pilot by default. The executable name and UCI identity remain `Chromatique v4` for compatibility. To use the original model from the repository root:

```sh
CHROMATIQUE_NATIVE_MODEL="$PWD/weights/pure-v4.native" ./bin/chromatique-v4
```

Alternatively, set `ChromatiqueModel` to the absolute path of either native file in the UCI GUI. The JSON files are complete editable counterparts, and `tools/export_native.py` regenerates the exact corresponding native bytes.

This publication changes the repository's bundled default, not the separate research workspace or a running public-site GUI. The broader goal remains a well-rounded Chromatique; that work is ongoing.

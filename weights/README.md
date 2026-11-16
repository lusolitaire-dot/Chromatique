# Chromatique v4.1.0 weights

`chromatique-v4.1.0.json.gz` is the complete editable model as gzip-compressed JSON, and `chromatique-v4.1.0.native`
is its lossless float32 runtime export. They use the CHROMA4 independent-policy-encoder format:
820 → 512 → 32 for evaluation and an independently learned 820 → 512 → 1968 policy head.

Their SHA-256 checksums and architecture are recorded in [`../release.json`](../release.json).

The network and its policy head are distributed under GPL-3.0-or-later with
the engine. No external game or puzzle dataset is included.

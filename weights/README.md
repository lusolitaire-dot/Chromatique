# V4 pilot and preserved pure-v4 weights

`chromatique-v4.json.gz` is the complete editable retained v4 pilot as gzip-compressed JSON; `chromatique-v4.native` is its lossless float32 runtime export and the standalone engine's default.

`pure-v4.json.gz` and `pure-v4.native` retain the original pure-v4 artifacts byte-for-byte. Select the original native model with the UCI `ChromatiqueModel` option or the `CHROMATIQUE_NATIVE_MODEL` environment variable. Use an absolute path when launching from a GUI.

All checksums and the unchanged 820 → 512 → 32 architecture are recorded in [`../release.json`](../release.json). Training and evaluation notes are in [`../docs/v4-pilot/README.md`](../docs/v4-pilot/README.md).

The network and its policy head are distributed under GPL-3.0-or-later with
the engine. No external game or puzzle dataset is included.

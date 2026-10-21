"""Losslessly archive completed-run logs/states; retain the originals locally."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile

BASE = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=BASE / "results")
    args = parser.parse_args()
    manifest = args.results_dir / "log-archives.json"
    payload = json.loads(manifest.read_text()) if manifest.exists() else {"files": []}
    records = {}
    paths = sorted([*args.results_dir.glob("*.log"), *args.results_dir.glob("*.state.json")])
    if not paths:
        raise ValueError("No raw logs or recovery states; existing archive manifest left unchanged")
    # Archived-only runs still own provenance when just some raw files return.
    # Validate retained evidence before creating archives or replacing the manifest.
    for record in payload["files"]:
        name = record["original"]
        if (Path(name).name != name or not name.endswith((".log", ".state.json"))
                or record["archive"] != name + ".gz" or name in records):
            raise ValueError("Invalid or duplicate retained archive record")
        compressed = (args.results_dir / record["archive"]).read_bytes()
        raw = gzip.decompress(compressed)
        if (sha(compressed) != record["archive_sha256"] or len(compressed) != record["archive_bytes"]
                or sha(raw) != record["sha256"] or len(raw) != record["bytes"]
                or record.get("roundtrip_verified") is not True):
            raise ValueError(f"Retained archive verification failed: {name}")
        records[name] = record
    pending = []
    for path in paths:
        name = path.name.removesuffix(".log").removesuffix(".state.json")
        receipt = json.loads((args.results_dir / (name + ".run.json")).read_text())
        if receipt.get("returncode") != 0:
            raise ValueError(f"Do not archive an unfinished run: {name}")
        raw = path.read_bytes()
        destination = path.with_name(path.name + ".gz")
        compressed = destination.read_bytes() if destination.exists() else gzip.compress(raw, mtime=0)
        if gzip.decompress(compressed) != raw:
            raise ValueError(f"Archive roundtrip mismatch: {path}")
        record = {"original": path.name, "sha256": sha(raw), "bytes": len(raw),
                        "archive": destination.name, "archive_sha256": sha(compressed),
                        "archive_bytes": len(compressed), "roundtrip_verified": True}
        if path.name in records:
            if any(records[path.name].get(k) != v for k, v in record.items()):
                raise ValueError(f"Raw file differs from retained evidence: {path.name}")
        else:
            records[path.name] = record
        if not destination.exists():
            pending.append((destination, compressed))
    for destination, compressed in pending:
        with destination.open("xb") as output:
            output.write(compressed)
    payload["files"] = list(records.values())
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.results_dir,
                                         prefix=".log-archives-", delete=False) as output:
            temporary = Path(output.name)
            output.write(json.dumps(payload, indent=2) + "\n")
        os.replace(temporary, manifest)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Verified {len(records)} lossless archives; original files retained locally")


if __name__ == "__main__":
    main()

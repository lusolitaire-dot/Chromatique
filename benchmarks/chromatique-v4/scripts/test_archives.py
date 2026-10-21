"""Protect the published archive manifest when raw inputs are absent."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ArchiveCustody(unittest.TestCase):
    def run_archiver(self, root):
        return subprocess.run([sys.executable, str(Path(__file__).with_name("archive_logs.py")),
                               "--results-dir", str(root)], capture_output=True, text=True)

    def retained(self, root, name):
        raw = (name + " match\n").encode()
        compressed = gzip.compress(raw, mtime=0)
        (root / (name + ".log.gz")).write_bytes(compressed)
        (root / (name + ".run.json")).write_text('{"returncode": 0}\n')
        return {"original": name + ".log", "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(), "archive": name + ".log.gz",
                "archive_bytes": len(compressed), "archive_sha256": hashlib.sha256(compressed).hexdigest(),
                "roundtrip_verified": True}

    def test_partial_raw_rerun_preserves_all_existing_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = [self.retained(root, name) for name in ["first", "second"]]
            manifest = root / "log-archives.json"
            manifest.write_text(json.dumps({"files": records}, indent=2) + "\n")
            (root / "second.log").write_bytes(b"second match\n")
            before = manifest.read_bytes()
            result = self.run_archiver(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(manifest.read_bytes(), before)

    def test_new_run_keeps_archived_only_records_and_validates_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self.retained(root, "old")
            manifest = root / "log-archives.json"
            manifest.write_text(json.dumps({"files": [old]}, indent=2) + "\n")
            (root / "new.log").write_bytes(b"new match\n")
            (root / "new.run.json").write_text('{"returncode": 0}\n')
            result = self.run_archiver(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = json.loads(manifest.read_text())["files"]
            self.assertEqual(len(actual), 2)
            self.assertEqual(next(r for r in actual if r["original"] == "old.log"), old)
            before = manifest.read_bytes()
            (root / "old.log.gz").write_bytes(b"corrupt archive")
            result = self.run_archiver(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(manifest.read_bytes(), before)

    def test_archive_only_checkout_preserves_retained_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = b"Finished match\n"
            compressed = gzip.compress(raw, mtime=0)
            (root / "finished.log.gz").write_bytes(compressed)
            (root / "finished.run.json").write_text('{"returncode": 0}\n')
            record = {"original": "finished.log", "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest(),
                      "archive": "finished.log.gz", "archive_bytes": len(compressed),
                      "archive_sha256": hashlib.sha256(compressed).hexdigest(),
                      "roundtrip_verified": True}
            (root / "log-archives.json").write_text(json.dumps({"files": [record]}) + "\n")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            script = Path(__file__).with_name("archive_logs.py")
            result = subprocess.run([sys.executable, str(script), "--results-dir", str(root)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, before)


if __name__ == "__main__":
    unittest.main()

"""Prevent historical benchmark results from silently changing model identity."""
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from run_matches import ROOT, BASELINE_MODEL, benchmark_environment, sha


class ModelSelection(unittest.TestCase):
    def test_historical_model_matches_preserved_release(self):
        manifest=json.loads((ROOT/'release.json').read_text())
        self.assertEqual(sha(BASELINE_MODEL),manifest['weights']['pure-v4.native'])
        self.assertNotEqual(sha(BASELINE_MODEL),manifest['weights']['chromatique-v4.native'])

    def test_benchmark_process_loads_pure_v4_despite_default_update(self):
        with patch.dict(os.environ,{'CHROMATIQUE_NATIVE_MODEL':'/invalid/override','CHROMATIQUE_POLICY':'0'}):
            env=benchmark_environment()
        self.assertNotIn('CHROMATIQUE_POLICY',env)
        p=subprocess.run([str(ROOT/'bin/chromatique-v4')],input='uci\nposition startpos\neval\nisready\nquit\n',
            env=env,text=True,capture_output=True,check=True,timeout=15)
        trace=json.loads(next(s.removeprefix('chromatique ') for s in p.stdout.splitlines() if s.startswith('chromatique {')))
        self.assertEqual(trace['model_sha256'],BASELINE_MODEL.read_bytes()[24:88].decode())


if __name__=='__main__':unittest.main()

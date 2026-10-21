"""Check style accounting and refusal to overwrite retained evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import chess

from style import judge_loss, main as style_main, move_features


class StyleAccounting(unittest.TestCase):
    def test_rejected_rerun_preserves_existing_evidence(self):
        for existing in [("style-probes.jsonl",), ("style-positions.json",),
                         ("style-probes.jsonl", "style-positions.json")]:
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                games = [f'[White "{white}"]\n[Black "{black}"]\n[Result "0-1"]\n\n1. a3 a6 2. b3 b6 3. c3 c6 4. h3 h6 5. a4 a5 6. b4 b5 7. c4 c5 8. f3 e5 9. g4 Qh4# 0-1\n'
                         for white, black in [("Chromatique-v4", "Reference"), ("Reference", "Chromatique-v4")]]
                (root / "main-source.pgn").write_text("\n".join(games))
                schedule = root / "schedule.json"
                schedule.write_text(json.dumps({"matches": [{"id": "main-source", "engines": []}]}))
                for name in existing:
                    (root / name).write_bytes(b"original retained evidence\n")
                before = {p.name: p.read_bytes() for p in root.iterdir()}
                command = ["style.py", str(schedule), "--central-match", "main-source", "--results-dir", str(root)]
                with patch.object(sys, "argv", command), patch("chess.engine.SimpleEngine.popen_uci", side_effect=AssertionError("Blocked reruns must not launch an engine")):
                    with self.assertRaises(FileExistsError):
                        style_main()
                self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, before)

    def test_mate_scores_do_not_become_centipawn_losses(self):
        self.assertEqual(judge_loss({"cp_or_mate_equivalent": 120, "mate": None},
                                    {"cp_or_mate_equivalent": 20, "mate": None}), 100)
        for baseline, selected in [({"cp_or_mate_equivalent": 100000, "mate": 3}, {"cp_or_mate_equivalent": 20, "mate": None}),
                                   ({"cp_or_mate_equivalent": 120, "mate": None}, {"cp_or_mate_equivalent": -100000, "mate": -4})]:
            self.assertIsNone(judge_loss(baseline, selected))

    def test_piece_offer_counts_net_concession_and_excludes_equal_trade(self):
        board = chess.Board("rnbq1rk1/ppp2ppp/5n2/3pP3/3P4/3B1N2/PPP2PPP/RNBQ1RK1 w - - 0 8")
        result = move_features(board, chess.Move.from_uci("d3h7"))
        self.assertTrue(result["check"])
        self.assertTrue(result["capture"])
        self.assertEqual(result["material_concession_proxy"], 2)
        board = chess.Board("r2q2k1/8/8/8/8/8/8/3Q2K1 w - - 0 1")
        result = move_features(board, chess.Move.from_uci("d1d8"))
        self.assertEqual(result["material_concession_proxy"], 0)


if __name__ == "__main__":
    unittest.main()

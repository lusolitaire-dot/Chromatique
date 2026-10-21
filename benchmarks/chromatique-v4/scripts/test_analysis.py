"""Protect score orientation, paired uncertainty and incomplete-PGN rejection."""
import io
import math
import unittest

from analyze import elo, paired_stats, validate_games


class AnalysisContract(unittest.TestCase):
    def test_logistic_elo_orientation_and_boundaries(self):
        self.assertAlmostEqual(elo(0.75), 190.848501887865, places=9)
        self.assertAlmostEqual(elo(0.25), -190.848501887865, places=9)
        self.assertEqual(elo(0), "-inf")
        self.assertEqual(elo(1), "+inf")

    def test_uncertainty_uses_opening_pairs_not_independent_games(self):
        # 100 pairs won 2-0, 100 lost 0-2: unbiased pair variance = 50/199.
        result = paired_stats([0, 1] * 100)
        self.assertEqual(result["pentanomial"], [100, 0, 0, 0, 100])
        self.assertEqual(result["score"], 0.5)
        self.assertAlmostEqual(result["score_se"], math.sqrt(1 / 796), places=12)
        self.assertAlmostEqual(result["normal95_score"][0], 0.43053, places=5)

    def test_degenerate_samples_do_not_report_zero_uncertainty(self):
        result = paired_stats([0.5] * 200)
        self.assertLess(result["normal95_score"][0], 0.5)
        self.assertGreater(result["normal95_score"][1], 0.5)
        self.assertEqual(result["interval_method"], "hoeffding_degenerate_fallback")
        self.assertIsNone(result["bootstrap95_score"])

    def test_replay_scores_target_color_and_rejects_missing_partner(self):
        # Both games are legal Fool's mates. Target loses White, wins Black.
        one = '[White "Target"]\n[Black "Ref"]\n[Result "0-1"]\n[Termination "normal"]\n\n1. f3 e5 2. g4 Qh4# 0-1\n\n'
        two = one.replace('[White "Target"]', '[White "Ref"]').replace('[Black "Ref"]', '[Black "Target"]')
        result = validate_games(io.StringIO(one + two), "Target", [("f2f3", "e7e5")], book_plies=2)
        self.assertEqual(result["wdl"], [1, 0, 1])
        self.assertEqual(result["pairs"], [0.5])
        with self.assertRaisesRegex(ValueError, "pair"):
            validate_games(io.StringIO(one), "Target", [("f2f3", "e7e5")], book_plies=2)
        with self.assertRaisesRegex(ValueError, "color"):
            validate_games(io.StringIO(one + one), "Target", [("f2f3", "e7e5")], book_plies=2)
        wrong_clock = (one + two).replace('[Termination "normal"]', '[Termination "normal"]\n[TimeControl "30+0.3"]')
        with self.assertRaisesRegex(ValueError, "time control"):
            validate_games(io.StringIO(wrong_clock), "Target", [("f2f3", "e7e5")], book_plies=2, tc="5+0.05")


if __name__ == "__main__":
    unittest.main()

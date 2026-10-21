"""Guard the predeclared example selection against flattering-only selection."""
import unittest

from inspect_examples import select_examples


class ExampleSelection(unittest.TestCase):
    def test_selects_low_and_high_loss_candidates_and_excludes_mate(self):
        rows = [{"index": index, "choices": [{"material_concession_proxy": offer, "judge_loss_cp": loss}]}
                for index, offer, loss in [(7, 3, None), (8, 0, 0), (4, 2, 20),
                                          (3, 1, -4), (1, 2, 20), (2, 1, 300)]]
        self.assertEqual([r["index"] for r in select_examples(rows)], [3, 1, 2])
        self.assertEqual(select_examples(rows[:2]), [])


if __name__ == "__main__":
    unittest.main()

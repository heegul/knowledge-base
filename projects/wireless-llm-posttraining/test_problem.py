import unittest

from problem import make_splits, parse_answer, score, solve


class ProblemTests(unittest.TestCase):
    def test_solver_and_tie_break(self):
        self.assertEqual(solve([[5, 9], [8, 2], [3, 4]]), ((1, 0), 17))
        self.assertEqual(solve([[1, 1], [1, 1], [1, 1]]), ((0, 1), 2))

    def test_constraints_and_reward(self):
        rates = [[5, 9], [8, 2], [3, 4]]
        self.assertEqual(score(rates, "RB1=U1,RB2=U0")["reward"], 1)
        self.assertEqual(score(rates, "RB1=U2,RB2=U0")["reward"], 12 / 17)
        for response in ("RB1=U0,RB2=U0", "RB1=U8,RB2=U1", "The answer is RB1=U1,RB2=U0"):
            self.assertIsNone(parse_answer(response, 3))
            self.assertEqual(score(rates, response)["reward"], 0)

    def test_split_uniqueness_and_optima(self):
        splits = make_splits()
        keys = [tuple(sum(row["rates"], [])) for rows in splits.values() for row in rows]
        self.assertEqual(len(keys), len(set(keys)))
        for rows in splits.values():
            for row in rows:
                self.assertEqual(score(row["rates"], row["answer"])["optimal_rate"], row["optimal_rate"])
                self.assertTrue(score(row["rates"], row["answer"])["optimal"])


if __name__ == "__main__":
    unittest.main()

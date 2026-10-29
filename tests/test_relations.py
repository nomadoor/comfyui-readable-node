"""Tests for scripts/relations.py (positions from relations, all at once). Python standard library only.

What is checked: hard edges always hold. An equality is kept only when everything kept before it can still be solved,
and is returned otherwise. Merged variables keep their offsets exactly. The magnet keeps what no relation moves.

Usage: python3 -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = next(p for p in (HERE.parent / "skills" / "comfyui-readable-node" / "scripts", HERE.parent / "skill" / "scripts")
               if p.is_dir())
sys.path.insert(0, str(SCRIPTS))
import relations as R  # noqa: E402


class TestProblem(unittest.TestCase):
    def test_magnet_keeps_what_nothing_moves(self):
        p = R.Problem()
        a, b = p.var("a", 0), p.var("b", 500)
        p.hard(a, b, 100)
        y = p.solve()
        self.assertEqual((y[a], y[b]), (0, 500))

    def test_hard_edge_pushes(self):
        p = R.Problem()
        a, b = p.var("a", 0), p.var("b", 50)
        p.hard(a, b, 100)
        y = p.solve()
        self.assertGreaterEqual(y[b] - y[a], 100)
        self.assertEqual(abs(y[a] - 0) + abs(y[b] - 50), 50)   # one of them moved the 50 that was missing

    def test_equality_is_exact(self):
        p = R.Problem()
        a, b = p.var("a", 0), p.var("b", 37)
        kept, _ = p.try_equal(a, b, 12.4)
        self.assertTrue(kept)
        y = p.solve()
        self.assertAlmostEqual(y[b] - y[a], 12.4)

    def test_conflicting_equality_is_returned(self):
        p = R.Problem()
        a, b, c = p.var("a", 0), p.var("b", 10), p.var("c", 20)
        self.assertTrue(p.try_equal(a, b, 10, "line 3")[0])
        self.assertTrue(p.try_equal(b, c, 10, "line 4")[0])
        kept, why = p.try_equal(a, c, 50, "line 5")
        self.assertFalse(kept)
        self.assertIn("line", why)
        y = p.solve()
        self.assertAlmostEqual(y[c] - y[a], 20)

    def test_equality_against_a_hard_edge_is_returned(self):
        p = R.Problem()
        a, b = p.var("a", 0), p.var("b", 200)
        p.hard(a, b, 100)          # b stays at least 100 below a
        kept, _ = p.try_equal(a, b, 0)
        self.assertFalse(kept)     # level with a would put b on a
        y = p.solve()
        self.assertGreaterEqual(y[b] - y[a], 100)

    def test_merged_blocks_with_edges_both_ways_are_refused(self):
        # a above c, d above b; a = b and c = d would make the blocks point at each other
        p = R.Problem()
        a, b, c, d = (p.var(x, v) for x, v in (("a", 0), ("b", 0), ("c", 100), ("d", -100)))
        p.hard(a, c, 50)
        p.hard(d, b, 50)
        self.assertTrue(p.try_equal(a, b, 0)[0])
        self.assertFalse(p.try_equal(c, d, 0)[0])
        y = p.solve()
        self.assertGreaterEqual(y[c] - y[a], 50)
        self.assertGreaterEqual(y[b] - y[d], 50)

    def test_try_edge(self):
        p = R.Problem()
        a, b = p.var("a", 0), p.var("b", 100)
        p.hard(a, b, 50)
        self.assertFalse(p.try_edge(b, a, 10)[0])   # a below b would be a cycle
        self.assertTrue(p.try_edge(a, b, 150)[0])
        y = p.solve()
        self.assertGreaterEqual(y[b] - y[a], 150)

    def test_wish(self):
        p = R.Problem()
        a = p.var("a", 0)
        r = p.var("r")             # no magnet: only the wish places it
        p.wish(r, 0, a, 30)
        y = p.solve()
        self.assertEqual(y[r] - y[a], 30)

    def test_same_problem_same_result(self):
        def build():
            p = R.Problem()
            vs = [p.var(str(i), (i * 37) % 200) for i in range(12)]
            for i in range(11):
                p.hard(vs[i], vs[i + 1], 20)
            p.try_equal(vs[0], vs[5], 120)
            return p.solve()
        self.assertEqual(build(), build())


if __name__ == "__main__":
    unittest.main()

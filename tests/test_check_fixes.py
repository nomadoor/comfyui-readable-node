"""Tests that what a check tells the agent to write can be written and makes that check line go away
(the check-fix tests). Python standard library only.

Each test builds the form a check names, writes the plan line the check's own words give, runs the layout again, and
checks that the layout does not stop and that the line is gone. A check that names a plan line gets a test here when it
is added or changed.

Usage: python3 -m unittest discover -s tests
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import test_canvas as T

C, G = T.C, T.G


class CheckFixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp())
        C.run_cmd(C.Work(cls.base), f"open {T.SUBJECT} {T.OI}")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base)

    def setUp(self):
        C.HAND_PLACING_FOR_TESTS = False   # as the agent writes plans: no numbers, no move
        self.dir = Path(tempfile.mkdtemp())
        for name in ("object_info.json", "src.flat.json", "canvas.config.json"):
            shutil.copy(self.base / name, self.dir / name)
        self.do("new t")

    def tearDown(self):
        C.HAND_PLACING_FOR_TESTS = True
        shutil.rmtree(self.dir)

    def do(self, line):
        return C.run_cmd(C.Work(self.dir), line)

    def layout(self, lines):
        f = self.dir / "plan.txt"
        f.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.do(f"layout {f}")

    def cv(self):
        return C.Work(self.dir).current()

    def check_lines(self, start):
        return [x for x in C.full_check(self.cv())[0] if start in x]

    def test_write_level_from_one_move(self):
        # "slanted wire that one move makes horizontal: … (write level A.out B.in [move X])"
        self.do("copy 13 8 9 27 10")
        self.do("link 13.0 8.samples 8.0 9.images 10.0 8.vae 27.0 13.latent_image")
        plan = ["put 13 origin", "put 8 right 13 wire", "put 9 right 8 bottom"]
        self.layout(plan)
        named = self.check_lines("one move makes horizontal")
        self.assertTrue(named, "the check names the slanted wire")
        fix = re.search(r"write (level [^)]+)\)", named[0]).group(1)
        self.layout(plan + [fix])
        self.assertFalse(self.check_lines("one move makes horizontal: 8.IMAGE"))

    def test_write_gap_wide_where_wires_cross(self):
        # "wires cross N times in the gap between A and B: write `gap wide` on the line that places B right of A"
        self.do("copy 25 22 16 17 27 13")
        self.do("link 25.0 13.noise 22.0 13.guider 16.0 13.sampler 17.0 13.sigmas 27.0 13.latent_image")
        plan = ["put 27 origin", "stack 27 17 16 22 25", "put 13 right 22 top"]
        self.layout(plan)
        named = self.check_lines("times in the gap between")
        self.assertTrue(named, "the check names the gap")
        m = re.search(r"between (\S+) and (\S+):", named[0])
        self.layout(plan[:-1] + [plan[-1] + " gap wide"])
        self.assertFalse(self.check_lines(f"times in the gap between {m.group(1)} and {m.group(2)}"))

    def test_write_rail_move_for_a_raised_loader(self):
        # "raising Reroute right of a loader …: write rail … move <its unit> to …"
        self.do("copy 10 13 8 9 27")
        self.do("link 13.0 8.samples 10.0 8.vae 8.0 9.images 27.0 13.latent_image")
        plan = ["put 13 origin", "put 8 right 13 wire", "put 9 right 8 wire", "put 27 left 13 bottom",
                "put 10 below 27", "rail 10.VAE above 13 to 8.vae"]
        self.layout(plan)
        named = self.check_lines("raising Reroute right of a loader")
        self.assertTrue(named, "the check names the loader")
        self.layout(plan[:-1] + ["rail 10.VAE above 13 move 10 to 8.vae"])
        self.assertFalse(self.check_lines("raising Reroute right of a loader"))


    def test_write_below_right_for_a_left_aligned_column(self):
        # "stacked nodes aligned on their left edges, not their right: … (place the lower one with put … below the other)"
        self.do("copy 42 26 22")
        self.do("link 42.0 26.conditioning 26.0 22.conditioning")
        out = self.layout(["put 42 origin", "put 26 below 42 left"])
        self.assertTrue(self.check_lines("stacked nodes aligned on their left edges"), "the check names the pair")
        self.assertTrue([x for x in out if x.startswith("left to fix") and "aligned on their left" in x], "a rule's violation")
        self.layout(["put 42 origin", "put 26 below 42"])
        self.assertFalse(self.check_lines("stacked nodes aligned on their left edges"))


if __name__ == "__main__":
    unittest.main()

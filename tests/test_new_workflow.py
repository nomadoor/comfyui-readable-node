"""Tests for building a new workflow, with no original (`open new <object_info>`). Python standard library only.

What is checked: the steps SKILL.md gives for a new workflow run to the end (build, layout, export, models, review,
report, finish), and the moves that only work on an original say so instead of failing on a missing file.

Usage: python3 -m unittest discover -s tests
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = next(p for p in (HERE.parent / "skills" / "comfyui-readable-node" / "scripts", HERE.parent / "skill" / "scripts")
               if p.is_dir())
sys.path.insert(0, str(SCRIPTS))
import canvas as C  # noqa: E402

FIX = HERE / "fixtures"


class NewWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.w = self.out / "w"

    def tearDown(self):
        shutil.rmtree(self.out)

    def do(self, line):
        return C.run_cmd(C.Work(self.w), line)

    def build(self):
        self.do(f"open new {FIX / 'object_info.json'}")
        self.do("new t")
        self.do("add UNETLoader unet")
        self.do("add ModelSamplingFlux msf")
        self.do("link unet.MODEL msf.model")

    def test_open_new_starts_without_an_original(self):
        out = self.do(f"open new {FIX / 'object_info.json'}")
        self.assertTrue(any("no original" in x for x in out), out)
        self.assertEqual(self.do("new t"), ["made canvas t"])

    def test_a_new_workflow_runs_to_finish(self):
        self.build()
        plan = self.w / "layout.txt"
        plan.write_text("put unet origin\nput msf right unet wire\n", encoding="utf-8")
        self.do(f"layout {plan}")
        self.do(f"export {self.out / 't.json'}")
        models = self.do("models")
        self.assertTrue(any("draft of the model Note text" in x for x in models), models)
        _, ids = C.Work(self.w).current().workflow()
        review = self.w / "review_t.md"
        review.write_text("# Review: t\n\n| rule | nodes | what to change | answer |\n|---|---|---|---|\n"
                          f"| Rails: a single value is wired directly | {min(ids.values())} | wire it directly | fixed |\n",
                          encoding="utf-8")
        self.do(f"review {review}")
        self.do(f"report {self.out / 'report.html'} en")
        self.do("finish")
        self.assertFalse(self.w.exists())
        self.assertTrue((self.out / "t.json").exists() and (self.out / "report.html").exists())

    def test_moves_for_an_original_say_there_is_none(self):
        self.build()
        for line in ("copy 12", "src all", "diff"):
            with self.assertRaises(C.Stop) as e:
                self.do(line)
            self.assertIn("no original", str(e.exception), line)

    def test_open_stops_in_a_working_folder_already_used(self):
        # one working folder is one job: opening another workflow over canvases (and their export, review and report
        # records) would let finish take the old records for the new job
        self.build()
        for line in (f"open new {FIX / 'object_info.json'}", f"open {FIX / 'flux_t2i.json'} {FIX / 'object_info.json'}"):
            with self.assertRaises(C.Stop) as e:
                self.do(line)
            self.assertIn("another working folder", str(e.exception), line)
        self.assertEqual(C.Work(self.w).names(), ["t"])

    def test_open_again_before_any_canvas(self):
        # nothing built yet: opening again (another object_info, the original after all) is fine
        self.do(f"open new {FIX / 'object_info.json'}")
        out = self.do(f"open {FIX / 'flux_t2i.json'} {FIX / 'object_info.json'}")
        self.assertTrue(any(x.startswith("read:") for x in out), out)

    def test_open_still_needs_both_files_for_an_original(self):
        with self.assertRaises(C.Stop) as e:
            self.do(f"open {FIX / 'flux_t2i.json'}")
        self.assertIn("open new", str(e.exception))


if __name__ == "__main__":
    unittest.main()

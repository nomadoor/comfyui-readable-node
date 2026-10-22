"""Tests for `canvas finish` (deleting the working folder). Python standard library only.

What is checked: finish stops and deletes nothing until every canvas is exported and the report page is up to date
(compared by content, so undo cannot fool it). It deletes only the files the canvas knows, never a file outside the
working folder, and leaves the folder when something it does not know is inside. CANVAS_KEEP_WORK=1 deletes nothing.

Usage: python3 -m unittest discover -s tests
"""
import os
import shutil
import subprocess
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


class FinishTest(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.w = self.out / "w"
        self.do(f"open {FIX / 'flux_t2i.json'} {FIX / 'object_info.json'}")
        self.do("new t")
        self.do("copy 12 30")
        (self.w / "understanding.md").write_text("understanding", encoding="utf-8")
        (self.w / "note_a.md").write_text("# A\ntext", encoding="utf-8")
        (self.out / "outside.md").write_text("# B\ntext", encoding="utf-8")
        (self.w / "layout.txt").write_text("put 12 origin\nput 30 right 12\n", encoding="utf-8")
        self.do(f"layout {self.w / 'layout.txt'}")
        self.do(f"note {self.w / 'note_a.md'} below 12")
        self.do(f"note {self.out / 'outside.md'} below 30")

    def tearDown(self):
        os.environ.pop("CANVAS_KEEP_WORK", None)
        shutil.rmtree(self.out)

    def do(self, line):
        return C.run_cmd(C.Work(self.w), line)

    def export_and_report(self):
        self.do(f"export {self.out / 't.json'}")
        self.do(f"report {self.out / 'report.html'} en")

    def test_stops_before_export_and_report(self):
        with self.assertRaises(C.Stop) as e:
            self.do("finish")
        self.assertIn("Nothing is deleted", str(e.exception))
        self.assertTrue((self.w / "src.flat.json").exists())

    def test_deletes_the_working_folder_and_keeps_the_outputs(self):
        self.export_and_report()
        out = self.do("finish")
        self.assertTrue(out[0].startswith("deleted the working folder"), out)
        self.assertFalse(self.w.exists())
        for f in ("t.json", "report.html", "outside.md"):
            self.assertTrue((self.out / f).exists(), f)
        self.assertTrue(any("outside the working folder" in x and "outside.md" in x for x in out), out)

    def test_a_change_after_export_stops_it_even_after_undo(self):
        self.export_and_report()
        self.do("move 30 0 40")
        self.do("undo")
        self.do("move 30 0 80")
        with self.assertRaises(C.Stop) as e:
            self.do("finish")
        msg = str(e.exception)
        self.assertIn("changed since it was exported", msg)
        self.assertIn("report page is older", msg)
        self.assertIn("`report <html> <language code>`", msg)

    def test_a_missing_export_or_report_page_stops_it(self):
        self.export_and_report()
        (self.out / "t.json").unlink()
        (self.out / "report.html").write_text("changed", encoding="utf-8")
        with self.assertRaises(C.Stop) as e:
            self.do("finish")
        msg = str(e.exception)
        self.assertIn("exported file of canvas t is missing or was changed", msg)
        self.assertIn("report page is missing or was changed", msg)
        self.assertTrue((self.w / "src.flat.json").exists())

    def test_unknown_files_and_the_folder_are_left(self):
        self.export_and_report()
        (self.w / "mine.txt").write_text("x", encoding="utf-8")
        out = self.do("finish")
        self.assertIn("mine.txt", out[0]); self.assertIn("rmdir", out[0])
        self.assertTrue((self.w / "mine.txt").exists())
        self.assertFalse((self.w / "src.flat.json").exists())
        self.assertFalse((self.w / "canvas").exists())

    def test_keep_work_deletes_nothing(self):
        self.export_and_report()
        os.environ["CANVAS_KEEP_WORK"] = "1"
        out = self.do("finish")
        self.assertTrue(out[0].startswith("finished.") and "CANVAS_KEEP_WORK=1 is set" in out[0])
        self.assertIn("the report page is up to date", out[0])
        self.assertTrue((self.w / "src.flat.json").exists())
        self.assertTrue((self.w / "note_a.md").exists())

    def test_a_note_written_in_a_layout_plan_is_deleted(self):
        (self.w / "note_b.md").write_text("# B\ntext", encoding="utf-8")
        (self.w / "layout2.txt").write_text(f"put 12 origin\nput 30 right 12\nnote {self.w / 'note_b.md'} below 12\n",
                                            encoding="utf-8")
        self.do(f"layout {self.w / 'layout2.txt'}")
        self.export_and_report()
        self.do("finish")
        self.assertFalse(self.w.exists())

    def test_a_stopped_layout_is_not_remembered(self):
        bad = self.w / "bad.txt"
        bad.write_text("put 30 right nothing\n", encoding="utf-8")
        with self.assertRaises(C.Stop):
            self.do(f"layout {bad}")
        self.assertNotIn(os.path.abspath(bad), C.Work(self.w).cfg.get("consumed") or [])

    def test_a_plan_given_to_run_is_deleted(self):
        plan = self.w / "build.txt"
        plan.write_text("color purple 12\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "canvas.py"), "--dir", str(self.w), "run", str(plan)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.export_and_report()
        self.do("finish")
        self.assertFalse(self.w.exists())


if __name__ == "__main__":
    unittest.main()

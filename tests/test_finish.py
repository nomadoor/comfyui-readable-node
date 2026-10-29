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

C.HAND_PLACING_FOR_TESTS = True   # the tests build odd shapes with move and numeric gaps

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
        self.do(f"note {self.w / 'note_a.md'} left 12")
        self.do(f"note {self.out / 'outside.md'} right 30")

    def tearDown(self):
        os.environ.pop("CANVAS_KEEP_WORK", None)
        shutil.rmtree(self.out)

    def do(self, line):
        return C.run_cmd(C.Work(self.w), line)

    def first_exported(self):
        """The smallest node number of the exported workflow."""
        _, ids = C.Work(self.w).current().workflow()
        return min(ids.values())

    def review(self, answer="fixed"):
        f = self.w / "review_t.md"
        f.write_text("# Review: t\n\n| rule | nodes | what to change | answer |\n|---|---|---|---|\n"
                     f"| Rails: a single value is wired directly | {self.first_exported()} | wire it directly | {answer} |\n", encoding="utf-8")
        return self.do(f"review {f}")

    def export_and_report(self):
        self.do(f"export {self.out / 't.json'}")
        self.review()
        self.do(f"report {self.out / 'report.html'} en")

    def test_stops_without_review(self):
        self.do(f"export {self.out / 't.json'}")
        self.do(f"report {self.out / 'report.html'} en")
        with self.assertRaises(C.Stop) as e:
            self.do("finish")
        self.assertIn("has no review", str(e.exception))

    def test_fast_needs_no_review_and_no_report(self):
        self.do(f"export {self.out / 't.json'}")
        self.do("finish fast")
        self.assertFalse(self.w.exists())

    def test_fast_still_needs_the_export(self):
        with self.assertRaises(C.Stop) as e:
            self.do("finish fast")
        self.assertIn("never exported", str(e.exception))

    def test_stops_on_a_review_row_without_answer(self):
        self.do(f"export {self.out / 't.json'}")
        out = self.review(answer="")
        self.assertTrue([x for x in out if "1 without an answer" in x], out)
        self.do(f"report {self.out / 'report.html'} en")
        with self.assertRaises(C.Stop) as e:
            self.do("finish")
        self.assertIn("review rows have no answer", str(e.exception))

    def test_review_shows_canvas_ids_and_reaches_the_report(self):
        self.do(f"export {self.out / 't.json'}")
        out = self.review()
        cv = C.Work(self.w).current()
        _, ids = cv.workflow()
        exported_one = next(k for k, v in ids.items() if v == self.first_exported())
        self.assertTrue([x for x in out if f"— {exported_one} —" in x], out)
        self.do(f"report {self.out / 'report.html'} en")
        self.assertIn("a single value is wired directly", (self.out / "report.html").read_text(encoding="utf-8"))
        self.do("finish")
        self.assertFalse(self.w.exists())   # the review file and the review picture are deleted with the working folder

    def test_review_picture_is_deleted_with_the_folder(self):
        self.do(f"export {self.out / 't.json'}")
        self.do(f"render {self.w / 'review_t.png'} export")
        f = self.w / "review_t.md"
        f.write_text("# Review: t\n\nNo findings.\n\nChecked: readable-form 30 rules\n", encoding="utf-8")
        self.do(f"review {f}")
        self.do(f"report {self.out / 'report.html'} en")
        self.do("finish")
        self.assertFalse(self.w.exists())

    def test_fixed_needs_a_change_since_the_review_picture(self):
        self.do(f"export {self.out / 't.json'}")
        self.do(f"render {self.w / 'review_t.png'} export")
        with self.assertRaises(C.Stop) as e:
            self.review(answer="fixed")
        self.assertIn("same as in the picture", str(e.exception))
        self.review(answer='left: "Load CLIP in the column of the text encoders" applies')   # leaving it needs no change

    def test_stale_review_stops_finish(self):
        self.do(f"export {self.out / 't.json'}")
        self.review()
        (self.w / "layout.txt").write_text("put 12 origin\nput 30 below 12\n", encoding="utf-8")
        self.do(f"layout {self.w / 'layout.txt'}")
        self.do(f"export {self.out / 't.json'}")
        self.do(f"report {self.out / 'report.html'} en")
        with self.assertRaises(C.Stop) as e:
            self.do("finish")
        self.assertIn("changed after its review was registered", str(e.exception))

    def test_new_from_does_not_copy_the_review(self):
        self.do(f"export {self.out / 't.json'}")
        self.review()
        self.do("new u from t")
        self.assertIsNone(C.Work(self.w).current().s.get("review"))

    def test_review_row_with_the_answer_after_an_empty_cell(self):
        self.do(f"export {self.out / 't.json'}")
        f = self.w / "review_t.md"
        f.write_text("| rule | nodes | what to change | answer |\n|---|---|---|---|\n"
                     "| readable-form.md: Left to right. | 1 | swap them | | left: “Load CLIP in the column of the text encoders” |\n", encoding="utf-8")
        self.do(f"review {f}")
        row = C.Work(self.w).current().s["review"]["rows"][0]
        self.assertEqual((row["rule"], row["nodes"], row["change"], row["answer"]),
                         ("readable-form.md: Left to right.", "1", "swap them", "left: “Load CLIP in the column of the text encoders”"))

    def test_review_rows_with_a_pipe_in_the_rule_and_a_missing_header(self):
        self.do(f"export {self.out / 't.json'}")
        f = self.w / "review_t.md"
        f.write_text("| readable-form: use `put … right|left` | 1 | put it right | left: no room |\n", encoding="utf-8")
        with self.assertRaises(C.Stop) as e:
            self.do(f"review {f}")
        self.assertIn("no header row", str(e.exception))
        f.write_text("| rule | nodes | what to change | answer |\n|---|---|---|---|\n"
                     "| readable-form: use `put … right|left` | 1 99 | put it right | left: 「Load CLIP in the column of the text encoders」 |\n", encoding="utf-8")
        out = self.do(f"review {f}")
        self.assertTrue([x for x in out if "put … right|left" in x], out)
        self.assertTrue([x for x in out if "not a node of the exported workflow" in x and "99" in x], out)

    def test_order_sets_the_report_tabs(self):
        self.do("new u")
        with self.assertRaises(C.Stop) as e:
            self.do("order u")
        self.assertIn("missing: t", str(e.exception))
        self.do("order u t")
        self.assertEqual(C._report_order(C.Work(self.w)), ["u", "t"])
        self.do("order m/u m/t")
        self.assertEqual(C._report_order(C.Work(self.w)), ["u", "t"])
        self.assertEqual(C.Work(self.w).cfg["tab_group"], {"u": "m", "t": "m"})

    def test_bad_forms_are_reported_and_stop_nothing(self):
        # the rules' Bad forms are listed first by layout, and export still writes the workflow (correction 980)
        self.do(f"layout {self.w / 'layout.txt'}")
        (self.w / "bad.txt").write_text("put 12 origin\nput 30 origin\n", encoding="utf-8")
        out = self.do(f"layout {self.w / 'bad.txt'}")
        self.assertTrue(any("violations of the skill's rules" in x for x in out), out)
        self.assertTrue(C.hard_problems(C.Canvas(C.Work(self.w), "t")))
        self.do(f"export {self.out / 't.json'}")
        self.assertTrue((self.out / "t.json").exists())

    def test_left_needs_a_quoted_rule_line_of_its_own(self):
        self.do(f"export {self.out / 't.json'}")
        f = self.w / "review_t.md"
        head = "| rule | nodes | what to change | answer |\n|---|---|---|---|\n"
        for rows, word in (("| r | 1 | a | left: there is no room |\n", "quoted line"),
                           ('| r | 1 | a | left: "a line that is in no rule file" |\n', "quoted line"),
                           ('| r | 1 | a | left: "Load CLIP in the column of the text encoders" |\n| s | 1 | b | left: "Load CLIP in the column of the text encoders" |\n',
                            "same words")):
            f.write_text(head + rows, encoding="utf-8")
            with self.assertRaises(C.Stop) as e:
                self.do(f"review {f}")
            self.assertIn(word, str(e.exception))

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
        (self.w / "layout2.txt").write_text(f"put 12 origin\nput 30 right 12\nnote {self.w / 'note_b.md'} left 12\n",
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

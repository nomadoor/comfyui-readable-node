"""Tests for the walkthrough (`canvas walk` and what the report page gets). Python standard library only.

What is checked: a walkthrough file is read into parts (ids, block:, group:); unknown names, a node in two parts, a Note
id, a part without text and a second "# " line stop it; nodes in no part are named; the wires and Reroutes to light are
found through Reroutes; a part emptied by rm is left out of the page; the report page carries it; `new ... from` does
not copy it.

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

sys.path.insert(0, str(HERE))
from test_canvas import report_data  # noqa: E402

FIX = HERE / "fixtures"

WALK = """# Flux text to image.

## Model
nodes: 12 30
Loads the model.

## Text
nodes: 11 6
Encodes the prompt.

## Generate and save
nodes: 22 13 8 9 10 26 27
Samples, decodes and saves.
"""


class WalkTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.w = self.d / "w"
        self.do(f"open {FIX / 'flux_t2i.json'} {FIX / 'object_info.json'}")
        self.do("new t")
        self.do("copy 12 11 10 30 6 26 22 13 8 9 27")
        self.do("link 12.0 30.model 11.0 6.clip 30.0 22.model 6.0 26.conditioning 26.0 22.conditioning "
                "22.0 13.guider 13.0 8.samples 10.0 8.vae 8.0 9.images 27.0 13.latent_image")
        self.do("row 12 30 22 13 8 9")
        self.do("put 11 below 12")
        self.do("put 6 right 11")
        self.do("put 26 right 6")
        self.do("put 10 below 11")
        self.do("put 27 below 26")

    def tearDown(self):
        shutil.rmtree(self.d)

    def do(self, line):
        return C.run_cmd(C.Work(self.w), line)

    def walk(self, text):
        f = self.w / "walk_t.md"
        f.write_text(text, encoding="utf-8")
        return self.do(f"walk {f}")

    def test_reads_parts(self):
        out = self.walk(WALK)
        self.assertTrue(any(x.startswith("walkthrough: 3 parts") for x in out), out)
        w = C.Work(self.w).current().s["walk"]
        self.assertEqual(w["intro"], "Flux text to image.")
        self.assertEqual([p["title"] for p in w["parts"]], ["Model", "Text", "Generate and save"])
        self.assertEqual(w["parts"][1]["ids"], ["11", "6"])
        self.assertEqual(w["parts"][1]["text"], "Encodes the prompt.")

    def test_unknown_node_and_two_parts_stop(self):
        with self.assertRaises(C.Stop):
            self.walk(WALK.replace("nodes: 12 30", "nodes: 12 30 999"))
        with self.assertRaises(C.Stop) as e:
            self.walk(WALK.replace("nodes: 11 6", "nodes: 11 6 12"))
        self.assertIn("two parts", str(e.exception))
        self.assertNotIn("walk", C.Work(self.w).current().s)

    def test_names_nodes_in_no_part(self):
        out = self.walk(WALK.replace(" 26 27", ""))
        self.assertTrue(any("in no part: 26 27" in x for x in out), out)

    def test_block_reference(self):
        self.do("block gen 22 13 8 9 10 26 27")
        self.walk(WALK.replace("nodes: 22 13 8 9 10 26 27", "nodes: block:gen"))
        self.assertEqual(len(C.Work(self.w).current().s["walk"]["parts"][2]["ids"]), 7)

    def test_group_reference(self):
        self.do('group gen 22 13 8 9 10 26 27')
        self.walk(WALK.replace("nodes: 22 13 8 9 10 26 27", "nodes: group:gen"))
        self.assertEqual(sorted(C.Work(self.w).current().s["walk"]["parts"][2]["ids"]), sorted("22 13 8 9 10 26 27".split()))
        with self.assertRaises(C.Stop):
            self.walk(WALK.replace("nodes: 22 13 8 9 10 26 27", "nodes: group:nothing"))

    def test_second_title_line_stops(self):
        with self.assertRaises(C.Stop):
            self.walk(WALK.replace("## Text", "# Text"))

    def test_part_without_text_stops(self):
        with self.assertRaises(C.Stop) as e:
            self.walk(WALK.replace("Encodes the prompt.\n", ""))
        self.assertIn("no text", str(e.exception))

    def test_note_id_in_nodes_stops(self):
        f = self.w / "hint.md"
        f.write_text("Write the prompt here.", encoding="utf-8")
        self.do(f"note {f} below 11")
        with self.assertRaises(C.Stop) as e:
            self.walk(WALK.replace("nodes: 11 6", "nodes: 11 6 hint"))
        self.assertIn("not a part of the processing", str(e.exception))

    def test_lit_and_wires_follow_reroutes(self):
        self.walk(WALK)
        self.do("rail 10.VAE below 10 to 8.vae")   # Load VAE to VAE Decode through Reroutes
        cv = C.Work(self.w).current()
        rr = [n["id"] for n in cv.s["nodes"] if n["type"] == "Reroute"]
        self.assertTrue(rr)
        gen = C.walk_view(cv)["parts"][2]   # 10 and 8 are both in it: the Reroutes between them and their wires are lit
        for r in rr:
            self.assertIn(r, gen["lit"])
        self.assertTrue(any(k.startswith(f"10|0|{rr[0]}|") for k in gen["w"]), gen["w"])
        # move 10 into the model part: the Reroutes are lit in both parts, as the wire runs between them
        self.walk(WALK.replace("nodes: 12 30", "nodes: 12 30 10").replace(" 10 26 27", " 26 27"))
        v = C.walk_view(C.Work(self.w).current())
        for r in rr:
            self.assertIn(r, v["parts"][0]["lit"])
            self.assertIn(r, v["parts"][2]["lit"])

    def test_rm_takes_the_node_out_of_its_part(self):
        self.walk(WALK)
        out = self.do("rm 30")
        self.assertEqual(C.Work(self.w).current().s["walk"]["parts"][0]["ids"], ["12"])
        out = self.do("rm 12")
        self.assertTrue(any("has no node left" in x for x in out), out)

    def test_page_leaves_out_an_emptied_part(self):
        self.walk(WALK)
        self.do("rm 12 30")
        v = C.walk_view(C.Work(self.w).current())
        self.assertEqual([p["title"] for p in v["parts"]], ["Text", "Generate and save"])
        out = self.do(f"report {self.d / 'r.html'} en")
        self.assertTrue(any('walkthrough of t: part "Model" has no node' in x for x in out), out)

    def test_report_names_nodes_added_after_walk(self):
        self.walk(WALK)
        self.do("copy 25")
        out = self.do(f"report {self.d / 'r.html'} en")
        self.assertIn("walkthrough of t: in no part: 25", out)

    def test_new_from_does_not_carry_the_walkthrough(self):
        self.walk(WALK)
        self.do("new t2 from t")
        self.assertNotIn("walk", C.Work(self.w).current().s)

    def test_text_before_the_first_part_stops(self):
        with self.assertRaises(C.Stop):
            self.walk("Flux text to image.\n\n## Model\nnodes: 12\n")

    def test_report_page_carries_the_walkthrough(self):
        self.walk(WALK)
        page = self.d / "r.html"
        self.do(f"report {page} en")
        data = report_data(page)
        w = data["canvases"][0]["walk"]
        self.assertEqual([p["title"] for p in w["parts"]], ["Model", "Text", "Generate and save"])
        self.assertTrue(all("w" in p and "lit" in p for p in w["parts"]))
        self.assertEqual(data["chrome"]["walk"], "Walkthrough")

    def test_finish_deletes_the_walkthrough_file(self):
        self.walk(WALK)
        self.do(f"export {self.d / 't.json'}")
        self.do(f"report {self.d / 'r.html'} en")
        self.do("finish")
        self.assertFalse(self.w.exists())


if __name__ == "__main__":
    unittest.main()

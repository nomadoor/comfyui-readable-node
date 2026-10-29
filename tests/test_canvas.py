"""Tests for the canvas (scripts/canvas.py). Python standard library only.

What is checked: a command moves only what it names. Alignment arithmetic is right. A stopped command changes nothing. Commands can be undone.
The subject is a hand-made Flux text to image in fixtures/ and an object_info cut down to the nodes it uses (runs without a server).

Usage: python3 -m unittest discover -s tests
"""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
# skills/comfyui-readable-node/scripts (the published repo) or ../skill/scripts (the development folder)
SCRIPTS = next(p for p in (HERE.parent / "skills" / "comfyui-readable-node" / "scripts", HERE.parent / "skill" / "scripts")
               if p.is_dir())
sys.path.insert(0, str(SCRIPTS))
import canvas as C  # noqa: E402

C.HAND_PLACING_FOR_TESTS = True   # the tests build odd shapes with move and numeric gaps
import geometry as G  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
SUBJECT = FIX / "flux_t2i.json"
OI = FIX / "object_info.json"


def report_data(path):
    """The data the report page at path carries (the JSON inside it)."""
    text = path.read_text(encoding="utf-8")
    return json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', text, re.S).group(1).replace("<\\/", "</"))


class CanvasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp())
        C.run_cmd(C.Work(cls.base), f"open {SUBJECT} {OI}")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base)

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        for name in ("object_info.json", "src.flat.json", "canvas.config.json"):
            shutil.copy(self.base / name, self.dir / name)
        self.do("new t")
        self.do("copy 12 11 10 30 42 6 26 22 13 8 9 27")
        self.do("link 12.0 30.model 11.0 42.clip 11.0 6.clip 30.0 22.model 26.0 22.conditioning "
                "22.0 13.guider 13.0 8.samples 10.0 8.vae 8.0 9.images 27.0 13.latent_image")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def do(self, line):
        return C.run_cmd(C.Work(self.dir), line)

    def cv(self):
        return C.Work(self.dir).current()

    def rect(self, nid):
        return G.rect(self.cv().node(nid))

    def positions(self):
        return {n["id"]: n.get("pos") for n in self.cv().s["nodes"]}

    def _layout_one(self):
        plan = self.dir / "p.txt"
        plan.write_text("put 11 origin\n", encoding="utf-8")
        return self.do(f"layout {plan}")

    def test_a_clip_loader_feeding_text_encoders_stays_yellow(self):
        # correction 1014: the fixed yellow stays when the CLIP reaches a text encoder, also through a node passing it on
        self._layout_one()
        yellow = list(C.COLORS["yellow"])
        self.assertEqual([self.cv().node("11").get("color"), self.cv().node("11").get("bgcolor")], yellow)
        cv = self.cv()
        cv.s["nodes"].append({"id": "lo", "type": "ClipPass", "mode": 0, "inputs": [{"name": "clip", "type": "CLIP", "link": None}],
                              "outputs": [{"name": "CLIP", "type": "CLIP", "links": []}], "properties": {}, "widgets_values": []})
        cv.s["links"] = [l for l in cv.s["links"] if l["origin_id"] != "11"]
        cv.s["links"] += [{"id": 900, "origin_id": "11", "origin_slot": 0, "target_id": "lo", "target_input": "clip", "type": "CLIP"},
                          {"id": 901, "origin_id": "lo", "origin_slot": 0, "target_id": "42", "target_input": "clip", "type": "CLIP"}]
        cv.relink()
        cv.clip_loader_role_color()
        self.assertEqual([cv.node("11").get("color"), cv.node("11").get("bgcolor")], yellow)

    def test_a_clip_loader_feeding_no_text_encoder_loses_its_yellow(self):
        self.do("unlink 42.clip 6.clip")
        self._layout_one()
        self.assertIsNone(self.cv().node("11").get("color"))

    def test_put_right_top_moves_only_that_node(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        before = self.positions()
        self.do("put 30 right 12")
        after = self.positions()
        changed = {k for k in after if after[k] != before[k]}
        self.assertEqual(changed, {"30"})
        r12, r30 = self.rect("12"), self.rect("30")
        self.assertEqual(r30[0], r12[2] + C.H_GAP)
        self.assertEqual(r30[1], r12[1])

    def test_put_right_wire_levels_the_wire(self):
        self.do("put 12 origin")
        self.do("put 30 right 12 wire")
        cv = self.cv()
        a = cv.out_xy("12", 0)
        b = cv.in_xy("30", "model")
        self.assertLess(abs(a[1] - b[1]), 1)

    def test_put_side_by_side_levels_the_wire_by_default(self):
        # 27 goes into the last input of 13 (latent_image): tops aligned would leave the wire diagonal
        self.do("put 27 origin")
        self.do("put 13 right 27")
        cv = self.cv()
        a, b = cv.out_xy("27", 0), cv.in_xy("13", "latent_image")
        self.assertLess(abs(a[1] - b[1]), 1)
        self.assertNotEqual(self.rect("13")[1], self.rect("27")[1])
        self.do("put 13 right 27 top")
        self.assertEqual(self.rect("13")[1], self.rect("27")[1])

    def test_report_says_the_wire_was_made_horizontal(self):
        import report as R
        self.do("put 27 origin")
        self.do("put 13 right 27")
        x = C._explain(self.cv(), self.cv(), "put 13 right 27", None)
        self.assertTrue(x["wired"])
        self.assertIn("made the wire between them horizontal", R.explain(x, "en")["s"])
        x = C._explain(self.cv(), self.cv(), "put 26 right 12", None)
        self.assertIn("tops aligned", R.explain(x, "en")["s"])

    def test_put_side_by_side_without_a_wire_aligns_tops(self):
        self.do("put 12 origin")
        self.do("put 26 right 12")
        self.assertEqual(self.rect("26")[1], self.rect("12")[1])

    def test_row_levels_wired_neighbours_by_default(self):
        self.do("put 27 origin")
        self.do("row 27 13")
        cv = self.cv()
        a, b = cv.out_xy("27", 0), cv.in_xy("13", "latent_image")
        self.assertLess(abs(a[1] - b[1]), 1)

    def check_lines(self, rule):
        cv = self.cv()
        fn = next(f for n, f in C.CHECKS if n == rule)
        return fn(cv, C._CheckCtx(cv))

    def test_loader_order_reports_vae_above_model(self):
        self.do("put 12 origin")
        self.do("put 10 above 12")
        self.assertTrue(any(x.startswith("vae loader 10 is above the model loader 12") for x in self.check_lines("loader order")))
        self.do("put 10 below 12")
        self.assertEqual(self.check_lines("loader order"), [])

    def test_vae_loader_used_only_by_decode_below_the_sampler(self):
        self.do("put 13 origin")
        self.do("put 8 right 13")
        self.do("put 10 below 13")
        self.assertTrue(any(x.startswith("vae loader 10 is used only by VAE Decode and sits below the sampler 13")
                            for x in self.check_lines("VAE loader below the sampler")))
        self.do("put 10 above 8")
        self.assertEqual(self.check_lines("VAE loader below the sampler"), [])

    def test_vae_loader_check_follows_reroutes(self):
        self.do("put 13 origin")
        self.do("put 8 right 13")
        self.do("put 10 below 13")
        self.do("rail 10.VAE below 13 to 8.vae")
        self.assertTrue(any(x.startswith("vae loader 10 is used only by VAE Decode")
                            for x in self.check_lines("VAE loader below the sampler")))

    def test_node_directly_below_a_sampler(self):
        self.do("put 13 origin")
        self.do("put 8 below 13")
        self.assertTrue(any(x.startswith("8 is directly below 13 (sampler)") for x in self.check_lines("below a node that grows")))
        self.do("put 8 right 13")
        self.assertEqual(self.check_lines("below a node that grows"), [])

    def test_a_node_further_below_a_sampler_than_it_grows_is_clear(self):
        # a sampler grows by its preview area while it runs: a node further below than that is not hidden
        self.do("put 13 origin")
        self.do("put 8 below 13")
        self.do(f"move 8 0 {C.SAMPLER_GROW}")
        self.assertEqual(self.check_lines("below a node that grows"), [])
        self.do("move 8 0 -100")
        self.assertTrue(self.check_lines("below a node that grows"))

    def test_a_node_showing_an_image_does_not_grow(self):
        # the image is drawn inside the image area of its initial size, so a node may stand right below it
        self.do("add LoadImage li")
        self.do("put li origin")
        self.do("put 8 below li")
        self.assertEqual([x for x in self.check_lines("below a node that grows") if "li" in x], [])

    def test_below_keeps_left_edge_and_gap(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        r12, r11 = self.rect("12"), self.rect("11")
        self.assertEqual(r11[0], r12[0])
        self.assertEqual(r11[1], r12[3] + C.V_GAP)

    def test_align_top_does_not_move_first(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        self.do("put 42 right 11")
        self.do("move 42 0 37")
        first = self.rect("11")
        self.do("align top 11 42")
        self.assertEqual(self.rect("11"), first)
        self.assertEqual(self.rect("42")[1], first[1])

    def test_level_moves_target_only(self):
        self.do("put 12 origin")
        self.do("put 30 right 12")
        self.do("move 30 0 50")
        before = self.positions()
        self.do("level 12.MODEL 30.model")
        after = self.positions()
        self.assertEqual({k for k in after if after[k] != before[k]}, {"30"})
        cv = self.cv()
        self.assertLess(abs(cv.out_xy("12", 0)[1] - cv.in_xy("30", "model")[1]), 1)

    def test_block_moves_together(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        self.do("put 10 below 11")
        self.do("block loaders 12 11")
        before = self.positions()
        self.do("move loaders 100 20")
        after = self.positions()
        self.assertEqual({k for k in after if after[k] != before[k]}, {"12", "11"})
        self.assertEqual(after["12"][0] - before["12"][0], 100)
        self.assertEqual(after["11"][1] - before["11"][1], 20)

    def test_stop_changes_nothing(self):
        self.do("put 12 origin")
        state = self.cv().s
        hist = len(list(self.cv().hist.glob("*.json")))
        with self.assertRaises(C.Stop):
            self.do("put 26 right 12 wire")   # no wire between 12 and 26
        self.assertEqual(self.cv().s, state)
        self.assertEqual(len(list(self.cv().hist.glob("*.json"))), hist)

    def test_undo_restores(self):
        self.do("put 12 origin")
        before = self.positions()
        self.do("put 30 right 12")
        self.do("undo")
        self.assertEqual(self.positions(), before)

    def test_link_replaces_existing_input(self):
        self.do("link 6.0 22.conditioning")
        ls = [l for l in self.cv().s["links"] if l["target_id"] == "22" and l["target_input"] == "conditioning"]
        self.assertEqual(len(ls), 1)
        self.assertEqual(ls[0]["origin_id"], "6")

    def test_rail_is_horizontal_between_reroutes(self):
        self.do("row 10 13 8 9")
        self.do("put 12 above 10")
        self.do("rail 10.VAE above 12 to 8.vae")
        cv = self.cv()
        rr = [n for n in cv.s["nodes"] if n["type"] == "Reroute"]
        self.assertEqual(len(rr), 2)
        ys = {n["pos"][1] for n in rr}
        self.assertEqual(len(ys), 1)
        into8 = next(l for l in cv.s["links"] if l["target_id"] == "8" and l["target_input"] == "vae")
        self.assertIn(into8["origin_id"], {n["id"] for n in rr})

    def test_group_follows_members(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        self.do("group g 12 11")
        g1 = self.cv().s["groups"][0]["bounding"]
        r = self.rect("12")
        self.assertEqual(g1[0], r[0] - C.PAD_L)
        self.assertEqual(g1[1], r[1] - C.PAD_T)
        self.do("move 12 11 50 0")
        self.assertEqual(self.cv().s["groups"][0]["bounding"][0], g1[0] + 50)

    def test_autogrow_input_with_dot(self):
        self.do("copy 34 35")
        self.do("add ComfyMathExpression m")
        self.do("link 34.INT m.values.a 35.INT m.values.b 34.INT m.values.c")
        names = [i["name"] for i in self.cv().node("m")["inputs"] if not i.get("widget")]
        self.assertEqual(names[:3], ["values.a", "values.b", "values.c"])

    def test_autogrow_node_is_sized_for_three_connected(self):
        # an Autogrow input gets the height of three connected inputs and the empty one after them from the start
        import nodesize as N
        info = {"input": {"required": {"clip": ["CLIP", {}], "images": ["COMFY_AUTOGROW_V3", {"template": {
            "input": {"required": {"image": ["IMAGE", {}]}}, "names": [f"image_{k}" for k in range(1, 17)], "min": 0}}]}},
            "output": ["CONDITIONING"], "output_name": ["CONDITIONING"]}
        n = {"type": "T", "inputs": [{"name": "clip", "type": "CLIP"}, {"name": "images.image_1", "type": "IMAGE"}],
             "outputs": [{"name": "CONDITIONING"}]}
        one = N.default_size({**n, "type": "U", "inputs": n["inputs"][:1]}, {"U": {**info, "input": {"required": {"clip": ["CLIP", {}]}}}})
        self.assertEqual(N.default_size(n, {"T": info})[1] - one[1], 4 * 20)   # clip + four image rows vs clip alone

    def test_set_control_after_generate_alias(self):
        self.do("add PrimitiveInt s")
        self.do("set s control_after_generate=randomize")
        self.assertEqual(self.cv().node("s")["widgets_values"][1], "randomize")

    def _reroutes(self):
        return [n for n in self.cv().s["nodes"] if n["type"] == "Reroute"]

    def test_auto_rail_keeps_the_output_height_when_clear(self):
        self.do("put 10 origin")
        self.do("put 13 below 10")
        self.do("put 8 right 10 gap 400")
        out = self.do("rail 10.VAE to 8.vae")
        self.assertTrue([x for x in out if "at the output height" in x], out)

    def test_auto_tool_rail_runs_above_the_eye_line(self):
        # the sampler 13 stands between the vae loader and VAE Decode on one row: the vae rail goes above the sampler
        self.do("row 10 13 8 9")
        self.do("rail 10.VAE to 8.vae")
        rr = sorted(self._reroutes(), key=lambda n: n["pos"][0])
        self.assertEqual(len(rr), 2)
        r13 = self.rect("13")
        self.assertLessEqual(G.rect(rr[0])[3], r13[1] - C.V_GAP + C.REROUTE_H / 2)
        # raising Reroute: left edge on the left edge of the next column; lowering Reroute: right edge on the right edge of the column left of 8
        self.assertEqual(G.rect(rr[0])[0], r13[0])
        self.assertEqual(G.rect(rr[1])[2], r13[2])

    def test_auto_product_rail_runs_below_the_eye_line(self):
        # an image rail passing a sampler goes below it, clear of its bottom edge
        self.do("row 8 13 9")
        self.do("rail 8.IMAGE to 9.images")
        rr = self._reroutes()
        self.assertTrue(rr)
        self.assertGreaterEqual(min(G.rect(n)[1] for n in rr) + C.REROUTE_H / 2, self.rect("13")[3] + C.LANE_CLEAR_ABOVE - 1)

    def test_raised_rail_reroute_is_not_idle(self):
        self.do("row 10 13 8 9")
        self.do("put 12 above 10")
        self.do("rail 10.VAE above 12 to 8.vae")
        lines, _ = C.full_check(self.cv())
        self.assertFalse([x for x in lines if x.startswith("Reroute doing nothing")])

    def test_new_from_copies_state(self):
        self.do("put 12 origin")
        self.do("new t2 from t")
        cv = self.cv()
        self.assertEqual(cv.name, "t2")
        self.assertEqual(cv.node("12")["pos"], C.Work(self.dir).current().node("12")["pos"])
        self.assertEqual(len(cv.s["links"]), 10)

    def test_rails_at_same_height_are_reported(self):
        self.do("row 10 13 8 9")
        self.do("put 12 above 10")
        self.do("put 11 below 10")
        self.do("rail 10.VAE above 12 to 8.vae")
        self.do("link 11.CLIP 6.clip")
        self.do("put 6 right 9")
        self.do("rail 11.CLIP above 12 to 6.clip")
        lines, _ = C.full_check(self.cv())
        self.assertFalse([x for x in lines if x.startswith("rails too close")])   # the second rail shifts automatically
        ys = sorted({round(y) for y, _, _, _ in C.rail_spans(self.cv())})
        self.assertGreaterEqual(ys[-1] - ys[0], C.P["RAIL_GAP"])

    def test_rails_from_two_outputs_of_one_node_are_two_rails(self):
        # two rails from SamplerCustomAdvanced (output and denoised_output) laid at the same height must be reported
        self.do("put 13 origin")
        self.do("add VAEDecode n1")
        self.do("link 10.VAE n1.vae 13.1 n1.samples")
        cv = self.cv()

        def reroute(rid, x):
            cv.s["nodes"].append({"id": rid, "type": "Reroute", "mode": 0, "pos": [x, -200], "size": [C.REROUTE_W, C.REROUTE_H],
                                  "inputs": [{"name": "", "type": "*", "link": None}], "outputs": [{"name": "", "type": "*", "links": []}]})
        for rid, x in (("ra", 400), ("rb", 900), ("rc", 450), ("rd", 950)):
            reroute(rid, x)
        cv.add_link("13", 0, "ra", "")
        cv.add_link("ra", 0, "rb", "")
        cv.add_link("13", 1, "rc", "")
        cv.add_link("rc", 0, "rd", "")
        lines = next(f for n, f in C.CHECKS if n == "overlapping rails")(cv, C._CheckCtx(cv))
        self.assertTrue([x for x in lines if x.startswith("rails too close") and "(outputs 0 and 1)" in x], lines)
        # the rules call it Bad: it is fixed in the plan, and the line says which source to raise
        self.assertTrue([x for x in C.hard_problems(cv) if x.startswith("rails too close") and "run the lower one" in x])
        import report as R
        self.assertTrue([k for k, p, _ in R.PROBLEMS if p.match(lines[0])])

    def test_between_counts_links(self):
        f = self.write_plan(self.PLAN)
        out = self.do(f"between {f}")
        self.assertTrue(any(x.startswith("load → core") for x in out))

    def test_inputs_right_aligned_column(self):
        self.do("put 13 origin")
        self.do("move 13 2000 0")
        self.do("inputs 13")
        cv = self.cv()
        srcs = [l["origin_id"] for l in cv.s["links"] if l["target_id"] == "13"]
        rights = {round(G.rect(cv.node(i))[2]) for i in srcs}
        self.assertEqual(rights, {round(G.rect(cv.node("13"))[0] - C.H_GAP)})
        lines, _ = C.full_check(cv)
        self.assertFalse([x for x in lines if "right edges of the sources wired directly into it are not aligned" in x])

    def test_a_sampler_input_that_also_feeds_another_of_its_inputs_stands_left_of_it(self):
        # the latent from VAE Encode goes into Reference Latent as well as into the sampler: it stands left of that column
        self.do("put 13 origin")
        self.do("move 13 2000 0")
        self.do("inputs 13")
        self.do("move 27 -600 0")
        chk = next(f for n, f in C.CHECKS if n == "right edges of sampler inputs")
        cv = self.cv()
        self.assertTrue([x for x in chk(cv, C._CheckCtx(cv)) if "not aligned" in x])
        cv.add_link("27", 0, "22", "")
        self.assertFalse([x for x in chk(cv, C._CheckCtx(cv)) if "not aligned" in x])

    def test_backward_wire_is_hard(self):
        self.do("row 12 30 22")
        self.do("put 13 right 22")
        self.do("put 8 right 13")
        self.do("put 9 right 8")
        self.do("put 10 right 9")   # VAE right of the save node goes back two nodes to Decode
        lines, counts = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("backward wire (cannot be kept")])
        self.assertGreaterEqual(counts["backward wires that cannot be kept"], 1)

    def test_backward_one_node_is_kept_only_for_zero_out(self):
        # Save Image placed under VAE Decode: its wire goes back one node's width. Only Conditioning Zero Out may do that
        self.do("put 8 origin")
        self.do("put 9 below 8")
        lines, counts = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("backward wire (cannot be kept")], lines)
        self.assertFalse([x for x in lines if x.startswith("backward wire that may be allowed")])
        self.assertIn("ConditioningZeroOut", C.BACKWARD_OK_TYPES)

    def test_backward_from_an_empty_latent_only_into_a_scheduler(self):
        # Empty Latent placed under the sampler it feeds: its wire goes back one node's width into a sampler, which is not
        # one of the accepted forms (only into a scheduler, a node that outputs SIGMAS)
        self.do("put 13 origin")
        self.do("put 27 below 13")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("backward wire (cannot be kept") and "27" in x], lines)

    def test_preview_above_source(self):
        self.do("add PreviewImage p")
        self.do("link 8.IMAGE p.images")
        self.do("put 8 origin")
        self.do("put p above 8")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("PreviewImage is above its source")])

    def test_image_wire_behind_a_save_node_is_a_violation(self):
        # the wire to the second output passes behind Save Image in a row: one of them steps down instead
        self.do("add SaveImage s")
        self.do("add PreviewImage p")
        self.do("link 8.IMAGE s.images 8.IMAGE p.images")
        plan = "put 8 origin" + chr(10) + "put s right 8 top" + chr(10) + "put p right s top" + chr(10)
        self.do(f"layout {self.write_plan(plan)}")
        self.assertTrue([x for x in C.hard_problems(self.cv()) if x.startswith("wire behind a node") and x.endswith("behind s")])
        plan = "put 8 origin" + chr(10) + "put s right 8 top" + chr(10) + "move s 0 120" + chr(10) + "put p right s top" + chr(10) + "move p 0 -120" + chr(10)
        self.do(f"layout {self.write_plan(plan)}")
        self.assertFalse([x for x in C.hard_problems(self.cv()) if x.startswith("wire behind a node")])

    def test_row_spacing(self):
        self.do("put 13 origin")
        self.do("put 8 right 13 top")
        self.do("put 9 right 8 top gap 200")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("uneven spacing in a row")])

    def test_shape_copies_layout(self):
        self.do("copy 34 35")
        self.do("put 42 origin")
        self.do("put 34 right 42")
        self.do("block a 42 34")
        self.do("block b 6 35")
        self.do("shape a b below 42")
        r42, r34, r6, r35 = (self.rect(i) for i in ("42", "34", "6", "35"))
        self.assertEqual(r35[0] - r6[0], r34[0] - r42[0])
        self.assertEqual(r35[1] - r6[1], r34[1] - r42[1])
        self.assertGreater(r6[1], r42[1])

    PLAN = """
block load 12 11 10
stack 12 11 10
block core 30 42 6 26 22 13 8 9 27
row 30 22 13 8 9
put 42 below 30
put 6 below 42
put 26 right 42
put 27 below 13
put core right load top
rail 10.VAE above 12 to 8.vae
"""

    # a plan line that places by hand needs a quoted rule line; the tests that are not about that give one
    WHY = ' # why: "No node is hidden."'

    def write_plan(self, text, why=True):
        f = self.dir / "plan.txt"
        if why:
            text = "\n".join(ln + self.WHY if re.match(r"(move|gap) |rail \S+ (above|below|level|out) ", ln) and "#" not in ln else ln
                             for ln in text.split("\n"))
        f.write_text(text, encoding="utf-8")
        return f

    def test_layout_is_repeatable_and_keeps_links(self):
        f = self.write_plan(self.PLAN)
        out1 = self.do(f"layout {f}")
        pos1 = self.positions()
        links1 = {(l["origin_id"], l["target_id"], l["target_input"]) for l in self.cv().s["links"]}
        self.assertTrue(any("8" == t and "vae" == i for _, t, i in links1))
        self.do(f"layout {f}")
        self.assertEqual(self.positions(), pos1)
        self.assertTrue(any(x.startswith("violations of the skill's rules") or x.startswith("no form the rules call Bad") for x in out1))

    PACKED = """put 30 origin
stack 30 6 42 26 22 27
put 10 left 42 top gap 300
put 8 right 42 top gap 400
rail 10.VAE to 8.vae
"""

    @unittest.skip("the canvas no longer chooses rail heights, moves nodes after the plan, or holds backward wires as unkeepable (correction 1001)")
    def test_layout_rail_opens_a_lane_in_a_packed_column(self):
        # a column stands across the vae rail's run, with no clear height near the output: the column opens at the rail
        out = self.do(f"layout {self.write_plan(self.PACKED)}")
        self.assertTrue([x for x in out if "opening a lane" in x or "opened a lane" in x], out)
        self.assertTrue([x for x in out if "to open the lane" in x], out)
        cv = self.cv()
        rr = [n for n in cv.s["nodes"] if n["type"] == "Reroute"]
        y = cv.out_xy(rr[0]["id"] if rr else "10", 0)[1]
        x0, x1, last = C.rail_extent(cv, "10", ["8"])
        self.assertEqual(C.lane_blockers(cv, y, x0, x1, {"10"} | last), [])
        self.assertEqual(self.rect("30")[1] <= 0, True)   # the top of the column moved up or stayed
        lines, _ = C.full_check(cv)
        self.assertFalse([x for x in lines if x.startswith("overlap")], lines)

    def test_layout_loader_rail_has_no_raising_reroute(self):
        # a loader heads its rail: the lane opens at its output height, no Reroute lifts or lowers its output
        self.do(f"layout {self.write_plan(self.PACKED)}")
        cv = self.cv()
        y = cv.out_xy("10", 0)[1]
        rr = [n for n in cv.s["nodes"] if n["type"] == "Reroute"]
        self.assertTrue({round(cv.out_xy(n["id"], 0)[1]) for n in rr} <= {round(y)})
        if not rr:   # the lane let the direct wire through
            self.assertTrue(C.wire_clear(cv, cv.out_xy("10", 0), cv.in_xy("8", "vae"), {"10", "8"}))
        self.assertFalse([x for x in C.full_check(cv)[0] if x.startswith("raising Reroute right of a loader")])

    @unittest.skip("the canvas no longer chooses rail heights, moves nodes after the plan, or holds backward wires as unkeepable (correction 1001)")
    def test_layout_rail_moves_the_source_rather_than_a_column(self):
        # the run is blocked at the output height of VAE Decode by a stack of three; moving the source (and the sampler
        # wired level into it) moves two nodes, opening a lane would move three: the source moves, nothing lifts the rail
        self.do("add PreviewImage p")
        self.do("link 8.IMAGE p.images")
        plan = """put 13 origin
put 8 right 13
block b 27 30 42
stack 27 30 42
put b right 8 top
put 9 right b
move 9 0 120
put p below 9
rail 8.IMAGE to 9.images p.images
"""
        C.AUTO_LEVEL = False   # this test is about the rail's choice alone (the layout would level 27 → 13 first)
        try:
            out = self.do(f"layout {self.write_plan(plan)}")
        finally:
            C.AUTO_LEVEL = True
        self.assertTrue([x for x in out if "moving the source" in x], out)
        cv = self.cv()
        self.assertEqual(self.rect("27")[1], 0)   # the stack stayed
        a, b = cv.out_xy("13", 0), cv.in_xy("8", "samples")
        self.assertLess(abs(a[1] - b[1]), 1)       # the sampler moved with it: still horizontal
        y = cv.out_xy("8", 0)[1]
        for n in cv.s["nodes"]:
            if n["type"] == "Reroute":
                self.assertLess(abs(cv.out_xy(n["id"], 0)[1] - y), 1)

    def test_move_closure_keeps_a_stack(self):
        self.do("block s 12 11 10")
        self.do("stack 12 11 10")
        cv = self.cv()
        solid = [m for m in cv.s["nodes"] if cv.placed(m)]
        self.assertEqual(C.move_closure(cv, solid, {"11"}, -100, set(), []), {"12", "11", "10"})
        self.assertIsNone(C.move_closure(cv, solid, {"11"}, -100, {"10"}, []))

    def test_rail_targets_after_the_first_lowering_take_the_rail(self):
        # 6 stands next to the source: wired directly. 42 needs a Reroute. c3 could be reached by a direct wire, but it
        # stands after the rail's first lowering Reroute, so it takes the value from the rail
        self.do("add CLIPTextEncode c3")
        self.do("link 11.CLIP c3.clip")
        plan = """put 11 origin
put 6 right 11
move 6 0 150
put 27 right 6 top
put 42 right 27
put 30 right 42 top
put c3 right 30
move c3 0 -600
rail 11.CLIP to 6.clip 42.clip c3.clip
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        rr = {n["id"] for n in cv.s["nodes"] if n["type"] == "Reroute"}
        into = {l["target_id"]: l["origin_id"] for l in cv.s["links"] if l["target_input"] == "clip"}
        self.assertEqual(into["6"], "11")
        self.assertIn(into["42"], rr)
        self.assertIn(into["c3"], rr)
        self.assertNotEqual(into["c3"], into["42"])
        self.assertTrue(C.wire_clear(cv, cv.out_xy("11", 0), cv.in_xy("c3", "clip"), {"11", "c3"}))

    def test_a_lowering_reroute_stands_on_the_right_edge_of_a_column_two_frames_away(self):
        # two group frames stand between the target and the column left of it (100px apart, more than a column gap):
        # the Reroute's right edge is still on that column's right edge, inside the left frame, not on the frames' border
        self.do("put 12 origin")
        self.do("put 22 right 12")
        self.do("move 22 40 0")
        cv = self.cv()
        x0 = G.rect(cv.node("22"))[0]
        self.assertEqual(C.rail_lower_x(cv, x0, "22") + C.REROUTE_W, G.rect(cv.node("12"))[2])

    def test_rail_into_one_target_further_down_runs_at_its_input_height(self):
        # rail written below a unit, its one target further down: the rail runs at the target's input height, so the wire
        # from its Reroute into the target is horizontal (correction 1041: a Reroute stopped halfway)
        plan = """put 13 origin
put 8 right 13
put 9 right 8
put 10 left 13
move 8 0 700
move 9 0 700
rail 10.VAE below 10 to 8.vae
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        into = next(l for l in cv.s["links"] if l["target_id"] == "8" and l["target_input"] == "vae")
        self.assertEqual(cv.node(into["origin_id"])["type"], "Reroute")
        self.assertAlmostEqual(cv.out_xy(into["origin_id"], 0)[1], cv.in_xy("8", "vae")[1], delta=1)

    def test_anything_everywhere_input_saved_as_wildcard_sends_its_source_type(self):
        # a broadcaster's input link saved with the type '*' sends the type of the output it comes from (MODEL here)
        wf = {"nodes": [
            {"id": 1, "type": "UNETLoader", "mode": 0, "pos": [0, 0], "size": [300, 80], "inputs": [],
             "outputs": [{"name": "MODEL", "type": "MODEL", "links": [1]}], "widgets_values": ["m.safetensors", "default"]},
            {"id": 2, "type": "Anything Everywhere3", "mode": 0, "pos": [400, 0], "size": [200, 80],
             "inputs": [{"name": "MODEL", "type": "*", "link": 1}, {"name": "anything", "type": "*", "link": None}],
             "outputs": [], "properties": {"group_restricted": False, "color_restricted": False}},
            {"id": 3, "type": "KSampler", "mode": 0, "pos": [0, 300], "size": [300, 260],
             "inputs": [{"name": "model", "type": "MODEL", "link": None}], "outputs": [{"name": "LATENT", "type": "LATENT", "links": []}],
             "widgets_values": [1, "fixed", 20, 7, "euler", "normal", 1.0]}],
            "links": [[1, 1, 0, 2, 0, "*"]], "groups": [], "version": 0.4}
        f = self.dir / "ue.json"
        f.write_text(json.dumps(wf))
        flat, _ = C.load_source(f, json.loads(OI.read_text()))
        self.assertTrue([l for l in flat["links"] if l["target_id"] == "3" and l["target_input"] == "model" and l["origin_id"] == "1"])

    def test_export_keeps_the_canvas_numbers(self):
        # whoever reads the exported workflow (the Notes writer, the reviewer) names the nodes by the canvas's numbers;
        # a node added under a name gets a number after them
        self._ksampler()
        self.do("put 12 origin")
        self.do("put k right 12")
        wf, ids = self.cv().workflow()
        self.assertEqual(ids["12"], 12)
        self.assertGreater(ids["k"], max(int(i) for i in ids if i.isdigit()))
        self.assertEqual(wf["last_node_id"], max(n["id"] for n in wf["nodes"]))

    def _ksampler(self):
        self.do("add KSampler k")
        self.do("link 30.0 k.model 42.0 k.positive 6.0 k.negative 27.0 k.latent_image")

    def test_model_chain_end_off_the_input_column_weighs_less(self):
        # the model chain ends at the right edge of the sampler's column of sources (correction 1044); off it is a soft line
        self._ksampler()
        self.do("add ModelSamplingFlux ms")
        self.do("link 30.0 ms.model ms.0 k.model")
        self.do(f"layout {self.write_plan('put k origin' + chr(10) + 'inputs k' + chr(10))}")
        self.assertFalse([x for x in C.soft_problems(self.cv()) if x.startswith("model chain end")])
        self.do(f"layout {self.write_plan('put k origin' + chr(10) + 'inputs k' + chr(10) + 'move ms -200 0' + chr(10))}")
        self.assertTrue([x for x in C.soft_problems(self.cv()) if x.startswith("model chain end ms")])
        self.assertFalse([x for x in C.hard_problems(self.cv()) if "model chain end" in x])

    def test_model_chain_end_that_also_sends_clip_is_left_where_it_is(self):
        # a node at the end of the model chain that also feeds another node (as a LoRA's CLIP feeds CLIP Set Last Layer)
        # is not pulled to the column
        self._ksampler()
        self.do("add ModelSamplingFlux ms")
        self.do("link 30.0 ms.model ms.0 k.model ms.0 22.model")
        self.do(f"layout {self.write_plan('put k origin' + chr(10) + 'inputs k' + chr(10) + 'move ms -200 0' + chr(10))}")
        self.assertFalse([x for x in C.soft_problems(self.cv()) if x.startswith("model chain end")])

    def test_merging_node_with_no_wire_level_weighs_less(self):
        # two conditionings into one node, the node set midway so neither wire is level (correction 1044)
        self.do("add ConditioningCombine m")
        self.do("link 42.0 m.conditioning_1 6.0 m.conditioning_2")
        plan = "put 42 origin" + chr(10) + "put 6 below 42" + chr(10) + "put m right 42" + chr(10) + "move m 0 120" + chr(10)
        self.do(f"layout {self.write_plan(plan)}")
        self.assertTrue([x for x in C.soft_problems(self.cv()) if x.startswith("no wire level into m")])
        plan = "put 42 origin" + chr(10) + "put 6 below 42" + chr(10) + "put m right 42 wire" + chr(10)
        self.do(f"layout {self.write_plan(plan)}")
        self.assertFalse([x for x in C.soft_problems(self.cv()) if x.startswith("no wire level into")])

    def test_image_wire_into_vae_encode_slanted_weighs_less(self):
        # i2i: the image chain stands on VAE Encode's row, so the image wire into it is level
        self.do("add LoadImage li")
        self.do("add VAEEncode e")
        self.do("link li.IMAGE e.pixels")
        self.do(f"layout {self.write_plan('put e origin' + chr(10) + 'put li left e' + chr(10) + 'move li 0 200' + chr(10))}")
        self.assertTrue([x for x in C.soft_problems(self.cv()) if x.startswith("image into e VAEEncode slants")])
        self.do(f"layout {self.write_plan('put e origin' + chr(10) + 'put li left e wire' + chr(10))}")
        self.assertFalse([x for x in C.soft_problems(self.cv()) if x.startswith("image into")])

    def test_gap_crossings_are_counted_in_each_row_sharing_its_span(self):
        # two rows ending and starting at the same x: the gap keeps the crossings of the row where they are, not 0 from
        # the first wire found (correction 1044: a model row ending at the column hid a crossed gap)
        self._ksampler()
        plan = """put k origin
put 42 left k gap 60
put 6 below 42
put 30 above k left
put 12 left 30 gap 60
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        # swap the encoders so their wires into k cross
        ya, yb = G.rect(cv.node("42"))[1], G.rect(cv.node("6"))[1]
        cv.translate(["42"], 0, yb - ya)
        cv.translate(["6"], 0, ya - yb)
        x0, x1 = G.rect(cv.node("42"))[2], G.rect(cv.node("k"))[0]
        spans = [g for g in C.column_gaps(cv) if round(g[0]) == round(x0) and round(g[1]) == round(x1)]
        self.assertEqual(len(spans), 1)
        self.assertGreaterEqual(spans[0][2], 1)

    def test_widening_a_gap_takes_a_node_right_aligned_with_the_opened_column(self):
        # a node above the gap whose right edge is the opened column's right edge moves with that column (correction 1044)
        self._ksampler()
        self.do("add ConditioningCombine m")
        self.do("link 42.0 m.conditioning_1 6.0 m.conditioning_2 m.0 k.positive")
        plan = """put k origin
put m left k wire
put 42 left m gap 60
put 6 below 42
put 30 above m right
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        w = G.rect(cv.node("30"))
        cv.translate(["30"], 0, 0)
        # make 30 straddle the gap between the encoders and m: wider to the left, right edge kept on m's
        cv.node("30")["size"][0] = (w[2] - w[0]) + 200
        cv.node("30")["pos"][0] = G.rect(cv.node("m"))[2] - cv.node("30")["size"][0]
        ys = [G.rect(cv.node(i))[1] for i in ("42", "6")]
        cv.translate(["42"], 0, ys[1] - ys[0])
        cv.translate(["6"], 0, ys[0] - ys[1])
        old = C.CROSS_WIDEN
        C.CROSS_WIDEN = 1
        try:
            done = C.widen_crossed_gaps(cv)
        finally:
            C.CROSS_WIDEN = old
        self.assertTrue(done)
        self.assertAlmostEqual(G.rect(cv.node("30"))[2], G.rect(cv.node("m"))[2], delta=1)

    def test_widening_a_gap_moves_the_rows_below_it_too(self):
        # a node right of the line far below the crossing wires moves too, so a column aligned across rows stays aligned
        # (corrections 1041, 1044)
        self._ksampler()
        self.do("add ConditioningCombine m")
        self.do("link 42.0 m.conditioning_1 6.0 m.conditioning_2 m.0 k.positive")
        plan = """put k origin
put m left k wire
put 42 left m gap 60
put 6 below 42
put 9 below m left
move 9 0 900
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        ys = [G.rect(cv.node(i))[1] for i in ("42", "6")]
        cv.translate(["42"], 0, ys[1] - ys[0])
        cv.translate(["6"], 0, ys[0] - ys[1])
        before = G.rect(cv.node("m"))[0] - G.rect(cv.node("9"))[0]
        old = C.CROSS_WIDEN
        C.CROSS_WIDEN = 1
        try:
            done = C.widen_crossed_gaps(cv)
        finally:
            C.CROSS_WIDEN = old
        self.assertTrue(done)
        self.assertAlmostEqual(G.rect(cv.node("m"))[0] - G.rect(cv.node("9"))[0], before, delta=1)

    def test_rail_lowering_into_a_group_joins_it(self):
        plan = """put 10 origin
put 13 right 10 gap 300
move 13 0 200
put 8 right 13
put 9 right 8
group G 13 8 9
rail 10.VAE to 8.vae
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        rr = [n["id"] for n in cv.s["nodes"] if n["type"] == "Reroute"]
        g = cv.s["groups"][0]
        self.assertTrue(rr)
        self.assertTrue(set(rr) <= set(g["members"]))
        self.assertLessEqual(g["bounding"][1] + C.P["GROUP_TITLE_H"]["value"] if "GROUP_TITLE_H" in C.P else g["bounding"][1],
                             min(G.rect(cv.node(r))[1] for r in rr))
        self.assertFalse([x for x in C.full_check(cv)[0] if "over the title of group" in x])

    def test_rail_reroute_not_below_a_sampler(self):
        # an image rail below the sampler: the Reroute before Save Image is not placed under the sampler
        self.do("add PreviewImage p")
        self.do("link 8.IMAGE p.images")
        self.do("row 8 13")
        self.do("put 9 right 13 gap 400")
        self.do("put p right 9 gap 400")
        self.do("rail 8.IMAGE to 9.images p.images")
        cv = self.cv()
        r13 = self.rect("13")
        for n in cv.s["nodes"]:
            if n["type"] == "Reroute":
                r = G.rect(n)
                self.assertTrue(r[1] >= r13[3] - 1, n["id"])   # the rail runs below the sampler
                self.assertFalse(C.in_grow_room(cv, cv.node("13"), r), n["id"])   # not within the room it grows into
        self.assertFalse([x for x in C.full_check(cv)[0] if x.startswith("r") and "is directly below 13" in x])

    def test_layout_rails_do_not_depend_on_plan_order(self):
        base = """put 30 origin
stack 30 6 42 26 22 27
put 10 left 42 top gap 300
put 12 above 10
put 8 right 42 top gap 400
"""
        one = base + "rail 10.VAE to 8.vae\nrail 12.MODEL to 22.model\n"
        two = base + "rail 12.MODEL to 22.model\nrail 10.VAE to 8.vae\n"
        self.do(f"layout {self.write_plan(one)}")
        cv = self.cv()
        p1 = self.positions()
        r1 = sorted((round(G.rect(n)[0]), round(G.rect(n)[1])) for n in cv.s["nodes"] if n["type"] == "Reroute")
        self.do(f"layout {self.write_plan(two)}")
        cv = self.cv()
        r2 = sorted((round(G.rect(n)[0]), round(G.rect(n)[1])) for n in cv.s["nodes"] if n["type"] == "Reroute")
        self.assertEqual({k: v for k, v in self.positions().items() if not k.startswith("r1")},
                         {k: v for k, v in p1.items() if not k.startswith("r1")})
        self.assertEqual(r1, r2)

    @unittest.skip("the canvas no longer chooses rail heights, moves nodes after the plan, or holds backward wires as unkeepable (correction 1001)")
    def test_layout_output_node_steps_down_for_a_wire_through(self):
        # Save Image stands level with VAE Decode, in the way of the image going on to a Preview farther right:
        # Save steps down (a staircase) and the wire through stays at the output height, with no Reroute
        self.do("add PreviewImage p")
        self.do("link 8.IMAGE p.images")
        plan = """put 8 origin
put 9 right 8
put 27 right 9 gap 300
put p right 27
rail 8.IMAGE to 9.images p.images
"""
        out = self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        self.assertTrue([x for x in out if "opening a lane" in x], out)
        self.assertGreater(self.rect("9")[1], self.rect("8")[1])
        self.assertFalse([n for n in cv.s["nodes"] if n["type"] == "Reroute"])
        self.assertTrue(C.wire_clear(cv, cv.out_xy("8", 0), cv.in_xy("p", "images"), {"8", "p"}))

    @unittest.skip("the canvas no longer chooses rail heights, moves nodes after the plan, or holds backward wires as unkeepable (correction 1001)")
    def test_layout_rails_go_model_vae_clip(self):
        def plan(stack):
            return f"""block load {stack}
stack {stack}
put 6 right load gap 600
put 42 below 6
put 8 right 6 gap 300
move 8 0 400
put 30 right 8
rail 12.MODEL to 30.model
rail 10.VAE to 8.vae
rail 11.CLIP to 6.clip 42.clip
"""
        with self.assertRaises(C.Stop) as e:
            self.do(f"layout {self.write_plan(plan('12 11 10'))}")
        self.assertIn("model, vae, clip from the top", str(e.exception))
        self.do(f"layout {self.write_plan(plan('12 10 11'))}")
        cv = self.cv()
        ys = {C.rail_type(cv, r, s): y for y, _, _, (r, s) in C.rail_spans(cv)}
        self.assertLess(ys["MODEL"], ys["VAE"])
        lines = C.full_check(cv)[0]
        self.assertFalse([x for x in lines if "rail runs above the" in x or "clip loader" in x], lines)

    def test_clip_loader_above_vae_loader_is_reported(self):
        self.do("stack 12 11 10")
        lines = C.full_check(self.cv())[0]
        self.assertTrue([x for x in lines if x.startswith("clip loader 11 is above the vae loader 10")], lines)

    def test_loader_order_is_checked_only_within_a_stacked_column(self):
        # Load VAE placed by its first user below, apart from the stacked model and clip loaders, is not out of order
        self.do("stack 12 11")
        self.do("put 10 below 11 gap 400")
        lines = C.full_check(self.cv())[0]
        self.assertFalse([x for x in lines if "is above the vae loader" in x], lines)
        self.do("stack 12 11 10")
        lines = C.full_check(self.cv())[0]
        self.assertTrue([x for x in lines if x.startswith("clip loader 11 is above the vae loader 10")], lines)

    @unittest.skip("the canvas no longer chooses rail heights, moves nodes after the plan, or holds backward wires as unkeepable (correction 1001)")
    def test_layout_conditioning_rail_runs_above_the_samplers(self):
        # the text encoder stands below the sampler; its conditioning still runs above the sampler to the guider beyond it
        plan = """put 13 origin
put 6 left 13 gap 300
move 6 0 400
put 26 right 13 gap 300
put 22 right 26 gap 300
rail 6.CONDITIONING to 26.conditioning 22.conditioning
"""
        self.do("unlink 26.conditioning")
        self.do("link 6.CONDITIONING 26.conditioning 6.CONDITIONING 22.conditioning")
        out = self.do(f"layout {self.write_plan(plan)}")
        h = [float(re.search(r"rail height (-?[\d.]+)", x).group(1)) for x in out if "line 6: rail height" in x]
        self.assertTrue(h, out)
        self.assertLess(h[0], self.rect("13")[1])

    def test_lane_crossings_counts_the_legs_across_the_other_rail(self):
        # A from 8 (top) to 9 (low), B from 27 (lower) to 13 (high): with A above B, A's drop into 9 crosses B's run
        # (B's drop into 13 lies past A's run); swapped, nothing crosses
        for nid, x, y in (("8", 0, 0), ("27", 0, 150), ("9", 800, 600), ("13", 900, -200)):
            self.do(f"put {nid} origin")
            self.do(f"move {nid} {x} {y}")
        cv = self.cv()
        a, b = [100, "8", 0, ["9"]], [200, "27", 0, ["13"]]
        self.assertEqual(C.lane_crossings(cv, a, b), 1)
        self.assertEqual(C.lane_crossings(cv, [100] + b[1:], [200] + a[1:]), 0)

    def test_loader_is_not_widened_past_the_node_below_it(self):
        # Load VAE stacked right above the sampler is not widened to the loader minimum width past the sampler
        self.do("put 13 origin")
        self.do("put 10 above 13")
        cv = self.cv()
        self.assertLess(cv.node("10")["size"][0], C.LOADER_MIN_W)
        self.assertNotIn("loader_base", cv.node("10"))

    def test_a_plan_places_without_numbers(self):
        C.HAND_PLACING_FOR_TESTS = False
        try:
            for plan, word in (("put 12 origin\nput 30 right 12\nmove 30 0 40\n", "there is no move"),
                               ("put 12 origin\nput 30 right 12 gap 100\n", "there is no gap 100"),
                               ("put 12 origin\nput 30 right 12 gap wide\n", "there is no gap wide"),
                               ("put 12 origin\nput 30 right 12\nwidth 12 30\n", "there is no width")):
                with self.assertRaises(C.Stop) as e:
                    self.do(f"layout {self.write_plan(plan, why=False)}")
                self.assertIn(word, str(e.exception))
        finally:
            C.HAND_PLACING_FOR_TESTS = True

    def test_put_between_two_references(self):
        C.AUTO_LEVEL = False   # the placing alone (the layout would close the gap between 30 and what it feeds)
        self.addCleanup(setattr, C, "AUTO_LEVEL", True)
        for second in ("put 13 right 30 below 22", "put 13 below 22 right 30"):
            self.do(f"layout {self.write_plan('put 30 origin' + chr(10) + 'put 22 below 30' + chr(10) + second + chr(10))}")
            self.assertEqual(self.rect("13")[0], self.rect("30")[2] + C.H_GAP)
            self.assertEqual(self.rect("13")[1], self.rect("22")[3] + C.V_GAP)

    def test_a_gap_is_kept_from_a_group_frame(self):
        self.do(f"layout {self.write_plan('put 12 origin' + chr(10) + 'put 30 right 12 top' + chr(10) + 'group A 30' + chr(10))}")
        self.assertEqual(self.rect("30")[0] - self.rect("12")[2], C.H_GAP + C.PAD_L)
        self.do(f"layout {self.write_plan('put 12 origin' + chr(10) + 'put 30 right 12 top' + chr(10) + 'group A 12' + chr(10) + 'group B 30' + chr(10))}")
        self.assertEqual(self.rect("30")[0] - self.rect("12")[2], C.H_GAP + C.PAD_R + C.PAD_L)

    def test_all_is_the_whole_workflow_with_its_frames(self):
        md = self.dir / "note_models.md"
        md.write_text("## What this workflow does\n\nx\n\n## models\n\n- vae\n", encoding="utf-8")
        plan = f"put 12 origin\nput 30 right 12 top\ngroup A 12 30\nnote {md} left all\nalign top all note_models\n"
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        cv.update_groups()
        frame = cv.s["groups"][0]["bounding"]
        self.assertEqual(self.rect("note_models")[1], frame[1])
        self.assertEqual(self.rect("note_models")[2], frame[0] - C.H_GAP)
        with self.assertRaises(C.Stop):
            self.do("put all right 12")

    def test_notes_are_placed_last_and_all_leaves_them_out(self):
        md, top = self.dir / "note_models.md", self.dir / "note_top.md"
        md.write_text("## What this workflow does\n\nx\n\n## models\n\n- vae\n", encoding="utf-8")
        top.write_text("### a\n\nb\n", encoding="utf-8")
        # the Note lines come before the node they name is placed: they run after every other line
        plan = (f"note {md} left all\nalign top all note_models\nnote {top} above 30 right\n"
                "put 12 origin\nput 30 right 12 top\n")
        self.do(f"layout {self.write_plan(plan)}")
        self.assertEqual(self.rect("note_top")[2], self.rect("30")[2])
        self.assertEqual(self.rect("note_top")[3], self.rect("30")[1] - C.V_GAP)
        # the overview Note aligns with the workflow's top, not with a Note placed above it (correction 913)
        self.assertEqual(self.rect("note_models")[1], min(self.rect("12")[1], self.rect("30")[1]))
        self.assertNotIn("model Note top edge", "\n".join(self.do("check")))

    def test_a_note_with_a_node_between_it_and_its_node_is_not_a_clear_place(self):
        # the places the canvas offers for a Note (in its frame, on another side) are the places the check accepts:
        # a node standing between the Note and the node it explains is trouble there too
        self.do("put 12 origin")
        self.do("put 30 right 12 top")
        md = self.dir / "note_b.md"
        md.write_text(f"🔗 {C.display_title(self.cv().node('12'), self.cv().oi)}\n\n### a\n\nb\n", encoding="utf-8")
        self.do(f"note {md} right 30")
        self.assertTrue([x for x in C.note_trouble(self.cv(), "note_b") if "stand between them" in x])

    @unittest.skip("a Note goes where the plan writes it; the canvas no longer tries other sides (correction 1005)")
    def test_a_note_below_a_node_that_grows_goes_above_it(self):
        md = self.dir / "note_g.md"
        md.write_text("### a\n\nb\n", encoding="utf-8")
        out = self.do(f"layout {self.write_plan(f'put 13 origin' + chr(10) + f'note {md} below 13' + chr(10))}")
        self.assertLess(self.rect("note_g")[3], self.rect("13")[1])
        self.assertTrue(any("goes above it" in l for l in out), out)

    def test_a_note_on_a_node_of_a_group_is_placed_with_the_group_inside_its_frame(self):
        # the Note line written with the group runs then, the frame takes it in, and the next group keeps clear of it
        md = self.dir / "note_in.md"
        md.write_text("### a\n\n" + "b\n\n" * 8, encoding="utf-8")
        plan = f"""put 30 origin
note {md} below 30
group "A" 30
put 12 right 30 top
group "B" 12
"""
        self.do(f"layout {self.write_plan(plan)}")
        cv = self.cv()
        ga = next(g for g in cv.s["groups"] if g["title"] == "A")["bounding"]
        gb = next(g for g in cv.s["groups"] if g["title"] == "B")["bounding"]
        r = self.rect("note_in")
        self.assertTrue(ga[0] <= r[0] and r[2] <= ga[0] + ga[2] and ga[1] <= r[1] and r[3] <= ga[1] + ga[3], (ga, r))
        self.assertGreaterEqual(gb[0], ga[0] + ga[2])   # the frames do not overlap

    def test_a_note_placed_inside_a_block_moves_with_the_block(self):
        # the Note line written right after its node's line, inside the block, before the block is put in its place
        md = self.dir / "note_blk.md"
        md.write_text("### a\n\nb\n", encoding="utf-8")
        plan = f"""block b 30
put 30 origin
note {md} below 30
put 12 origin
put b right 12 top
group "A" 30
"""
        self.do(f"layout {self.write_plan(plan)}")
        n, r = self.rect("note_blk"), self.rect("30")
        self.assertLess(abs(n[0] - r[0]), 1, (n, r))
        self.assertGreaterEqual(n[1], r[3])

    def test_a_note_widening_its_group_while_there_is_room_inside_is_told_where(self):
        # a short node beside a tall one leaves room inside the frame: the check names a note line that keeps it inside
        md = self.dir / "note_w2.md"
        md.write_text("### a\n\nb\n", encoding="utf-8")
        self.do("add SaveImage s")
        plan = f"""put s origin
put 30 right s top
put 12 right 30 top
note {md} left s
group "A" s 30 12
"""
        self.do(f"layout {self.write_plan(plan)}")
        lines = [x for x in C.hard_problems(self.cv()) if "widens the frame" in x]
        self.assertTrue(lines and "write note <its file>" in lines[0], lines)
        hint = lines[0].split("write note <its file> ")[1]
        self.do(f"layout {self.write_plan(plan.replace('left s', hint))}")
        self.assertFalse([x for x in C.hard_problems(self.cv()) if "widens the frame" in x])

    @unittest.skip("a Note goes where the plan writes it; the canvas no longer tries other sides (correction 1005)")
    def test_a_note_that_would_land_on_a_node_goes_to_another_side(self):
        md = self.dir / "note_o.md"
        md.write_text("### a\n\nb\n", encoding="utf-8")
        # right of 30 is where 12 stands: the canvas tries the other sides of 30 instead of putting it on 12
        out = self.do(f"layout {self.write_plan('put 30 origin' + chr(10) + 'put 12 right 30 top' + chr(10) + f'note {md} right 30' + chr(10))}")
        self.assertFalse([x for x in out if "overlap" in x and "note_o" in x], out)
        self.assertTrue(any("note_o: placed" in l for l in out), out)

    def test_a_title_written_after_the_lines_that_place_takes_its_width_before_them(self):
        # a long title widens its node: written at the end of the plan, the node beside it still keeps its gap
        self.do(f"layout {self.write_plan('put 12 origin' + chr(10) + 'put 30 right 12 top' + chr(10) + 'title 12 ' + 'W' * 60 + chr(10))}")
        self.assertGreaterEqual(self.rect("30")[0], self.rect("12")[2] + C.H_GAP - 0.5)

    def test_a_plan_includes_the_common_plan(self):
        common = self.dir / "common.txt"
        common.write_text("put 30 right 12 top\n", encoding="utf-8")
        self.do(f"layout {self.write_plan(f'put 12 origin' + chr(10) + 'include common.txt' + chr(10))}")
        self.assertEqual(self.rect("30")[0], self.rect("12")[2] + C.H_GAP)
        # a line of the included file that stops names that file and line
        common.write_text("put nope right 12\n", encoding="utf-8")
        with self.assertRaises(C.Stop) as e:
            self.do(f"layout {self.write_plan(f'put 12 origin' + chr(10) + 'include common.txt' + chr(10))}")
        self.assertIn("common.txt:1", str(e.exception))

    def test_a_note_has_the_default_width(self):
        md = self.dir / "note_w.md"
        md.write_text("### a\n\nb\n", encoding="utf-8")
        self.do(f"layout {self.write_plan(f'put 30 origin' + chr(10) + f'note {md} below 30' + chr(10))}")
        self.assertEqual(self.rect("note_w")[2] - self.rect("note_w")[0], 400)
        self.do(f"layout {self.write_plan(f'put 30 origin' + chr(10) + f'note {md} right 30' + chr(10))}")
        self.assertEqual(self.rect("note_w")[2] - self.rect("note_w")[0], 400)

    def test_a_note_takes_two_references(self):
        md = self.dir / "note_a.md"
        md.write_text("### a\n\nb\n", encoding="utf-8")
        self.do(f"layout {self.write_plan(f'put 30 origin' + chr(10) + 'put 22 below 30' + chr(10) + f'note {md} right 30 below 22' + chr(10))}")
        self.assertEqual(self.rect("note_a")[0], self.rect("30")[2] + C.H_GAP)
        self.assertEqual(self.rect("note_a")[1], self.rect("22")[3] + C.V_GAP)

    def test_core_names_what_the_usual_form_lacks_instead_of_stopping(self):
        self.do("unlink 8.samples")
        out = self.do("core 13")
        self.assertIn("put 13 origin", out)
        self.assertIn("inputs 13   # 22 is the guider: its conditioning enters it horizontally", out)
        self.assertTrue(any(l.startswith("# no decoder takes 13's latent") for l in out))

    def test_guide_quotes_the_lines_that_name_nodes_on_the_canvas(self):
        out = self.do("guide")
        self.assertTrue(out[0].startswith("# the lines of references/"))
        heads = [l for l in out if l.startswith("\n## ")]
        self.assertTrue(any("SamplerCustomAdvanced" in h for h in heads), heads)

    def test_core_prints_the_usual_form(self):
        out = self.do("core 13")
        self.assertIn("inputs 13   # 22 is the guider: its conditioning enters it horizontally", out)
        self.assertIn("put 26 left 22 wire", out)
        self.assertIn("put 10 above 13   # Load VAE used only by the decoder", out)
        self.assertIn("put 8 right 13 wire", out)
        self.do(f"layout {self.write_plan(chr(10).join(l for l in out if not l.startswith('#')))}")
        self.assertEqual(C.hard_problems(self.cv()), [])
        with self.assertRaises(C.Stop):
            self.do("core 8")

    def test_checks_for_titles_far_loaders_and_use_core(self):
        self.do("put 12 origin")
        self.do("put 30 right 12")
        self.do("title 30 my sampling")
        lines = C.full_check(self.cv())[0]
        self.assertTrue([x for x in lines if x.startswith("title the author gave") and x.endswith(": 30")], lines)
        # an author's title weighs less: reported after the others
        self.assertIn("title the author gave left on a node (names go back to the display name \"ModelSamplingFlux\"): 30",
                      C.soft_problems(self.cv()))
        self.do("title 30 ModelSamplingFlux")
        self.do("put 6 right 30")
        self.do("put 26 right 6")
        self.do("put 11 left 12")
        self.do("move 11 0 200")
        lines = C.full_check(self.cv())[0]
        self.assertTrue([x for x in lines if x.startswith("loader away from its first user") and x.endswith(": 11")], lines)
        self.assertTrue(C.in_use_core("ImageResize+", ["ImageResize+ (essentials, keep proportion)"]))
        self.assertFalse(C.in_use_core("ImageResize", ["ImageResizeKJ (KJNodes)"]))

    def test_put_step_stands_just_below_the_wire(self):
        self.do("put 8 origin")
        out = self.do("put 9 right 8 step")
        self.assertIn("stepped down below the wire from 8: 9", out)
        self.assertEqual(self.rect("9")[1], self.cv().out_xy("8", 0)[1] + C.LANE_CLEAR_BELOW)

    def test_conditioning_rail_runs_below_the_model_rail(self):
        for nid, x, y in (("12", 0, 0), ("6", 0, 300), ("30", 900, 0), ("22", 900, 300)):
            self.do(f"put {nid} origin")
            self.do(f"move {nid} {x} {y}")
        cv = self.cv()
        lo, hi = C.type_bounds(cv, "6", 0, ["22"], [[100, "12", 0, ["30"]]])
        self.assertEqual(lo, 100 + C.P["RAIL_GAP"])

    def test_report_reads_rails_without_height(self):
        # the report page explains a rail line without a height and the lines layout writes about it
        RPT = C.RPT
        x = RPT.explain({"toks": ["rail", "10.VAE", "to", "8.vae"]}, "ja")
        self.assertIn("canvas が決めた高さ", x["s"])
        S = RPT.Say("ja")
        self.assertIn("通り道を空け", RPT.note_text("line 5: rail height 475: opened a lane 49px above the output height, since the nearest clear height is 572px away", S))
        self.assertIn("下げました", RPT.note_text("line 5: moved 43px down to open the lane: 42 26", S))
        self.assertIn("出力の高さ", RPT.note_text("line 5: rail height 141: at the output height", S))

    def test_layout_stops_without_change(self):
        self.do(f"layout {self.write_plan(self.PLAN)}")
        before = self.cv().s
        bad = self.write_plan(self.PLAN + "put 9 right nosuchnode\n")
        with self.assertRaises(C.Stop):
            self.do(f"layout {bad}")
        self.assertEqual(self.cv().s, before)

    def test_preview_any_is_not_smaller_than_frontend(self):
        self.do("add PreviewAny pa")
        w, h = self.cv().node("pa")["size"]
        self.assertGreaterEqual(h, 122)   # the size after the frontend adds preview_text and preview_mode (oracle_widgets.json)

    def test_empty_band_is_reported(self):
        self.do("put 12 origin")
        self.do("put 11 below 12 gap 300")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("empty band across everything")])

    def test_core_like_finds_color_transfer(self):
        oi = C.Work(self.dir).oi
        self.assertTrue(any(x.startswith("ColorTransfer") for x in C.core_like("ColorMatch", oi)))

    def test_text_area_is_at_least_100(self):
        cv = self.cv()
        oi = cv.oi
        if "MiniMaxH3ImageToVideo" not in oi:
            self.skipTest("not in object_info")
        self.do("add MiniMaxH3ImageToVideo m")
        n = self.cv().node("m")
        names, grow = C.RD.widget_info(n, oi)
        lay = G.widget_layout(n, names, grow)
        self.assertGreaterEqual(lay["prompt"][1], C.TEXT_MIN_H)
        self.assertEqual(C.TEXT_MIN_H, 100)

    def test_loaders_have_same_width(self):
        cv = self.cv()
        ws = {cv.node(i)["size"][0] for i in ("12", "11", "10")}   # UNETLoader, DualCLIPLoader, VAELoader
        self.assertEqual(len(ws), 1)
        self.assertGreaterEqual(ws.pop(), C.LOADER_MIN_W)

    def test_width_and_value_top_checks(self):
        self.do("copy 34 35")
        self.do("put 34 origin")
        self.do("put 35 right 34")
        self.do("move 35 0 20")
        self.do("put 13 below 30" if False else "put 22 below 34")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("value nodes side by side have unaligned tops")])

    def test_inputs_puts_the_guider_level_with_sampler_custom(self):
        # correction 1025: the sampler stays on the eye line and its column moves to it; the guider's wire is horizontal
        self.do("copy 25 16 17")
        self.do("link 25.NOISE 13.noise 16.SAMPLER 13.sampler 17.SIGMAS 13.sigmas 30.MODEL 17.model")
        self.do("put 13 origin")
        self.do("move 13 2000 600")
        before = self.rect("13")
        self.do("inputs 13")
        cv = self.cv()
        self.assertEqual(self.rect("13"), before)
        self.assertLess(abs(cv.out_xy("22", 0)[1] - cv.in_xy("13", "guider")[1]), 1)

    def test_image_area_is_added_to_initial_size(self):
        import nodesize
        for t, kind in (("SaveImage", "save"), ("PreviewImage", "preview"), ("LoadImage", "load")):
            self.do(f"add {t} x_{kind}")
            n = self.cv().node(f"x_{kind}")
            self.assertEqual(C.image_kind(t, self.cv().oi), kind)
            w0, h0 = nodesize.default_size(n, self.cv().oi, title=C.display_title(n, self.cv().oi))
            # a square image area below the initial size (never smaller than the frontend makes the node)
            fw, fh = C.FRONTEND_MIN.get(t) or (0, 0)
            a = C.IMAGE_AREA[kind]
            self.assertEqual(n["size"], [round(max(w0, fw, a)), round(max(h0, fh) + a + C.P["VUE_MARGIN"])])
        self.assertIsNone(C.image_kind("VAEDecode", self.cv().oi))

    def test_image_kind_from_object_info(self):
        img = ["IMAGE", {}]
        oi = {
            "VideoCombine": {"output_node": True, "category": "Video Helper Suite",
                             "input": {"required": {"images": img, "filename_prefix": ["STRING", {"default": "x"}]}}},
            "SaveAnimatedWEBP": {"output_node": True, "category": "image", "input": {"required": {"images": img}}},
            "Viewer": {"output_node": True, "category": "image", "input": {"optional": {"image_a": img}}},
            "LoadVideo": {"output_node": False, "category": "video",
                          "input": {"required": {"file": ["COMBO", {"options": ["a.mp4"], "video_upload": True}]}}},
            "SaveVideo": {"output_node": True, "category": "video", "input": {"required": {"video": ["VIDEO", {}]}}},
        }
        self.assertEqual({t: C.image_kind(t, oi) for t in oi},
                         {"VideoCombine": "save", "SaveAnimatedWEBP": "save", "Viewer": "preview", "LoadVideo": "load",
                          "SaveVideo": "save"})

    def test_column_gap_and_consecutive_reroute(self):
        self.do("copy 25 16")
        self.do("link 25.NOISE 13.noise 16.SAMPLER 13.sampler")
        self.do("put 25 origin")
        self.do("put 16 below 25 gap 200")   # two sources of SamplerCustomAdvanced: one column
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("gap inside a column")])

    def test_export_has_all_placed_nodes(self):
        self.do("row 12 30 22 13 8 9")
        cv = self.cv()
        wf, _ = cv.workflow()
        self.assertEqual(len(wf["nodes"]), 6)

    def test_cross_into_same_node_is_counted(self):
        # wires into VAE Decode cross when the upper input (samples) comes from below and the lower input (vae) from above
        self.do("put 8 origin")
        self.do("put 13 left 8")
        self.do("move 13 0 300")
        self.do("put 10 left 8")
        self.do("move 10 -400 -300")
        cv = self.cv()
        ws = dict((l["target_input"], pts) for l, pts in C.wires_of(cv) if l["target_id"] == "8")
        self.assertTrue(C.poly_cross(ws["samples"], ws["vae"]))
        _, counts = C.full_check(cv)
        self.assertGreaterEqual(counts["crossings"], 1)

    def test_only_model_loaders_share_width(self):
        # only diffusion model, clip and vae loaders share a width
        self.do("add UpscaleModelLoader u")
        cv = self.cv()
        self.assertFalse(cv.is_model_loader(cv.node("u")))
        self.assertTrue(cv.is_model_loader(cv.node("12")))
        self.assertNotIn("loader_base", cv.node("u"))

    def test_loader_not_widened_into_neighbor(self):
        # a loader that would overlap its neighbour is not widened
        self.do("put 11 origin")
        self.do("put 10 right 11 gap 0")
        cv = self.cv()
        self.assertEqual(C.overlaps(cv), [])

    def test_set_dynamic_combo_resets_children(self):
        self.do("add ResizeImageMaskNode r")
        self.do("set r 'resize_type=scale to multiple'")
        self.assertEqual(self.cv().node("r")["widgets_values"], ["scale to multiple", 8, "area"])

    def test_level_on_unplaced_node_stops(self):
        with self.assertRaises(C.Stop) as e:
            self.do("level 12.MODEL 30.model")
        self.assertIn("not placed yet", str(e.exception))

    def test_rail_does_not_add_reroute_before_target_on_rail(self):
        # no Reroute right before a target that sits at the rail height
        self.do("put 10 origin")
        self.do("put 26 right 10")
        self.do("put 8 right 26")
        cv = self.cv()
        y = cv.bbox(["26"])[3] + C.V_GAP
        self.do(f"move 8 0 {round(y - cv.in_xy('8', 'vae')[1])}")
        self.do("unlink 8.vae")
        self.do("rail 10.VAE below 26 to 8.vae")
        cv = self.cv()
        rr = [n for n in cv.s["nodes"] if n["type"] == "Reroute"]
        self.assertEqual(len(rr), 1)

    def test_subgraph_exit_mismatch(self):
        raw = {"definitions": {"subgraphs": [{"name": "S", "outputs": [{"name": "a", "linkIds": [1]}, {"name": "b", "linkIds": [1]}],
                                              "links": [{"id": 1, "origin_id": 5, "origin_slot": 1, "target_id": -20, "target_slot": 0}]}]}}
        w = C.subgraph_exit_mismatch(raw)
        self.assertTrue(any("more than one exit" in x for x in w))
        self.assertTrue(any("exit b lists wire 1, which goes into another exit" in x for x in w))

    def test_render_label_keeps_ascii(self):
        import render as R
        self.assertEqual(R.ascii_part("Markdown Note: 使い方"), "Markdown Note")
        self.assertEqual(R.ascii_part("使い方"), "")

    def test_legacy_group_node_is_expanded(self):
        import legacy_groups as LGR
        oi = C.Work(self.dir).oi
        raw = {
            "nodes": [
                {"id": 1, "type": "EmptyLatentImage", "inputs": [], "outputs": [{"name": "LATENT", "type": "LATENT", "links": [3]}],
                 "widgets_values": [512, 512, 1], "pos": [0, 0]},
                {"id": 10, "type": "workflow>G", "pos": [300, 0], "mode": 0,
                 "inputs": [{"name": "samples", "type": "LATENT", "link": 3},
                            {"name": "vae_name", "type": "COMBO", "widget": {"name": "vae_name"}, "link": None}],
                 "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [4]}], "widgets_values": ["b.safetensors"]},
                {"id": 2, "type": "PreviewImage", "inputs": [{"name": "images", "type": "IMAGE", "link": 4}], "outputs": [], "pos": [600, 0]},
            ],
            "links": [[3, 1, 0, 10, 0, "LATENT"], [4, 10, 0, 2, 0, "IMAGE"]],
            "last_node_id": 10, "last_link_id": 4,
            "extra": {"groupNodes": {"G": {
                "nodes": [
                    {"type": "VAELoader", "pos": [0, 0], "inputs": [{"name": "vae_name", "type": "COMBO", "widget": {"name": "vae_name"}, "link": None}],
                     "outputs": [{"name": "VAE", "type": "VAE", "links": []}], "widgets_values": ["a.safetensors"]},
                    {"type": "VAEDecode", "pos": [300, 0], "inputs": [{"name": "samples", "type": "LATENT", "link": None}, {"name": "vae", "type": "VAE", "link": None}],
                     "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": []}], "widgets_values": []}],
                "links": [[0, 0, 1, 1, 9, "VAE"]], "external": []}}},
        }
        out, warn = LGR.expand(raw, oi)
        types = {n["id"]: n["type"] for n in out["nodes"]}
        self.assertNotIn(10, types)
        vae = next(i for i, t in types.items() if t == "VAELoader")
        dec = next(i for i, t in types.items() if t == "VAEDecode")
        self.assertEqual(next(n for n in out["nodes"] if n["id"] == vae)["widgets_values"], ["b.safetensors"])
        ls = {(l[1], l[2], l[3], l[4]) for l in out["links"]}
        self.assertIn((1, 0, dec, 0), ls)
        self.assertIn((vae, 0, dec, 1), ls)
        self.assertIn((dec, 0, 2, 0), ls)
        self.assertTrue(warn)

    def test_model_note_is_purple(self):
        md = self.dir / "note_models.md"
        md.write_text("## models\n\n- vae\n", encoding="utf-8")
        self.do("put 12 origin")
        self.do(f"note {md} left 12")
        n = self.cv().node("note_models")
        self.assertEqual((n["color"], n["bgcolor"]), C.COLORS["purple"])

    def test_other_note_is_yellow(self):
        md = self.dir / "note_how.md"
        md.write_text("## how to use\n\n- load an image\n", encoding="utf-8")
        self.do("put 12 origin")
        self.do(f"note {md} left 12")
        n = self.cv().node("note_how")
        self.assertEqual((n["color"], n["bgcolor"]), C.COLORS["yellow"])

    def test_title_with_type_name_is_pointed_out(self):
        out = self.do("add PrimitiveInt")
        nid = self.cv().s["nodes"][-1]["id"]
        out = "\n".join(self.do(f"title {nid} PrimitiveInt: fps"))
        self.assertIn("the name shown on screen is Int", out)
        out = "\n".join(self.do(f"title {nid} Int: fps"))
        self.assertNotIn("shown on screen", out)

    def test_a_load_clip_above_a_node_that_is_not_a_sampler_takes_the_loaders_width(self):
        # the loaders are made as wide as the widest; only a sampler right below keeps a loader from sticking out past it
        self.do("add PrimitiveInt t")
        self.do("put 12 origin")
        self.do("put 10 below 12")
        self.do("put t right 12 gap 400")
        self.do("put 11 above t right")
        cv = self.cv()
        cv.same_loader_width()
        widest = max(cv.node(i)["size"][0] for i in ("12", "10"))
        self.assertGreater(widest, cv.node("t")["size"][0])
        self.assertEqual(cv.node("11")["size"][0], widest)
        # written right-aligned with t: it widens to the left and keeps that edge
        self.assertEqual(G.rect(cv.node("11"))[2], G.rect(cv.node("t"))[2])
        # written left-aligned: widened too (it sticks out past t, which is not a sampler)
        self.do("put 11 above t left")
        cv = self.cv()
        cv.same_loader_width()
        self.assertEqual(cv.node("11")["size"][0], widest)

    def test_a_stage_whose_result_wire_is_level_but_whose_latent_slants_is_fixed_in_the_plan(self):
        # the previous stage's image (out of VAE Decode 8) enters the stage's VAE Encode level, while the latent into the
        # stage's KSampler slants: the stage's chain is the one to move
        self.do("add VAEEncode e")
        self.do("add KSampler k")
        self.do("link 8.0 e.pixels 10.0 e.vae e.0 k.latent_image")
        self.do("put 8 origin")
        self.do("put e right 8")
        self.do("level 8.IMAGE e.pixels move e")
        self.do("put k right e")
        self.do("move k 0 80")
        chk = next(f for n, f in C.CHECKS if n == "result wire level, latent into the sampler slants")
        cv = self.cv()
        self.assertTrue(chk(cv, C._CheckCtx(cv)), "the latent slants while the result wire is level")
        self.do("align top k e")
        cv = self.cv()
        self.assertEqual(chk(cv, C._CheckCtx(cv)), [], "the chain on the sampler's top edge is as good")
        self.do("move k 0 80")
        self.do("level e.LATENT k.latent_image move e")
        cv = self.cv()
        self.assertEqual(chk(cv, C._CheckCtx(cv)), [])

    def test_a_positive_from_the_column_left_of_a_sampler_that_slants_is_fixed_in_the_plan(self):
        # a conditioning node (as Apply ControlNet) stands in the column just left of the stage's KSampler, far above it:
        # its positive is levelled
        self.do("add KSampler k")
        self.do("add FluxGuidance a")
        self.do("link 6.0 a.conditioning a.0 k.positive")
        self.do("put k origin")
        self.do("put a left k")
        self.do("move a 0 -300")
        cv = self.cv()
        self.assertTrue([x for x in C.hard_problems(cv) if x.startswith("positive into the sampler slants")])
        self.do("level a.CONDITIONING k.positive move a")
        cv = self.cv()
        self.assertFalse([x for x in C.hard_problems(cv) if x.startswith("positive into the sampler slants")])

    def test_a_note_touching_a_node_is_fixed_in_the_plan(self):
        # a Note left-aligned below a narrow node sticks out and touches the next node: fixed in the plan
        self.do("put 8 origin")
        cv = self.cv()
        r = G.rect(cv.node("8"))
        cv.s["nodes"].append({"id": "nt", "type": "MarkdownNote", "mode": 0, "pos": [r[2] + 10, r[1]], "size": [400, 100],
                              "widgets_values": ["text"], "inputs": [], "outputs": []})
        hard = [x for x in C.hard_problems(cv) if x.startswith("narrow gap")]
        self.assertTrue(hard and "a Note too close" in hard[0], hard)
        cv.node("nt")["pos"][0] = r[2] + 45
        self.assertFalse([x for x in C.hard_problems(cv) if x.startswith("narrow gap")])

    def test_a_load_image_may_say_what_it_takes_in_its_title(self):
        self.do("add LoadImage li")
        self.do("put li origin")
        self.do("title li Load Image: reference image 1")
        cv = self.cv()
        chk = next(f for n, f in C.CHECKS if n == "titles the author gave")
        self.assertEqual(chk(cv, C._CheckCtx(cv)), [])
        plan = "put li origin\ntitle li \"Load Image: reference image 1\"\n"
        self.do(f"layout {self.write_plan(plan)}")
        self.assertEqual(self.cv().node("li").get("title"), "Load Image: reference image 1")

    def test_tool_wire_not_horizontal_is_reported(self):
        self.do("put 10 origin")
        self.do("put 8 right 10")
        self.do("move 8 0 100")
        lines, counts = C.full_check(self.cv())
        tilt = [x for x in lines if x.startswith("non-horizontal wire (VAE,")]
        self.assertTrue(tilt)
        self.assertFalse([x for x in lines if "allowed; count only" in x])
        self.assertGreaterEqual(counts["non-horizontal wires"], 1)
        self.assertEqual(C.RPT.problem_text({"r": tilt[0]}, "en")["k"], "tilt")

    def _two_loader_rails(self, model_spec, vae_spec):
        # model loader above the vae loader, a tall node right of both (so the rails cannot run at the output height)
        self.do("put 12 origin")
        self.do("put 10 below 12")
        self.do("put 6 right 12")
        self.do("put 30 right 6")
        self.do("put 8 right 30")
        return self._rails(model_spec, vae_spec)

    def _rails(self, model_spec, vae_spec):
        self.do(f"rail 12.MODEL {model_spec} to 30.model")
        self.do(f"rail 10.VAE {vae_spec} to 8.vae")
        return C.full_check(self.cv())[0]

    def test_rail_order_against_loader_order(self):
        lines = self._two_loader_rails("below 10", "above 12")
        bad = [x for x in lines if x.startswith("rail order differs from loader order")]
        self.assertEqual(len(bad), 1)
        self.assertTrue(bad[0].endswith("rail of 12 and rail of 10"))
        self.assertEqual(C.RPT.problem_text({"r": bad[0]}, "en")["k"], "order")
        self.do("undo")
        self.do("undo")
        lines = self._rails("above 12", "below 10")
        self.assertFalse([x for x in lines if x.startswith("rail order differs from loader order")])

    def test_raising_reroute_right_of_loader(self):
        lines = self._two_loader_rails("above 12", "below 10")
        raise_lines = [x for x in lines if x.startswith("raising Reroute right of a loader")]
        self.assertEqual({x.rsplit(": ", 1)[1] for x in raise_lines}, {"12", "10"})
        self.assertNotIn("`move", raise_lines[0] + raise_lines[1])   # names what to do in the plan, no coordinates
        self.assertEqual(C.RPT.problem_text({"r": raise_lines[0]}, "en")["k"], "reroute")
        self.do("undo")
        self.do("undo")
        self.do("rail 12.MODEL level 12.MODEL to 30.model")   # at the output height: no raising Reroute
        lines = C.full_check(self.cv())[0]
        self.assertFalse([x for x in lines if x.startswith("raising Reroute right of a loader")])

    def test_loader_rail_below_its_targets(self):
        lines = self._two_loader_rails("above 12", "below 10")
        bad = [x for x in lines if x.startswith("loader rail runs below its targets")]
        self.assertEqual(bad, ["loader rail runs below its targets (model, vae and clip rails go above): rail of 10"])
        self.assertEqual(C.RPT.problem_text({"r": bad[0]}, "en")["k"], "order")
        self.assertIn("のレールが、配る先のノードより下を通っています", C.RPT.problem_text({"r": bad[0]}, "ja")["t"])
        self.do("undo")
        self.do("undo")
        lines = self._rails("above 12", "above 12")
        self.assertFalse([x for x in lines if x.startswith("loader rail runs below its targets")])

    def test_sampler_custom_advanced_side_inputs_are_not_tilt(self):
        self.do("copy 25 16 17")
        self.do("link 25.0 13.noise 16.0 13.sampler 17.0 13.sigmas")
        self.do("put 13 origin")
        for nid, dy in (("25", -300), ("22", -150), ("16", 150), ("17", 300), ("27", 450)):
            self.do(f"put {nid} left 13")
            self.do(f"move {nid} 0 {dy}")
        lines = C.full_check(self.cv())[0]
        into13 = {x.rsplit(".", 1)[1] for x in lines if x.startswith("non-horizontal wire") and " → 13." in x}
        self.assertEqual(into13, {"latent_image"})

    def test_controlnet_apply_sd3_becomes_apply_controlnet(self):
        import json
        oi = json.loads(OI.read_text(encoding="utf-8"))
        cond = lambda: {"positive": ["CONDITIONING"], "negative": ["CONDITIONING"], "control_net": ["CONTROL_NET"]}
        floats = {"strength": ["FLOAT", {"default": 1.0}], "start_percent": ["FLOAT", {"default": 0.0}], "end_percent": ["FLOAT", {"default": 1.0}]}
        oi["ControlNetApplySD3"] = {"display_name": "Apply Controlnet with VAE", "category": "model/conditioning/controlnet",
                                    "python_module": "comfy_extras.nodes_sd3", "deprecated": True, "output": ["CONDITIONING", "CONDITIONING"],
                                    "output_name": ["positive", "negative"],
                                    "input": {"required": {**cond(), "vae": ["VAE"], "image": ["IMAGE"], **floats}}}
        oi["ControlNetApplyAdvanced"] = {"display_name": "Apply ControlNet", "category": "model/conditioning/controlnet",
                                         "python_module": "nodes", "output": ["CONDITIONING", "CONDITIONING"], "output_name": ["positive", "negative"],
                                         "input": {"required": {**cond(), "image": ["IMAGE"], **floats}, "optional": {"vae": ["VAE"]}}}
        node = {"id": 5, "type": "ControlNetApplySD3", "pos": [0, 0], "mode": 0, "widgets_values": [0.4, 0, 0.6],
                "inputs": [{"name": n, "type": t, "link": None} for n, t in
                           (("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("control_net", "CONTROL_NET"), ("vae", "VAE"), ("image", "IMAGE"))],
                "outputs": [{"name": "positive", "type": "CONDITIONING", "links": []}, {"name": "negative", "type": "CONDITIONING", "links": []}]}
        wf = {"nodes": [node], "links": [], "last_node_id": 5, "last_link_id": 0}
        d = Path(tempfile.mkdtemp())
        try:
            (d / "wf.json").write_text(json.dumps(wf), encoding="utf-8")
            (d / "oi.json").write_text(json.dumps(oi), encoding="utf-8")
            out = C.run_cmd(C.Work(d / "w"), f"open {d / 'wf.json'} {d / 'oi.json'}")
            self.assertTrue(any(x.startswith("replaced: 5 ControlNetApplySD3 → ControlNetApplyAdvanced") for x in out), out)
            flat = json.loads((d / "w" / "src.flat.json").read_text(encoding="utf-8"))
            n = {str(x["id"]): x for x in flat["nodes"]}["5"]
            self.assertEqual(n["type"], "ControlNetApplyAdvanced")
            self.assertEqual(n["widgets_values"][:3], [0.4, 0, 0.6])
        finally:
            shutil.rmtree(d)

    def test_rgthree_comparer_becomes_core_image_compare(self):
        import json
        oi = json.loads(OI.read_text(encoding="utf-8"))
        oi["ImageCompare"] = {"display_name": "Compare Images", "category": "image", "output_node": True,
                              "python_module": "comfy_extras.nodes_image_compare", "output": [], "output_name": [],
                              "input": {"required": {"compare_view": ["IMAGECOMPARE", {"socketless": True}]},
                                        "optional": {"image_a": ["IMAGE", {}], "image_b": ["IMAGE", {}]}}}
        oi["Image Comparer (rgthree)"] = {"display_name": "Image Comparer (rgthree)", "category": "rgthree", "output_node": True,
                                          "python_module": "custom_nodes.rgthree-comfy", "output": [], "output_name": [],
                                          "input": {"required": {}, "optional": {"image_a": ["IMAGE"], "image_b": ["IMAGE"]}}}
        img_out = {"name": "IMAGE", "type": "IMAGE", "links": [1, 2, 3]}
        ab = lambda a, b: [{"name": "image_a", "type": "IMAGE", "link": a, "shape": 7}, {"name": "image_b", "type": "IMAGE", "link": b, "shape": 7}]
        wf = {"nodes": [
            {"id": 1, "type": "LoadImage", "pos": [0, 0], "mode": 0, "inputs": [], "widgets_values": ["example.png", "image"],
             "outputs": [img_out, {"name": "MASK", "type": "MASK", "links": []}]},
            {"id": 2, "type": "Image Comparer (rgthree)", "pos": [400, 0], "mode": 0, "inputs": ab(1, 2), "outputs": [],
             "widgets_values": [[{"name": "A", "selected": True, "url": "/api/view?filename=a.png"}]]},
            {"id": 3, "type": "ImageCompare", "pos": [400, 400], "mode": 0, "inputs": ab(3, None), "outputs": [], "widgets_values": []}],
            "links": [[1, 1, 0, 2, 0, "IMAGE"], [2, 1, 0, 2, 1, "IMAGE"], [3, 1, 0, 3, 0, "IMAGE"]],
            "last_node_id": 3, "last_link_id": 3}
        d = Path(tempfile.mkdtemp())
        try:
            (d / "wf.json").write_text(json.dumps(wf), encoding="utf-8")
            (d / "oi.json").write_text(json.dumps(oi), encoding="utf-8")
            out = C.run_cmd(C.Work(d / "w"), f"open {d / 'wf.json'} {d / 'oi.json'}")
            self.assertTrue(any(x.startswith("replaced: 2 Image Comparer (rgthree) → ImageCompare") for x in out))
            self.assertFalse([x for x in out if x.startswith("removed:")])
            flat = json.loads((d / "w" / "src.flat.json").read_text(encoding="utf-8"))
            nodes = {str(n["id"]): n for n in flat["nodes"]}
            self.assertEqual(nodes["2"]["type"], "ImageCompare")
            self.assertEqual([i["name"] for i in nodes["2"]["inputs"]], ["image_a", "image_b"])
            self.assertEqual(nodes["2"]["widgets_values"], [])
            into2 = {l["target_input"] for l in flat["links"] if str(l["target_id"]) == "2"}
            self.assertEqual(into2, {"image_a", "image_b"})
            self.assertEqual(nodes["3"]["type"], "ImageCompare")
        finally:
            shutil.rmtree(d)

    def test_refs_and_models_read_the_shipped_copy(self):
        import json
        d = Path(tempfile.mkdtemp())
        old = C.SITE_CATALOG
        try:
            C.SITE_CATALOG = d / "index.json"
            with self.assertRaises(C.Stop) as e:
                C.do_refs(["flux"])
            self.assertIn("missing", str(e.exception))
            C.SITE_CATALOG.write_text(json.dumps({"workflows": [
                {"url": "https://example.invalid/workflows/flux-t2i.json", "updated": "2026-01-02",
                 "articles": [{"lang": "en", "title": "Flux", "heading": "text to image"}],
                 "models": [{"name": "ae.safetensors", "directory": "vae", "url": "https://example.invalid/ae.safetensors"}]}]}),
                encoding="utf-8")
            self.assertEqual(C.do_refs(["flux"]), ["2026-01-02  https://example.invalid/workflows/flux-t2i.json  (Flux / text to image)"])
            self.assertEqual(C._site_models()["ae.safetensors"]["directory"], "vae")
        finally:
            C.SITE_CATALOG = old
            shutil.rmtree(d)
        self.assertEqual(C.SITE_CATALOG, Path(C.__file__).resolve().parent.parent / "references" / "site" / "index.json")
        self.assertTrue(C.SITE_CATALOG.is_file())   # the copy is shipped with the skill

    def test_null_proxy_widget_value_keeps_inner_value(self):
        import json
        sgid = "11111111-2222-3333-4444-555555555555"
        wf = {"nodes": [
            {"id": 1, "type": sgid, "pos": [0, 0], "mode": 0, "inputs": [],
             "outputs": [{"name": "NOISE", "type": "NOISE", "links": []}],
             "properties": {"proxyWidgets": [["5", "noise_seed"], ["5", "control_after_generate"], ["6", "noise_seed"]]},
             "widgets_values": [None, None, 7]}],
            "links": [], "last_node_id": 1, "last_link_id": 0,
            "definitions": {"subgraphs": [{
                "id": sgid, "name": "S", "inputs": [],
                "outputs": [{"id": "o", "name": "NOISE", "type": "NOISE", "linkIds": [1]}],
                "nodes": [
                    {"id": 5, "type": "RandomNoise", "pos": [0, 0], "mode": 0, "inputs": [],
                     "outputs": [{"name": "NOISE", "type": "NOISE", "links": [1]}], "widgets_values": [1, "randomize"]},
                    {"id": 6, "type": "RandomNoise", "pos": [0, 200], "mode": 0, "inputs": [],
                     "outputs": [{"name": "NOISE", "type": "NOISE", "links": []}], "widgets_values": [3, "fixed"]}],
                "links": [{"id": 1, "origin_id": 5, "origin_slot": 0, "target_id": -20, "target_slot": 0, "type": "NOISE"}]}]}}
        d = Path(tempfile.mkdtemp())
        try:
            (d / "wf.json").write_text(json.dumps(wf), encoding="utf-8")
            C.run_cmd(C.Work(d / "w"), f"open {d / 'wf.json'} {OI}")
            flat = json.loads((d / "w" / "src.flat.json").read_text(encoding="utf-8"))
            values = {str(n["id"]): n.get("widgets_values") for n in flat["nodes"]}
            self.assertEqual(values["1:5"], [1, "randomize"])   # null on the instance: the inner value stays
            self.assertEqual(values["1:6"], [7, "fixed"])       # a non-null value is still written in
        finally:
            shutil.rmtree(d)

    def test_models_skip_generic_file_names(self):
        import json
        d = Path(tempfile.mkdtemp())
        old = C.SITE_CATALOG
        try:
            C.SITE_CATALOG = d / "index.json"
            site = "https://example.invalid/"
            C.SITE_CATALOG.write_text(json.dumps({"workflows": [
                {"url": site + "a.json", "models": [
                    {"name": "diffusion_pytorch_model.safetensors", "directory": "controlnet", "url": site + "other/diffusion_pytorch_model.safetensors"},
                    {"name": "ae.safetensors", "directory": "vae", "url": site + "flux/resolve/main/ae.safetensors"},
                    {"name": "t5.safetensors", "directory": "text_encoders", "url": site + "one/t5.safetensors"}]},
                {"url": site + "b.json", "models": [
                    {"name": "ae.safetensors", "directory": "vae", "url": site + "flux/blob/main/ae.safetensors?download=true"},
                    {"name": "t5.safetensors", "directory": "text_encoders", "url": site + "two/t5.safetensors"}]}]}),
                encoding="utf-8")
            cv = self.cv()
            cv.node("12")["widgets_values"][0] = "Union-Pro/diffusion_pytorch_model.safetensors"
            cv.node("11")["widgets_values"][0] = "t5.safetensors"
            cv.node("10")["widgets_values"][0] = "ae.safetensors"
            cv.save()
            out = self.do("models")
            line = lambda name: next(x for x in out if x.startswith(f"- {name} "))
            self.assertIn("URL: ?  (file name too generic to look up)", line("Union-Pro/diffusion_pytorch_model.safetensors"))
            self.assertIn("URL: ?  (file name too generic to look up)", line("t5.safetensors"))   # two different URLs
            self.assertIn("URL: " + site + "flux/resolve/main/ae.safetensors  (from", line("ae.safetensors"))   # the same file twice
        finally:
            C.SITE_CATALOG = old
            shutil.rmtree(d)

    def test_set_on_dict_values(self):
        cv = self.cv()
        n = cv.node("12")
        n["widgets_values"] = {"a": 1, "b": "x"}
        cv.save()
        self.do("set 12 a=2")
        self.assertEqual(self.cv().node("12")["widgets_values"], {"a": 2, "b": "x"})

    def test_width_keeps_right_aligned_column(self):
        self.do("put 42 origin")
        self.do("put 30 below 42")
        self.do("align right 42 30")
        self.assertNotEqual(self.rect("42")[2] - self.rect("42")[0], self.rect("30")[2] - self.rect("30")[0])
        r = self.rect("42")[2]
        self.do("width 42 30")
        self.assertEqual(round(self.rect("42")[2]), round(r))
        self.assertEqual(round(self.rect("30")[2]), round(r))

    def test_wide_gap_to_linked_neighbor(self):
        self.do("put 12 origin")
        self.do("put 30 right 12 wire gap 200")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("wide gap to a wired neighbour")])

    def test_python_error_becomes_stop_and_keeps_undo(self):
        before = len(list((self.dir / "canvas" / "t.hist").glob("*.json")))
        with self.assertRaises(C.Stop):
            self.do("rail 12.MODEL above to 30.model")   # the source is not placed
        with self.assertRaises(C.Stop):
            self.do("use")
        with self.assertRaises(C.Stop):
            self.do("layout no_such_plan.txt")
        self.assertEqual(len(list((self.dir / "canvas" / "t.hist").glob("*.json"))), before)

    def test_width_on_loader_is_kept(self):
        self.do("put 12 origin")
        self.do("put 10 below 12")
        self.do("put 42 right 12 gap 600")
        w = self.cv().node("42")["size"][0]
        self.assertGreater(w, self.cv().node("12")["size"][0])
        self.do("width 12 42")
        self.do("move 10 0 10")
        self.assertEqual(self.cv().node("12")["size"][0], w)

    def test_diff_runs(self):
        out = self.do("diff")
        self.assertTrue(out and out[0].startswith("differences"))

    def test_report_page(self):
        self.do("put 12 origin")
        self.do("put 30 right 12 wire")
        out = self.dir / "report.html"
        self.assertEqual(self.do(f"report {out}")[0], f"report page: {out}")
        text = out.read_text(encoding="utf-8")
        self.assertIn('id="data"', text)
        self.assertIn('<html lang="en">', text)
        self.assertIn("<title>Readable Node report</title>", text)
        self.assertNotIn("<script src", text)   # one file, nothing loaded from the network

    def test_replay_is_the_old_name_of_report(self):
        self.do("put 12 origin")
        out = self.dir / "old.html"
        self.assertEqual(self.do(f"replay {out}"), [f"report page: {out}"])
        self.assertIn('id="data"', out.read_text(encoding="utf-8"))

    def test_report_page_in_another_language_has_english_sentences(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        out = self.dir / "report.html"
        self.do(f"report {out} zh")
        self.assertIn('<html lang="zh">', out.read_text(encoding="utf-8"))
        data = report_data(out)
        self.assertEqual(data["lang"], "en")
        self.assertIn("below", data["canvases"][0]["steps"][-1]["s"])

    def test_report_page_in_japanese(self):
        plan = self.dir / "plan.txt"
        plan.write_text("put 12 origin\nput 30 right 12 wire\n", encoding="utf-8")
        self.do(f"layout {plan}")
        self.do("put 11 below 12")
        out = self.dir / "report.html"
        self.do(f"report {out} ja")
        text = out.read_text(encoding="utf-8")
        self.assertIn('<html lang="ja">', text)
        self.assertNotIn("<script src", text)
        data = report_data(out)
        steps = data["canvases"][0]["steps"]
        self.assertEqual(steps[0]["kind"], "build")          # copy and link changed nothing on the drawing: one step
        self.assertEqual(steps[1]["kind"], "layout")
        self.assertIn("（2 行）", steps[1]["s"])              # the plan's line count was recorded by layout
        self.assertTrue(any("水平" in d for d in steps[1]["d"]))   # and what its lines did, in plain words
        self.assertIn("の下に", steps[2]["s"])

    def test_layout_does_not_echo_what_lines_did(self):
        # correction 1020: the reply is an error log; what the plan's lines did is kept for the report page only
        plan = self.dir / "plan.txt"
        plan.write_text("put 12 origin\nput 30 right 12 wire\n", encoding="utf-8")
        out = self.do(f"layout {plan}")
        self.assertFalse(any("made horizontal" in x for x in out), out)
        notes = list(self.cv().s["layout_notes"].values())[-1]["notes"]
        self.assertTrue(any(x.startswith("line 2: made horizontal") for x in notes), notes)

    def test_loader_never_below_minimum_width(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        self.do("put 10 below 11")
        self.do("put 6 right 11")
        self.do("width 12 6")
        cv = self.cv()
        for i in ("11", "10"):
            self.assertGreaterEqual(cv.node(i)["size"][0], C.LOADER_MIN_W)

    def test_width_in_plan_is_not_undone_by_loader_widths(self):
        plan = self.dir / "plan.txt"
        plan.write_text("put 12 origin\nput 10 below 12\nwidth 10 42\nput 42 right 10 gap 400\n", encoding="utf-8")
        self.do(f"layout {plan}")
        # the plan is edited: the loader now starts again from its initial width, narrower than the aligned loaders
        plan.write_text("put 12 origin\nput 10 below 12\nwidth 10 26\nput 26 below 10\nput 9 right 12 gap 400\n", encoding="utf-8")
        self.do(f"layout {plan}")
        cv = self.cv()
        widths = {i: cv.node(i)["size"][0] for i in ("10", "26", "12")}
        self.assertEqual(widths["10"], widths["26"])
        self.assertGreaterEqual(widths["10"], C.LOADER_MIN_W)   # a loader is still never below the minimum
        self.do(f"layout {plan}")   # the same plan again gives the same widths
        self.assertEqual({i: self.cv().node(i)["size"][0] for i in widths}, widths)
        self.do("move 9 0 10")   # a later command aligns loaders again
        cv = self.cv()
        self.assertEqual(cv.node("10")["size"][0], cv.node("26")["size"][0])
        self.assertGreaterEqual(cv.node("12")["size"][0], C.LOADER_MIN_W)   # loaders not named in width are still aligned

    def test_sampler_custom_advanced_is_a_sampler(self):
        self.assertTrue(C.is_sampler(self.cv().node("13")))

    def test_rail_rejects_unknown_words(self):
        self.do("put 10 origin")
        self.do("put 8 right 10")
        self.do("unlink 8.vae")
        with self.assertRaises(C.Stop):
            self.do("rail 10.VAE above 8 gap 100 to 8.vae")

    def test_layout_undoes_titles_and_colors_of_the_previous_plan(self):
        self.do("title 42 Width")          # a title that is not the display name: the layout puts the name back
        plan = self.dir / "plan.txt"
        plan.write_text("put 12 origin\ncolor green 12\ntitle 30 Shift\n", encoding="utf-8")
        self.do(f"layout {plan}")
        self.assertEqual(self.cv().node("30").get("title"), "Shift")
        plan.write_text("put 12 origin\n", encoding="utf-8")
        self.do(f"layout {plan}")
        cv = self.cv()
        self.assertIsNone(cv.node("30").get("title"))
        self.assertNotEqual(cv.node("12").get("color"), C.COLORS["green"][0])
        self.assertIsNone(cv.node("42").get("title"))

    def test_column_gap_only_between_sources_of_one_node(self):
        self.do("put 12 origin")
        self.do("put 6 below 12 gap 200")   # a model loader above a prompt: different rows, not a column
        lines, _ = C.full_check(self.cv())
        self.assertFalse([x for x in lines if x.startswith("gap inside a column") and " 12 and 6" in x])


    def test_rail_counts_a_target_in_the_way_of_a_later_target(self):
        # 6 stands at the output height of 11, and 42 is further right at the same height: a rail drawn at the
        # output height would run on behind 6 to reach 42, so 6 is an obstacle (the wire into 6 itself is fine)
        self.do("put 11 origin")
        self.do("put 6 right 11 wire")
        self.do("put 42 right 6 top")
        self.do("unlink 6.clip 42.clip")
        out = self.do("rail 11.CLIP above 6 to 6.clip 42.clip")
        self.assertFalse([x for x in out if x.startswith("drawn at the output height")])
        cv = self.cv()
        self.assertEqual(C.hidden_wires(cv), [])
        lines = C.full_check(cv)[0]
        self.assertFalse([x for x in lines if x.startswith("rail needs no raising Reroute")])

    def test_a_shared_source_belongs_to_the_earlier_stage_even_before_it_is_placed(self):
        # the second stage takes the first stage's result and the same guider: the guider stays with the first stage
        self.do("add SamplerCustomAdvanced s2")
        self.do("link 13.0 s2.latent_image 22.0 s2.guider")
        self.do("put s2 origin")
        self.assertFalse(C.owns_source(self.cv(), "s2", "22"))
        self.assertTrue(C.owns_source(self.cv(), "13", "22"))

    def test_a_node_without_a_number_keeps_its_number_from_export_to_export(self):
        # a node named on the canvas (a Reroute it made, an id from a subgraph) gets a number once; a node added later
        # does not shift it, so the numbers a reviewer saw still name the same nodes
        self.do("add VAEDecode zb")
        self.do("put zb origin")
        cv = self.cv()
        _, first = cv.workflow()
        cv.work.save_cfg()
        self.do("put 13 right zb")   # a numbered node placed later: numbers after the highest one would move
        _, second = self.cv().workflow()
        self.assertEqual(first["zb"], second["zb"])
        self.assertNotEqual(second["13"], second["zb"])

    def test_link_gives_a_widget_its_input(self):
        # a value node handed out to a widget (text, seed): the widget gets its input slot, as in the frontend
        self.do("add PrimitiveStringMultiline s")
        self.do("link s.0 6.text")
        n = self.cv().node("6")
        self.assertEqual([(i["name"], bool(i.get("widget"))) for i in n["inputs"]], [("clip", False), ("text", True)])
        self.assertTrue(any(l["origin_id"] == "s" and l["target_input"] == "text" for l in self.cv().s["links"]))

    def test_a_rail_of_one_reroute_is_a_rail_too_close_to_another(self):
        # the level piece from a node's output to its only Reroute is part of its rail, as the pieces between Reroutes are
        self.do("put 13 origin")
        cv = self.cv()

        def reroute(rid, x, src, slot):
            cv.s["nodes"].append({"id": rid, "type": "Reroute", "mode": 0, "pos": [x, 0], "size": [C.REROUTE_W, C.REROUTE_H],
                                  "inputs": [{"name": "", "type": "*", "link": None}], "outputs": [{"name": "", "type": "*", "links": []}]})
            n = cv.node(rid)
            n["pos"][1] += cv.out_xy(src, slot)[1] - cv.in_xy(rid, "")[1]
            cv.add_link(src, slot, rid, "")
        reroute("ra", 600, "13", 0)
        reroute("rb", 650, "13", 1)
        lines = next(f for n, f in C.CHECKS if n == "overlapping rails")(cv, C._CheckCtx(cv))
        self.assertTrue([x for x in lines if x.startswith("rails too close")], lines)

    def test_a_rail_kept_off_another_rail_of_the_same_node_needs_its_raising_reroute(self):
        # two outputs of one node 20px apart both head rails: drawn at its output height, the second would run too close to
        # the first, so its raising Reroute is not one to take out
        self.do("put 13 origin")
        cv = self.cv()

        def reroute(rid, x, src, slot, dy):
            cv.s["nodes"].append({"id": rid, "type": "Reroute", "mode": 0, "pos": [x, 0], "size": [C.REROUTE_W, C.REROUTE_H],
                                  "inputs": [{"name": "", "type": "*", "link": None}], "outputs": [{"name": "", "type": "*", "links": []}]})
            n = cv.node(rid)
            n["pos"][1] += cv.out_xy(src, slot)[1] - cv.in_xy(rid, "")[1] + dy
            cv.add_link(src, slot, rid, "")
        chk = next(f for n, f in C.CHECKS if n == "rails that can run at the output height")
        reroute("rb", 650, "13", 1, 80)
        self.assertTrue([x for x in chk(cv, C._CheckCtx(cv)) if "(rb," in x])
        reroute("ra", 600, "13", 0, 0)
        self.assertFalse([x for x in chk(cv, C._CheckCtx(cv)) if "(rb," in x])

    def test_a_prompt_handed_out_from_one_line_string_is_fixed_in_the_plan(self):
        # the negative prompt was written in a text area: the value node handing it out is Text (Multiline), not String
        self.do("add CLIPTextEncode e")
        self.do("add PrimitiveString s")
        self.do("put e origin")
        self.do("put s left e")
        self.do("link s.0 e.text")
        hard = [x for x in C.hard_problems(self.cv()) if x.startswith("one-line text into a text area")]
        self.assertTrue(hard and "PrimitiveStringMultiline" in hard[0], hard)

    def test_a_model_rail_from_a_lora_runs_above_the_vae_rail_of_its_loader(self):
        # the model rail starts at a node of the model chain (30 after 12), the vae rail at the loader stacked with 12
        self.do("put 12 origin")
        self.do("put 10 below 12")
        self.do("put 30 right 12 wire")
        self.do("put 22 right 30 gap 900")
        self.do("put 8 right 22 top")
        self.do("rail 10.VAE above 12 to 8.vae")
        self.do("rail 30.MODEL below 10 to 22.model")
        cv = self.cv()
        chk = next(f for n, f in C.CHECKS if n == "model, vae and clip rails out of order")
        self.assertTrue([x for x in chk(cv, C._CheckCtx(cv)) if "rail runs above the MODEL rail" in x], chk(cv, C._CheckCtx(cv)))

    def test_a_rail_lifted_off_a_free_output_height_is_fixed_in_the_plan(self):
        # nothing stands at 11's output height up to 42: a rail written above 42 lifts it for nothing
        self.do("put 11 origin")
        self.do("put 42 right 11 gap 600")
        self.do("move 42 0 300")
        self.do("rail 11.CLIP above 42 to 42.clip")
        hard = [x for x in C.hard_problems(self.cv()) if x.startswith("rail needs no raising Reroute")]
        self.assertTrue(hard and "px off" in hard[0], hard)

    def test_layout_says_how_to_start_a_block(self):
        f = self.write_plan("block load 12 11\nput 11 below 12\n")
        with self.assertRaises(C.Stop) as e:
            self.do(f"layout {f}")
        msg = str(e.exception)
        self.assertIn("Place the first node of block load first: put 12 origin", msg)
        self.assertIn("put 12 right <placed node>", msg)
        ok = self.write_plan("block load 12 11\nput 12 origin\nput 11 below 12\n")
        self.do(f"layout {ok}")
        self.assertTrue(self.cv().placed(self.cv().node("11")))

    def test_set_before_copy_stops_and_says_copy_first(self):
        self.do("new u")
        with self.assertRaises(C.Stop) as e:
            self.do("set 6 text=hello")
        self.assertIn("copy 6 first", str(e.exception))
        self.do("copy 6")
        self.do("set 6 text=hello")
        self.assertEqual(self.cv().node("6")["widgets_values"][0], "hello")

if __name__ == "__main__":
    unittest.main()

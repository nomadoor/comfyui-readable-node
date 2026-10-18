"""Tests for the canvas (scripts/canvas.py). Python standard library only.

What is checked: a command moves only what it names. Alignment arithmetic is right. A stopped command changes nothing. Commands can be undone.
The subject is a hand-made Flux text to image in fixtures/ and an object_info cut down to the nodes it uses (runs without a server).

Usage: python3 -m unittest discover -s tests
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
# scripts/ next to tests/ (the published repo) or ../skill/scripts (the development folder)
SCRIPTS = next(p for p in (HERE.parent / "scripts", HERE.parent / "skill" / "scripts") if p.is_dir())
sys.path.insert(0, str(SCRIPTS))
import canvas as C  # noqa: E402
import geometry as G  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
SUBJECT = FIX / "flux_t2i.json"
OI = FIX / "object_info.json"


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

    def test_set_control_after_generate_alias(self):
        self.do("add PrimitiveInt s")
        self.do("set s control_after_generate=randomize")
        self.assertEqual(self.cv().node("s")["widgets_values"][1], "randomize")

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

    def test_backward_wire_is_hard(self):
        self.do("row 12 30 22")
        self.do("put 13 right 22")
        self.do("put 8 right 13")
        self.do("put 9 right 8")
        self.do("put 10 right 9")   # VAE right of the save node goes back two nodes to Decode
        lines, counts = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("backward wire (cannot be kept")])
        self.assertGreaterEqual(counts["backward wires that cannot be kept"], 1)

    def test_preview_above_source(self):
        self.do("add PreviewImage p")
        self.do("link 8.IMAGE p.images")
        self.do("put 8 origin")
        self.do("put p above 8")
        lines, _ = C.full_check(self.cv())
        self.assertTrue([x for x in lines if x.startswith("PreviewImage is above its source")])

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

    def write_plan(self, text):
        f = self.dir / "plan.txt"
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
        self.assertTrue(any(x.startswith("■ ") or x == "no problems" for x in out1))

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

    def test_inputs_centers_sampler_custom(self):
        self.do("copy 25 16 17")
        self.do("link 25.NOISE 13.noise 16.SAMPLER 13.sampler 17.SIGMAS 13.sigmas 30.MODEL 17.model")
        self.do("put 13 origin")
        self.do("move 13 2000 600")
        self.do("inputs 13")
        cv = self.cv()
        srcs = list({l["origin_id"] for l in cv.s["links"] if l["target_id"] == "13"})
        col = cv.bbox(srcs)
        r = self.rect("13")
        self.assertLess(abs((col[1] + col[3]) / 2 - (r[1] + r[3]) / 2), 1)

    def test_image_nodes_min_size(self):
        self.do("add SaveImage sv")
        w, h = self.cv().node("sv")["size"]
        self.assertGreaterEqual(w, 503)
        self.assertGreaterEqual(h, 574)

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

    def test_replay_page(self):
        self.do("put 12 origin")
        self.do("put 30 right 12 wire")
        out = self.dir / "replay.html"
        self.do(f"replay {out}")
        text = out.read_text(encoding="utf-8")
        self.assertIn('id="data"', text)
        self.assertNotIn("<script src", text)   # one file, nothing loaded from the network

    def test_layout_reports_what_lines_did(self):
        plan = self.dir / "plan.txt"
        plan.write_text("put 12 origin\nput 30 right 12 wire\n", encoding="utf-8")
        out = self.do(f"layout {plan}")
        self.assertTrue(any(x.startswith("  line 2: made horizontal") for x in out))

    def test_loader_never_below_minimum_width(self):
        self.do("put 12 origin")
        self.do("put 11 below 12")
        self.do("put 10 below 11")
        self.do("put 6 right 11")
        self.do("width 12 6")
        cv = self.cv()
        for i in ("11", "10"):
            self.assertGreaterEqual(cv.node(i)["size"][0], C.LOADER_MIN_W)

    def test_sampler_custom_advanced_is_a_sampler(self):
        self.assertTrue(C.is_sampler(self.cv().node("13")))

    def test_rail_rejects_unknown_words(self):
        self.do("put 10 origin")
        self.do("put 8 right 10")
        self.do("unlink 8.vae")
        with self.assertRaises(C.Stop):
            self.do("rail 10.VAE above 8 gap 100 to 8.vae")

    def test_layout_undoes_titles_and_colors_of_the_previous_plan(self):
        self.do("title 42 Width")          # build-time title stays
        plan = self.dir / "plan.txt"
        plan.write_text("put 12 origin\ncolor green 12\ntitle 30 Shift\n", encoding="utf-8")
        self.do(f"layout {plan}")
        self.assertEqual(self.cv().node("30").get("title"), "Shift")
        plan.write_text("put 12 origin\n", encoding="utf-8")
        self.do(f"layout {plan}")
        cv = self.cv()
        self.assertIsNone(cv.node("30").get("title"))
        self.assertNotEqual(cv.node("12").get("color"), C.COLORS["green"][0])
        self.assertEqual(cv.node("42").get("title"), "Width")

    def test_column_gap_only_between_sources_of_one_node(self):
        self.do("put 12 origin")
        self.do("put 6 below 12 gap 200")   # a model loader above a prompt: different rows, not a column
        lines, _ = C.full_check(self.cv())
        self.assertFalse([x for x in lines if x.startswith("gap inside a column") and " 12 and 6" in x])


if __name__ == "__main__":
    unittest.main()

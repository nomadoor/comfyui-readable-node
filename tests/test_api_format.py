"""Tests for reading an API-format workflow (scripts/api_format.py). Python standard library only.

What is checked: an API-format file opens on the canvas. Nodes are placed in columns by level as the frontend's
graph.arrange() does, values go into the widgets, [id, slot] become wires, and the original view says it was API format.

Usage: python3 -m unittest discover -s tests
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = next(p for p in (HERE.parent / "skills" / "comfyui-readable-node" / "scripts", HERE.parent / "skill" / "scripts")
               if p.is_dir())
sys.path.insert(0, str(SCRIPTS))
import api_format as AF  # noqa: E402
import canvas as C  # noqa: E402

OI = HERE / "fixtures" / "object_info.json"

# ids as an API export writes them: not in order, and one from inside a subgraph ("12:3")
API = {
    "12:3": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["2", 0]}, "_meta": {"title": "VAE Decode"}},
    "10": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["5", 0], "guider": ["7", 0], "sampler": ["8", 0],
                                                             "sigmas": ["9", 0], "latent_image": ["4", 0]}},
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "3": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp16.safetensors", "clip_name2": "clip_l.safetensors",
                                                     "type": "flux"}},
    "4": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 832, "height": 1216, "batch_size": 1}},
    "5": {"class_type": "RandomNoise", "inputs": {"noise_seed": 42}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cat", "clip": ["3", 0]}, "_meta": {"title": "Positive"}},
    "7": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["6", 0]}},
    "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
    "9": {"class_type": "BasicScheduler", "inputs": {"scheduler": "simple", "steps": 20, "denoise": 1.0, "model": ["1", 0]}},
    "11": {"class_type": "SaveImage", "inputs": {"filename_prefix": "out", "images": ["12:3", 0]}},
}


class ApiFormatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oi = json.loads(OI.read_text(encoding="utf-8"))
        cls.ui, cls.warns = AF.to_ui(API, cls.oi)
        cls.nodes = {str(n["id"]): n for n in cls.ui["nodes"]}

    def test_detects_api_format(self):
        self.assertTrue(AF.is_api(API))
        self.assertFalse(AF.is_api({"nodes": [], "links": []}))

    def test_ids_in_object_keys_order_and_colon_replaced(self):
        self.assertEqual([str(n["id"]) for n in self.ui["nodes"]],
                         ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12_3"])

    def test_values_and_wires(self):
        self.assertEqual(self.nodes["4"]["widgets_values"], [832, 1216, 1])
        self.assertEqual(self.nodes["6"]["title"], "Positive")
        self.assertNotIn("title", self.nodes["12_3"])   # same as the display name
        self.assertEqual(len(self.ui["links"]), 12)
        save_in = self.nodes["11"]["inputs"][0]
        link = next(l for l in self.ui["links"] if l[0] == save_in["link"])
        self.assertEqual((str(link[1]), link[3]), ("12_3", 11))
        self.assertEqual(self.warns, [])

    def test_columns_by_level_like_graph_arrange(self):
        x = {k: n["pos"][0] for k, n in self.nodes.items()}
        # level 1: loaders and nodes without wired inputs; 2: what they feed; ...
        self.assertEqual({x[k] for k in ("1", "2", "3", "4", "5", "8")}, {100})
        self.assertEqual(x["6"], x["9"])
        self.assertLess(x["6"], x["7"])
        self.assertLess(x["7"], x["10"])
        self.assertLess(x["10"], x["12_3"])
        self.assertLess(x["12_3"], x["11"])
        # in a column: from y = 130, each node height + 130 down, in topological order
        col = sorted((n for n in self.ui["nodes"] if n["pos"][0] == 100), key=lambda n: n["pos"][1])
        self.assertEqual(col[0]["pos"][1], 130)
        for a, b in zip(col, col[1:]):
            self.assertEqual(b["pos"][1], a["pos"][1] + a["size"][1] + 130)
        widest = max(n["size"][0] for n in col)
        self.assertEqual(x["6"], 100 + max(widest, 100) + 100)

    def test_opens_on_the_canvas_and_the_original_view_says_api(self):
        d = Path(tempfile.mkdtemp())
        try:
            src = d / "api.json"
            src.write_text(json.dumps(API), encoding="utf-8")
            out = C.run_cmd(C.Work(d / "w"), f"open {src} {OI}")
            self.assertTrue(any(x.startswith("API format: 12 nodes") for x in out))
            self.assertTrue(any(x.startswith("read: 12 nodes, 12 wires") for x in out))
            view = C._original_view(d / "w" / "source.ui.json", self.oi, C._Intern())
            self.assertTrue(view["api"])
            self.assertEqual(len({(n[1], n[2]) for n in view["nodes"]}), 12)   # no two nodes at the same place
        finally:
            shutil.rmtree(d)


# VideoHelperSuite's Load Video, cut down (its frontend saves the values keyed by name)
VHS_LOAD_VIDEO = {
    "input": {"required": {"video": [["a.mp4"], {"video_upload": True}], "force_rate": ["FLOAT", {"default": 0}],
                           "custom_width": ["INT", {"default": 0}], "custom_height": ["INT", {"default": 0}],
                           "frame_load_cap": ["INT", {"default": 0}], "skip_first_frames": ["INT", {"default": 0}],
                           "select_every_nth": ["INT", {"default": 1}]},
              "optional": {"vae": ["VAE"], "format": [["None", "Wan"], {"default": "None"}]}},
    "input_order": {"required": ["video", "force_rate", "custom_width", "custom_height", "frame_load_cap",
                                 "skip_first_frames", "select_every_nth"], "optional": ["vae", "format"]},
    "output": ["IMAGE", "INT"], "output_name": ["IMAGE", "frame_count"], "name": "VHS_LoadVideo",
    "display_name": "Load Video (Upload)", "category": "video", "output_node": False,
    "python_module": "custom_nodes.comfyui-videohelpersuite"}


class NamedValuesTest(unittest.TestCase):
    def test_vhs_values_are_keyed_by_name(self):
        oi = json.loads(OI.read_text(encoding="utf-8"))
        oi["VHS_LoadVideo"] = VHS_LOAD_VIDEO
        api = {"1": {"class_type": "VHS_LoadVideo", "inputs": {
            "video": "a.mp4", "force_rate": 16, "custom_width": 0, "custom_height": 0, "frame_load_cap": 125,
            "skip_first_frames": 0, "select_every_nth": 1, "format": "None"}}}
        ui, _ = AF.to_ui(api, oi)
        v = ui["nodes"][0]["widgets_values"]
        self.assertIsInstance(v, dict)
        self.assertEqual((v["frame_load_cap"], v["skip_first_frames"], v["force_rate"]), (125, 0, 16))
        self.assertNotIn("upload", v)

    def test_vhs_load_video_counts_as_a_loading_node_that_shows_a_preview(self):
        self.assertEqual(C.image_kind("VHS_LoadVideo", {"VHS_LoadVideo": VHS_LOAD_VIDEO}), "load")


if __name__ == "__main__":
    unittest.main()

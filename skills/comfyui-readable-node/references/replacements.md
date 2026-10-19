# Replacement dictionary

Replacements for custom nodes and deprecated core nodes that have been confirmed by reading the source once. Replacements decided by the node's name are here; techniques that rebuild the form of several nodes are in techniques.md. Those listed here may be used without investigating again. For those not listed here, read the source following the steps in SKILL.md and write it in the table of the understanding document.

A custom node not listed here is decided by reading its source. For a custom node that is not installed in ComfyUI, read only the files you need.
1. Find the repository. If the node's properties have `cnr_id`, use `repository` from `https://api.comfy.org/nodes/<cnr_id>`. Otherwise `aux_id` (if it is `owner/repo`, GitHub). If neither exists, look up `https://api.comfy.org/comfy-nodes/<type>/node` with the node's type name. If it is not there either, search ComfyUI-Manager's `https://raw.githubusercontent.com/Comfy-Org/ComfyUI-Manager/main/extension-node-map.json`.
2. Read `__init__.py` by its raw URL, and follow `NODE_CLASS_MAPPINGS` to the file that has the node's type name.
3. Read only that file. If `ver` is a commit, read the one at that commit.
- Do not clone. Do not run code you fetched. Do not put it into ComfyUI's custom_nodes.
- If it is found nowhere, leave it unreplaced, and write in the report "the source was not found, so this could not be determined".

For where replacement stops, see SKILL.md.

Write what changes through a replacement in the report (not in a Note). For replacements that change the model file or its location, put the new model in the list of the overview and models Note.

Each row's "Where verified" is which source it was verified in. When the node's version differs, its internals can change, so verify again when the workflow's `ver` differs greatly.

## Use core

| custom node | How to build with core | What changes / what to watch out for | Where verified |
|---|---|---|---|
| VHS_VideoCombine (output) | CreateVideo + SaveVideo (copy format, codec, crf) | Keep it only when it saves as GIF (core's Save Video is only mp4, mkv, webm) | Decided by nomadoor. comfy_extras/nodes_video.py |
| Concatenate Text (StringConcatenate) | One Format Text (StringFormat). The texts to join as a, b, c…, the separators in f_string (`{a}, {b}\n{c}` and so on). Whether chained or only one (two inputs) | If an empty text goes in, the separator stays (`{a}, {b}` with a = "cat", b = "" gives "cat, "). Concatenate Text does the same, so nothing changes from the original | Decided by nomadoor. comfy_extras/nodes_string.py (StringConcatenate, StringFormat) |
| easy fullLoader (easy-use) | Load Checkpoint + CLIP Set Last Layer (clip_skip) + CLIP Text Encode ×2 + Empty Latent Image. LoRA and ControlNet inside the loader are also brought out as core nodes | If the prompt weight interpretation (token_normalization, weight_interpretation) is not the default (none, comfy), how the weights act changes slightly. Write it in the report | py/nodes/loaders.py and py/libs/adv_encode.py of easy-use 130c1b5 |
| Power Lora Loader (rgthree) | One Load LoRA per enabled row, in order. How each LoRA's clip is handled is in the LoRA item of techniques.md | Delete rows that are off and rows set to None. Internally it only calls LoraLoader in order | rgthree source |
| KSampler (Efficient), KSampler Adv. (Efficient) | KSampler / KSamplerAdvanced + VAE Decode | It displayed the image itself (an output node), so if a place to view it is needed, Preview Image | efficiency-nodes source |
| HighRes-Fix Script (efficiency, both) | VAE Decode → Upscale Image (using Model) → Resize Image/Mask (scale by multiplier) → VAE Encode → KSampler | The Upscale Latent By at factor 1 inside does nothing, so do not include it | efficiency-nodes source |
| easy controlnetStack | Load ControlNet Model + Apply ControlNet (vae too) | Rows after num_controlnet have no effect | easy-use source |
| SDXLEmptyLatentSizePicker+ (essentials) | Empty Latent Image | Enter the size that is in effect with the width / height overrides | essentials source |
| ImageResize+ (essentials, keep proportion) | For a square frame, Resize Image/Mask's scale longer dimension (rounding is also the same). For a rectangular frame, rebuild it in the form of techniques.md "Build the resolution from what the resolution is for" (scale total pixels → round to the model's multiple → Get Image Size) | With a rectangular frame the output size differs from the original. Write it in the report | essentials source (execute of ImageResize in image.py). Decided by nomadoor (rectangular frame) |
| ImageResizeKJ (KJNodes, v1. keep_proportion on, width and height the same) | Resize Image/Mask with "scale longer dimension", followed by "scale to multiple" (multiple of 8). The size and the center crop come out the same | KJ crops first and then scales, while core scales to cover and then crops, so the pixels differ slightly. Does not apply when the box is a rectangle, or to ImageResizeKJv2 | scale_to_multiple_cover in comfy_extras/nodes_post_processing.py |
| ImageResize+ (essentials, stretch) | Resize Image/Mask's match size (crop disabled) | | essentials source |
| ImagePadKJ + AILab_ICLoRAConcat | Stitch Images (right, copy spacing and color). For the mask on the right, Stitch a black and a white Empty Image with the same spacing, then Convert Image to Mask | ImagePadKJ's color "1,1,1" is white in the 0 to 1 range | KJNodes and ComfyUI-RMBG source |
| AnimaLLLiteApply_sdscripts | Load Model Patch (ModelPatchLoader) + Apply Anima LLLite | The model's location changes from controlnet to model_patches | Decided by nomadoor |
| Color Match (KJNodes, ColorMatch / ColorMatchV2) | Transfer Color (ColorTransfer). Choose the closest method from reinhard_lab, mkl_lab, histogram | hm-mvgd-hm and others are not in core, so the color values change slightly. Write it in the report | comfy_extras/nodes_post_processing.py |
| SUPIR (kijai's SUPIR_model_loader, first_stage, encode, conditioner, sample, decode) | Load Model Patch (the SUPIR model) + Apply SUPIR Patch (SUPIRApply: model, model_patch, vae, image, strength, restore_cfg) + an ordinary KSampler and VAE Decode | The sampler (RestoreEDMSampler) and tile settings change in core. The shape of the output is the same. Write it in the report | comfy_extras/nodes_model_patch.py, comfy/ldm/supir/ |
| LoadImageCrop (obvpm) | Load Image + Crop Image (ImageCropV2). The crop area is decided by dragging on the Crop Image node (the user's operation is kept) | Place Crop Image even when crop is empty (the whole image). Crop Image's default area is 512×512, so the image is cropped until the user sets the frame. Say so in one line in the Usage of a Note. max_megapixels (shrinks) and aspect (fixes the frame's ratio) are not in Crop Image. At 0 / free they are the same. If they are used, write it in the report | obvpm's load_image_crop.py, comfy_extras/nodes_images.py, the frontend's useImageCrop.ts |
| RIFE VFI (Frame-Interpolation) | Load Frame Interpolation Model + Run Frame Interpolation Model (copy multiplier) | Core reads RIFE in the v4.25-and-later form (rife_v4.25, rife_v4.26 in Comfy-Org/frame_interpolation, and so on) and FILM. Loading requires the encode layers and 5 blocks, so earlier forms (rife49.pth and so on) are probably not readable (not tested). The model file changes | comfy_extras/nodes_frame_interpolation.py |
| LLM Text Processor (KingManiya, a GGUF LLM via llama.cpp) | Generate Text (TextGenerate). Load the LLM with CLIPLoader (Qwen3.5, Qwen3-VL and so on can generate text in core). To have it describe an image, use the image input | GGUF cannot be loaded, so the model file changes to safetensors | qwen35.py and qwen3vl.py in comfy/text_encoders |
| SaveImageKJ (KJNodes) with no caption connected | Save Image | | nodes/image_nodes.py of KJNodes |
| Image Comparer (rgthree) | Compare Images (ImageCompare). Connect image_a and image_b as they are | core's Compare Images shows the side-by-side comparison only in Nodes 2.0 | py/image_comparer.py of rgthree, comfy_extras/nodes_image_compare.py |
| ImagesGridByColumns (all images the same size, gap 0) | Make Image Grid (ImageGrid). columns is max_columns, cell_width and cell_height are the image size, padding is 0 | Make Image Grid is experimental | src/utils/images_grid.py of images-grid-comfy-plugin, comfy_extras/nodes_dataset.py |
| ShowText\|pysssss (a node that displays the value it receives and passes it straight on) | Take it out of the flow and connect before and after directly, then branch from the value you want to see into Preview as Text (PreviewAny). How to build is "Do not put a display node in the flow; put it on a branch" in techniques.md | | py/show_text.py of pysssss (displays the text it receives and returns it as the output as is), comfy_extras/nodes_preview_any.py |
| MathExpression\|pysssss | Math Expression (the same expression) | Check with values that the expression is the same. If the pysssss expression uses the size of an image or latent (a.width, a.height), widget values of other nodes, randomint, randomchoice or iif, it cannot be written as is in core's Math Expression (core has only numbers and sum, min, max, abs, round, pow, sqrt, ceil, floor, log, sin, cos, tan, int, float) | py/math_expression.py of pysssss, comfy_extras/nodes_math.py |

## Deprecated core nodes

| deprecated node | New node | What changes / what to watch out for | Where verified |
|---|---|---|---|
| Apply ControlNet (DEPRECATED) (ControlNetApply) | Apply ControlNet (ControlNetApplyAdvanced) | The old one receives one conditioning and also acts on the negative side. The new one receives positive and negative, so connect negative too | ControlNetApply and ControlNetApplyAdvanced in nodes.py (control_apply_to_uncond) |
| Apply Controlnet with VAE (ControlNetApplySD3) | Apply ControlNet (ControlNetApplyAdvanced). `canvas open` replaces it when reading the original | Inputs and outputs have the same names. The calculation is the same (no successor is named) | comfy_extras/nodes_sd3.py and ControlNetApplyAdvanced in nodes.py |

## May be removed (no effect on the result)

| custom node | Reason | Where verified |
|---|---|---|
| PlaySound, easy cleanGpuUsed, easy clearCacheAll | Completion sound, freeing memory | Decided by nomadoor |
| BlehModelPatchFastTerminate | Only makes the response to interruption faster | bleh source |
| FromDetailerPipe (Impact Pack) | Only takes the inputs out as they are. Connect directly from where the inputs come from | Impact Pack source |

## Keep (not the same in core)

These too are kept only when that workflow uses a function core does not have. If it does not use one, replace it with core.

| custom node | Reason to keep | Where verified |
|---|---|---|
| ClownsharKSampler_Beta (RES4LYF) | Special samplers are kept as an exception to where replacement stops. eta (adds and removes noise each step), methods such as ralston, and bongmath are not in core. Core does have methods that evaluate twice (heun, dpmpp_2s_ancestral, seeds_2) and samplers with eta, but the sampler the author chose stays custom | beta/samplers.py of RES4LYF, object_info |
| Crop Image TargetSize (JPS) | There is no core node that receives the crop area through number wires and crops (Crop Image (DEPRECATED) is deprecated. Crop Image [ImageCropV2]'s area is only a frame dragged on the node, and is not received through wires [socketless]) | comfy_extras/nodes_images.py |
| ImagesGridByColumns where the image sizes are not uniform or gap is not 0 | It lines images up at the size of the first image and fills the gaps (gap) with white. core's Make Image Grid (experimental) shrinks cells to cell_width × cell_height and fills the gaps (padding) with black | src/utils/images_grid.py of images-grid-comfy-plugin, comfy_extras/nodes_dataset.py |
| Patch Sage Attention KJ | core's Model Attention Backend cannot select sage. The only way to use sage in core is the launch option --use-sage-attention | comfy_extras/nodes_model_advanced.py, comfy/ldm/modules/attention.py |
| UnetLoaderGGUF | core has no node that loads GGUF | |
| SaveImageKJ (KJNodes) with a caption connected | It saves the text together as a .txt. core's Save Image-Text (to Folder) can do this too, but it is experimental and does not put the workflow into the PNG (a node that writes out training data) | nodes/image_nodes.py of KJNodes, comfy_extras/nodes_dataset.py |
| A resize that "shrinks only when large" (conditional ones such as ImageResize+) | Without the condition, small images are also enlarged (the output size changes). Write the core way to build it as a suggestion in the Caution of a Note | Decided by nomadoor |

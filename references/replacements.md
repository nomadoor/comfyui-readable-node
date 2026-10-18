# Replacement dictionary

Replacements for custom nodes that have been confirmed by reading the source once. Those listed here may be used without investigating again. For those not listed here, read the source following the steps in SKILL.md and write it in the table of the understanding document.

For the replacement boundary, see SKILL.md. If only the model file the user installs changes, use core (except GGUF loaders). (Undecided: whether the differences of a replacement are written in the Note, or only in the report. See SKILL.md.)

Each row's "Where verified" is which source it was verified in. When the node's version differs, its internals can change, so verify again when the workflow's `ver` differs greatly.

## Use core

| custom node | How to build with core | What changes / what to watch out for | Where verified |
|---|---|---|---|
| VHS_VideoCombine (output) | CreateVideo + SaveVideo (copy format, codec, crf) | Replace unless there is a special reason | Decided by the skill author |
| Concatenate Text (StringConcatenate) | One Format Text (StringFormat). The texts to join as a, b…, the separators in f_string | Whether chained or only one | Decided by the skill author. techniques.md |
| easy fullLoader (easy-use) | Load Checkpoint + CLIP Set Last Layer (clip_skip) + CLIP Text Encode ×2 + Empty Latent Image. LoRA and ControlNet inside the loader are also brought out as core nodes | If the prompt weight interpretation (token_normalization, weight_interpretation) is not the default (none, comfy), how the weights act changes slightly. Write it in the Note and the report | py/nodes/loaders.py and py/libs/adv_encode.py of easy-use 130c1b5 |
| Power Lora Loader (rgthree) | One Load LoRA per enabled row, in order. Check whether the LoRA acts on the text encoder (whether the safetensors header has text encoder keys); use LoraLoader only for those that do, LoraLoaderModelOnly for the rest (do not decide by whether the CLIP link is connected) | Delete rows that are off and rows set to None. Internally it only calls LoraLoader in order | rgthree source |
| KSampler (Efficient), KSampler Adv. (Efficient) | KSampler / KSamplerAdvanced + VAE Decode | It displayed the image itself (an output node), so if a place to view it is needed, Preview Image | efficiency-nodes source |
| HighRes-Fix Script (efficiency, both) | VAE Decode → Upscale Image (using Model) → Resize Image/Mask (scale by multiplier) → VAE Encode → KSampler | The Upscale Latent By at factor 1 inside does nothing, so do not include it | efficiency-nodes source |
| easy controlnetStack | Load ControlNet Model + Apply ControlNet (vae too) | Rows after num_controlnet have no effect | easy-use source |
| SDXLEmptyLatentSizePicker+ (essentials) | Empty Latent Image | Enter the size that is in effect with the width / height overrides | essentials source |
| ImageResize+ (essentials, keep proportion) | If width and height are the same (a square frame), Resize Image/Mask's scale longer dimension | Rounding is also the same. With a frame whose width and height differ, it is not the same (ImageResize+ fits into the frame with a factor of min(width / original width, height / original height). With a frame of 832×480, a 1024×1024 image becomes 480×480; with scale longer dimension 832 it becomes 832×832) | essentials source (execute of ImageResize in image.py) |
| ImageResize+ (essentials, stretch) | Resize Image/Mask's match size (crop disabled) | | essentials source |
| ImagePadKJ + AILab_ICLoRAConcat | Stitch Images (right, copy spacing and color). For the mask on the right, Stitch a black and a white Empty Image with the same spacing, then Convert Image to Mask | ImagePadKJ's color "1,1,1" is white in the 0 to 1 range | KJNodes and ComfyUI-RMBG source |
| AnimaLLLiteApply_sdscripts | Load Model Patch (ModelPatchLoader) + Apply Anima LLLite | The model's location changes from controlnet to model_patches. Write it in the model Note | Decided by the skill author |
| Color Match (KJNodes, ColorMatch / ColorMatchV2) | Transfer Color (ColorTransfer). Choose the closest method from reinhard_lab, mkl_lab, histogram | hm-mvgd-hm and others are not in core, so the color values change slightly. Write it in the Note and the report | comfy_extras/nodes_post_processing.py |
| SUPIR (kijai's SUPIR_model_loader, first_stage, encode, conditioner, sample, decode) | Load Model Patch (the SUPIR model) + Apply SUPIR Patch (SUPIRApply: model, model_patch, vae, image, strength, restore_cfg) + an ordinary KSampler and VAE Decode | The sampler (RestoreEDMSampler) and tile settings change in core. The shape of the output is the same. Write it in the Note and the report | comfy_extras/nodes_model_patch.py, comfy/ldm/supir/ |
| A Format Text that joins an instruction and the body text and feeds it into Text Generate | Put the instruction into Text Generate's system_prompt (optional) | The behavior changes slightly (it is passed as system). Write it in the Note and the report | TextGenerate in object_info |
| LoadImageCrop (obvpm) | Load Image + Crop Image (ImageCropV2). The crop area is decided by dragging on the Crop Image node (the user's operation is kept) | Place Crop Image even when crop is empty (the whole image). Crop Image's default area is 512×512, so the image is cropped until the user sets the frame. Say so in one line in the Note's usage. max_megapixels (shrinks) and aspect (fixes the frame's ratio) are not in Crop Image. At 0 / free they are the same. If they are used, write it in the Note and the report | obvpm's load_image_crop.py, comfy_extras/nodes_images.py, and the frontend's useImageCrop.ts |
| RIFE VFI (Frame-Interpolation) | Load Frame Interpolation Model + Run Frame Interpolation Model (copy multiplier) | Core reads RIFE in the v4.25-and-later form (rife_v4.25, rife_v4.26 in Comfy-Org/frame_interpolation, etc.) and FILM. Loading requires the encode layers and 5 blocks, so earlier forms (rife49.pth, etc.) are probably not readable (not tested). The model file changes. Write it in the model Note | comfy_extras/nodes_frame_interpolation.py |
| LLM Text Processor (KingManiya, a GGUF LLM via llama.cpp) | Generate Text (TextGenerate). Load the LLM with CLIPLoader (Qwen3.5, Qwen3-VL, etc. can generate text in core). To have it describe an image, use the image input | GGUF cannot be loaded, so the model file changes to safetensors. Write it in the model Note | qwen35.py and qwen3vl.py in comfy/text_encoders |
| MathExpression\|pysssss, easy's math nodes (compare, ifElse, mathInt, etc.) | Math Expression (the same expression) | Check with values that the expression is the same | |

## May be deleted (no effect on the result)

| custom node | Reason | Where verified |
|---|---|---|
| PlaySound, easy cleanGpuUsed, easy clearCacheAll | Completion sound, freeing memory | Decided by the skill author |
| BlehModelPatchFastTerminate | Only makes the response to interruption faster | bleh source |
| FromDetailerPipe (Impact Pack) | Only takes the inputs out as they are. Connect directly from the origin | Impact Pack source |
| Image Comparer (rgthree), ImageCompare | Only for comparing by eye. The canvas's open deletes them | |

## Keep (not the same in core)

| custom node | Reason to keep | Where verified |
|---|---|---|
| ClownsharKSampler_Beta (RES4LYF) | Special samplers are kept as an exception to the replacement boundary. eta (adds and removes noise each step), methods such as ralston, and bongmath are not in core. Core does have methods that evaluate twice (heun, dpmpp_2s_ancestral, seeds_2) and samplers with eta, but the sampler the author chose stays custom | RES4LYF's beta/samplers.py, object_info |
| Crop Image TargetSize (JPS) | There is no core node that receives the crop area through number links and crops (Crop Image (DEPRECATED) is deprecated. Crop Image [ImageCropV2]'s area is only a frame dragged on the node and is not received through links [socketless]) | comfy_extras/nodes_images.py |
| SaveImageKJ | core's Save Image has no feature to save text as a .txt alongside | |
| ImagesGridByColumns | core's Make Image Grid is experimental; it shrinks cells to a fixed size and also adds margins. The shape of the output image changes | |
| Patch Sage Attention KJ | core's Model Attention Backend cannot select sage. The only way to use sage in core is the launch option --use-sage-attention | comfy_extras/nodes_model_advanced.py, comfy/ldm/modules/attention.py |
| UnetLoaderGGUF | core has no node that loads GGUF | |
| A resize that "shrinks only when large" (conditional ones such as ImageResize+) | Without the condition, small images are also enlarged (the output size changes). Write the core way to build it in the Note as a suggestion | Decided by the skill author |

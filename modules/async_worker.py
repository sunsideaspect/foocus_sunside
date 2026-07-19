import threading

from modules.patch import PatchSettings, patch_settings, patch_all
import modules.config

_inpaint_mask_import_error = None
try:
    from extras.inpaint_mask import generate_mask_from_image, SAMOptions
except Exception as e:
    generate_mask_from_image = None
    _inpaint_mask_import_error = e

    # Keep startup alive when optional inpaint-mask dependencies are broken.
    class SAMOptions:  # type: ignore[no-redef]
        def __init__(self,
                     dino_prompt='',
                     dino_box_threshold=0.3,
                     dino_text_threshold=0.25,
                     dino_erode_or_dilate=0,
                     dino_debug=False,
                     max_detections=2,
                     model_type='vit_b'):
            self.dino_prompt = dino_prompt
            self.dino_box_threshold = dino_box_threshold
            self.dino_text_threshold = dino_text_threshold
            self.dino_erode_or_dilate = dino_erode_or_dilate
            self.dino_debug = dino_debug
            self.max_detections = max_detections
            self.model_type = model_type

patch_all()


class AsyncTask:
    def __init__(self, args):
        from modules.flags import Performance, MetadataScheme, ip_list, disabled, cn_ip_face
        from modules.util import get_enabled_loras
        from modules.config import default_max_lora_number
        import args_manager

        self.args = args.copy()
        self.yields = []
        self.results = []
        self.last_stop = False
        self.processing = False

        self.performance_loras = []

        if len(args) == 0:
            return

        args.reverse()
        self.generate_image_grid = args.pop()
        self.prompt = args.pop()
        self.negative_prompt = args.pop()
        self.style_selections = args.pop()

        self.performance_selection = Performance(args.pop())
        self.steps = self.performance_selection.steps()
        self.original_steps = self.steps

        self.aspect_ratios_selection = args.pop()
        self.image_number = args.pop()
        self.pro_mode_enabled = modules.config.default_pro_mode_enabled
        self.pro_mode_keep_count = modules.config.default_pro_mode_keep_count
        self.pro_mode_min_images = modules.config.default_pro_mode_min_images
        self.pro_mode_detail_pass_enabled = modules.config.default_pro_mode_detail_pass_enabled
        self.pro_mode_detail_prompts = modules.config.default_pro_mode_detail_prompts
        self.pro_mode_detail_inpaint_engine = modules.config.default_pro_mode_detail_inpaint_engine
        self.pro_mode_detail_strength = modules.config.default_pro_mode_detail_strength
        self.pro_mode_detail_respective_field = modules.config.default_pro_mode_detail_respective_field
        self.pro_mode_detail_erode_or_dilate = modules.config.default_pro_mode_detail_erode_or_dilate
        self.pro_mode_structure_control_enabled = modules.config.default_pro_mode_structure_control_enabled
        self.pro_mode_structure_use_canny = modules.config.default_pro_mode_structure_use_canny
        self.pro_mode_structure_use_cpds = modules.config.default_pro_mode_structure_use_cpds
        self.pro_mode_structure_canny_stop = modules.config.default_pro_mode_structure_canny_stop
        self.pro_mode_structure_canny_weight = modules.config.default_pro_mode_structure_canny_weight
        self.pro_mode_structure_cpds_stop = modules.config.default_pro_mode_structure_cpds_stop
        self.pro_mode_structure_cpds_weight = modules.config.default_pro_mode_structure_cpds_weight
        self.output_format = args.pop()
        self.seed = int(args.pop())
        self.read_wildcards_in_order = args.pop()
        self.sharpness = args.pop()
        self.cfg_scale = args.pop()
        self.base_model_name = args.pop()
        self.refiner_model_name = args.pop()
        self.refiner_switch = args.pop()
        self.loras = get_enabled_loras([(bool(args.pop()), str(args.pop()), float(args.pop())) for _ in
                                        range(default_max_lora_number)])
        self.input_image_checkbox = args.pop()
        self.current_tab = args.pop()
        self.uov_method = args.pop()
        self.uov_input_image = args.pop()
        self.outpaint_selections = args.pop()
        self.inpaint_input_image = args.pop()
        self.inpaint_additional_prompt = args.pop()
        self.inpaint_mask_image_upload = args.pop()

        self.disable_preview = args.pop()
        self.disable_intermediate_results = args.pop()
        self.disable_seed_increment = args.pop()
        self.black_out_nsfw = args.pop()
        self.adm_scaler_positive = args.pop()
        self.adm_scaler_negative = args.pop()
        self.adm_scaler_end = args.pop()
        self.adaptive_cfg = args.pop()
        self.clip_skip = args.pop()
        self.sampler_name = args.pop()
        self.scheduler_name = args.pop()
        self.vae_name = args.pop()
        self.overwrite_step = args.pop()
        self.overwrite_switch = args.pop()
        self.overwrite_width = args.pop()
        self.overwrite_height = args.pop()
        self.overwrite_vary_strength = args.pop()
        self.overwrite_upscale_strength = args.pop()
        self.mixing_image_prompt_and_vary_upscale = args.pop()
        self.mixing_image_prompt_and_inpaint = args.pop()
        self.debugging_cn_preprocessor = args.pop()
        self.skipping_cn_preprocessor = args.pop()
        self.canny_low_threshold = args.pop()
        self.canny_high_threshold = args.pop()
        self.refiner_swap_method = args.pop()
        self.controlnet_softness = args.pop()
        self.freeu_enabled = args.pop()
        self.freeu_b1 = args.pop()
        self.freeu_b2 = args.pop()
        self.freeu_s1 = args.pop()
        self.freeu_s2 = args.pop()
        self.debugging_inpaint_preprocessor = args.pop()
        self.inpaint_disable_initial_latent = args.pop()
        self.inpaint_engine = args.pop()
        self.inpaint_strength = args.pop()
        self.inpaint_respective_field = args.pop()
        self.inpaint_advanced_masking_checkbox = args.pop()
        self.invert_mask_checkbox = args.pop()
        self.inpaint_erode_or_dilate = args.pop()
        self.save_final_enhanced_image_only = args.pop() if not args_manager.args.disable_image_log else False
        self.save_metadata_to_images = args.pop() if not args_manager.args.disable_metadata else False
        self.metadata_scheme = MetadataScheme(
            args.pop()) if not args_manager.args.disable_metadata else MetadataScheme.FOOOCUS

        self.cn_tasks = {x: [] for x in ip_list}
        for _ in range(modules.config.default_controlnet_image_count):
            cn_img = args.pop()
            cn_stop = args.pop()
            cn_weight = args.pop()
            cn_type = args.pop()
            if cn_img is not None:
                self.cn_tasks[cn_type].append([cn_img, cn_stop, cn_weight])

        self.debugging_dino = args.pop()
        self.dino_erode_or_dilate = args.pop()
        self.debugging_enhance_masks_checkbox = args.pop()

        self.enhance_input_image = args.pop()
        self.enhance_checkbox = args.pop()
        self.enhance_uov_method = args.pop()
        self.enhance_uov_processing_order = args.pop()
        self.enhance_uov_prompt_type = args.pop()
        self.enhance_ctrls = []
        for _ in range(modules.config.default_enhance_tabs):
            enhance_enabled = args.pop()
            enhance_mask_dino_prompt_text = args.pop()
            enhance_prompt = args.pop()
            enhance_negative_prompt = args.pop()
            enhance_mask_model = args.pop()
            enhance_mask_cloth_category = args.pop()
            enhance_mask_sam_model = args.pop()
            enhance_mask_text_threshold = args.pop()
            enhance_mask_box_threshold = args.pop()
            enhance_mask_sam_max_detections = args.pop()
            enhance_inpaint_disable_initial_latent = args.pop()
            enhance_inpaint_engine = args.pop()
            enhance_inpaint_strength = args.pop()
            enhance_inpaint_respective_field = args.pop()
            enhance_inpaint_erode_or_dilate = args.pop()
            enhance_mask_invert = args.pop()
            if enhance_enabled:
                self.enhance_ctrls.append([
                    enhance_mask_dino_prompt_text,
                    enhance_prompt,
                    enhance_negative_prompt,
                    enhance_mask_model,
                    enhance_mask_cloth_category,
                    enhance_mask_sam_model,
                    enhance_mask_text_threshold,
                    enhance_mask_box_threshold,
                    enhance_mask_sam_max_detections,
                    enhance_inpaint_disable_initial_latent,
                    enhance_inpaint_engine,
                    enhance_inpaint_strength,
                    enhance_inpaint_respective_field,
                    enhance_inpaint_erode_or_dilate,
                    enhance_mask_invert
                ])
        self.should_enhance = self.enhance_checkbox and (self.enhance_uov_method != disabled.casefold() or len(self.enhance_ctrls) > 0)
        self.images_to_enhance_count = 0
        self.enhance_stats = {}

        # Sunside extras appended at end of ctrls -> remain at front after reverse; pop from end last
        self.character_enabled = False
        self.character_name = None
        self.face_pass_enabled = False
        self.face_ref_image = None
        self.character_anchor_override = None
        self.export_prefix = None
        self._character_face_ref = None
        if len(args) >= 5:
            self.character_enabled = bool(args.pop())
            self.character_name = args.pop()
            self.face_pass_enabled = bool(args.pop())
            self.face_ref_image = args.pop()
            self.character_anchor_override = args.pop()
        elif len(args) >= 4:
            self.character_enabled = bool(args.pop())
            self.character_name = args.pop()
            self.face_pass_enabled = bool(args.pop())
            self.face_ref_image = args.pop()
        elif len(args) >= 3:
            self.character_enabled = bool(args.pop())
            self.character_name = args.pop()
            self.face_pass_enabled = bool(args.pop())

        try:
            from modules.product_mode import is_product_mode, build_export_prefix
            if is_product_mode():
                self.black_out_nsfw = False
        except Exception:
            def build_export_prefix(*_a, **_k):
                return 'sunside'

        self.export_prefix = build_export_prefix(
            self.character_name if self.character_enabled else None,
            self.style_selections,
        )
        if self.character_enabled and self.character_name:
            try:
                from modules.characters import get_by_name, apply_character_to_prompt, merge_character_negative
                character = get_by_name(self.character_name)
                if character is not None:
                    self.prompt = apply_character_to_prompt(
                        self.prompt, character, anchor_override=self.character_anchor_override
                    )
                    self.negative_prompt = merge_character_negative(self.negative_prompt, character)
                    self.export_prefix = build_export_prefix(character.name, self.style_selections)
                    self._character_face_ref = character.face_ref_path
            except Exception as e:
                print(f'[Sunside Character] {e}')

        # Prefer UI-uploaded face ref over folder file
        if self.face_ref_image is not None:
            self._face_lock_ref = self.face_ref_image
        else:
            self._face_lock_ref = self._character_face_ref

        # Face lock DISABLED in product mode: insightface/inswapper still OOM-kills
        # Colab (SIGKILL) even on CPU — try/except cannot catch that.
        self._apply_face_lock = False
        try:
            from modules.product_mode import is_product_mode
            if is_product_mode() and self.face_pass_enabled:
                print('[Sunside] Face lock ignored (disabled — crashes Colab). Use Character anchor + prompt.')
        except Exception:
            pass

        # Never use IP-Adapter FaceSwap in product mode (OOM).
        try:
            from modules.product_mode import is_product_mode
            if is_product_mode():
                if cn_ip_face in self.cn_tasks and self.cn_tasks[cn_ip_face]:
                    print('[Sunside] IP-Adapter FaceSwap stripped (disabled on Colab)')
                    self.cn_tasks[cn_ip_face] = []
        except Exception:
            pass

        # Gallery Vary: UOV vary from selected image (whole-frame, not face paste)
        self.vary_enabled = False
        self.vary_image = None
        self.vary_mode = None
        if len(args) >= 3:
            self.vary_enabled = bool(args.pop())
            self.vary_image = args.pop()
            self.vary_mode = args.pop()
        elif len(args) >= 2:
            self.vary_enabled = bool(args.pop())
            self.vary_image = args.pop()
        if self.vary_enabled and self.vary_image is not None:
            self._configure_gallery_vary()

    def _configure_gallery_vary(self):
        """Run Fooocus Vary (Subtle/Strong) on a gallery image — coherent whole-frame variants."""
        from modules.flags import subtle_variation, strong_variation
        mode = self.vary_mode or subtle_variation
        mode_l = str(mode).casefold()
        if 'strong' in mode_l:
            mode = strong_variation
        else:
            mode = subtle_variation
        self.input_image_checkbox = True
        self.current_tab = 'uov'
        self.uov_method = mode
        self.uov_input_image = self.vary_image
        self.enhance_checkbox = False
        self.enhance_ctrls = []
        self.should_enhance = False
        n = max(1, min(int(self.image_number or 1), 32))
        self.image_number = n
        print(f'[Sunside Vary] {mode} × {n} from gallery (Image Number)')


async_tasks = []


class EarlyReturnException(BaseException):
    pass


def worker():
    global async_tasks

    import os
    import traceback
    import math
    import numpy as np
    import torch
    import time
    import shared
    import random
    import copy
    import cv2
    import modules.default_pipeline as pipeline
    import modules.core as core
    import modules.flags as flags
    import modules.patch
    import ldm_patched.modules.model_management
    import extras.preprocessors as preprocessors
    import modules.inpaint_worker as inpaint_worker
    import modules.constants as constants
    import extras.ip_adapter as ip_adapter
    import extras.face_crop
    import fooocus_version
    import args_manager

    from extras.censor import default_censor
    from modules.sdxl_styles import apply_style, get_random_style, fooocus_expansion, apply_arrays, random_style_name
    from modules.private_logger import log
    from extras.expansion import safe_str
    from modules.util import (remove_empty_str, HWC3, resize_image, get_image_shape_ceil, set_image_shape_ceil,
                              get_shape_ceil, resample_image, erode_or_dilate, parse_lora_references_from_prompt,
                              apply_wildcards)
    from modules.upscaler import perform_upscale
    from modules.flags import Performance
    from modules.meta_parser import get_metadata_parser

    pid = os.getpid()
    print(f'Started worker with PID {pid}')

    try:
        async_gradio_app = shared.gradio_root
        flag = f'''App started successful. Use the app with {str(async_gradio_app.local_url)} or {str(async_gradio_app.server_name)}:{str(async_gradio_app.server_port)}'''
        if async_gradio_app.share:
            flag += f''' or {async_gradio_app.share_url}'''
        print(flag)
    except Exception as e:
        print(e)

    def progressbar(async_task, number, text):
        print(f'[Fooocus] {text}')
        async_task.yields.append(['preview', (number, text, None)])

    def should_censor(black_out_nsfw):
        if args_manager.args.disable_censor:
            return False
        return modules.config.default_black_out_nsfw or black_out_nsfw

    def yield_result(async_task, imgs, progressbar_index, black_out_nsfw, censor=True, do_not_show_finished_images=False):
        if not isinstance(imgs, list):
            imgs = [imgs]

        if args_manager.args.disable_censor:
            censor = False

        if censor and should_censor(black_out_nsfw):
            progressbar(async_task, progressbar_index, 'Checking for NSFW content ...')
            imgs = default_censor(imgs)

        async_task.results = async_task.results + imgs

        if do_not_show_finished_images:
            return

        async_task.yields.append(['results', async_task.results])
        return

    def build_image_wall(async_task):
        results = []

        if len(async_task.results) < 2:
            return

        for img in async_task.results:
            if isinstance(img, str) and os.path.exists(img):
                img = cv2.imread(img)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if not isinstance(img, np.ndarray):
                return
            if img.ndim != 3:
                return
            results.append(img)

        H, W, C = results[0].shape

        for img in results:
            Hn, Wn, Cn = img.shape
            if H != Hn:
                return
            if W != Wn:
                return
            if C != Cn:
                return

        cols = float(len(results)) ** 0.5
        cols = int(math.ceil(cols))
        rows = float(len(results)) / float(cols)
        rows = int(math.ceil(rows))

        wall = np.zeros(shape=(H * rows, W * cols, C), dtype=np.uint8)

        for y in range(rows):
            for x in range(cols):
                if y * cols + x < len(results):
                    img = results[y * cols + x]
                    wall[y * H:y * H + H, x * W:x * W + W, :] = img

        # must use deep copy otherwise gradio is super laggy. Do not use list.append() .
        async_task.results = async_task.results + [wall]
        return

    def apply_pro_mode_ranking(async_task):
        if args_manager.args.disable_pro_mode or not async_task.pro_mode_enabled:
            return
        if len(async_task.results) < async_task.pro_mode_min_images:
            return

        try:
            from modules.pro_ranking import rank_results

            ranked_items, unscored_items, scored_meta = rank_results(async_task.results)
            if len(scored_meta) == 0:
                print('[Pro Mode] No rankable images found. Skipped.')
                return

            keep_count = int(async_task.pro_mode_keep_count)
            if keep_count > 0:
                ranked_items = ranked_items[:keep_count]

            async_task.results = ranked_items + unscored_items

            top = scored_meta[:min(3, len(scored_meta))]
            for i, x in enumerate(top):
                print(
                    f'[Pro Mode] Rank {i + 1}: score={x.score:.4f}, sharp={x.sharpness:.4f}, '
                    f'contrast={x.contrast:.4f}, exposure={x.exposure:.4f}, entropy={x.entropy:.4f}'
                )
            print(f'[Pro Mode] Ranked {len(scored_meta)} images, kept {len(ranked_items)} scored item(s).')
        except Exception as e:
            print(f'[Pro Mode] Ranking failed: {e}')
        return

    def configure_pro_mode_detail_pass(async_task):
        if args_manager.args.disable_pro_mode or not async_task.pro_mode_enabled:
            return
        if not async_task.pro_mode_detail_pass_enabled:
            return
        if len(async_task.enhance_ctrls) > 0 and async_task.enhance_checkbox:
            # Respect explicit user-defined enhance pipeline.
            return

        prompts = [safe_str(x).strip() for x in async_task.pro_mode_detail_prompts]
        prompts = [x for x in prompts if x != '']
        if len(prompts) == 0:
            return

        async_task.enhance_checkbox = True
        async_task.save_final_enhanced_image_only = True
        async_task.enhance_ctrls = []

        for detection_prompt in prompts:
            async_task.enhance_ctrls.append([
                detection_prompt,                              # enhance_mask_dino_prompt_text
                '',                                            # enhance_prompt (fallback to global prompt)
                '',                                            # enhance_negative_prompt (fallback to global negative)
                'sam',                                         # enhance_mask_model
                modules.config.default_inpaint_mask_cloth_category,
                modules.config.default_inpaint_mask_sam_model,
                0.25,                                          # enhance_mask_text_threshold
                0.30,                                          # enhance_mask_box_threshold
                modules.config.default_sam_max_detections,     # enhance_mask_sam_max_detections
                False,                                         # enhance_inpaint_disable_initial_latent
                async_task.pro_mode_detail_inpaint_engine,     # enhance_inpaint_engine
                async_task.pro_mode_detail_strength,           # enhance_inpaint_strength
                async_task.pro_mode_detail_respective_field,   # enhance_inpaint_respective_field
                async_task.pro_mode_detail_erode_or_dilate,    # enhance_inpaint_erode_or_dilate
                False                                          # enhance_mask_invert
            ])

        print(
            f'[Pro Mode] Enabled auto detail pass with prompts={prompts}, '
            f'engine={async_task.pro_mode_detail_inpaint_engine}, '
            f'strength={async_task.pro_mode_detail_strength}, '
            f'respective={async_task.pro_mode_detail_respective_field}'
        )
        return

    def prepare_pro_mode_structure_control(async_task, controlnet_canny_path, controlnet_cpds_path):
        if args_manager.args.disable_pro_mode or not async_task.pro_mode_enabled or not async_task.pro_mode_structure_control_enabled:
            return controlnet_canny_path, controlnet_cpds_path

        if async_task.pro_mode_structure_use_canny and controlnet_canny_path is None:
            controlnet_canny_path = modules.config.downloading_controlnet_canny()
        if async_task.pro_mode_structure_use_cpds and controlnet_cpds_path is None:
            controlnet_cpds_path = modules.config.downloading_controlnet_cpds()

        print(
            f'[Pro Mode] Structure control enabled: '
            f'canny={async_task.pro_mode_structure_use_canny} '
            f'(stop={async_task.pro_mode_structure_canny_stop}, weight={async_task.pro_mode_structure_canny_weight}), '
            f'cpds={async_task.pro_mode_structure_use_cpds} '
            f'(stop={async_task.pro_mode_structure_cpds_stop}, weight={async_task.pro_mode_structure_cpds_weight})'
        )
        return controlnet_canny_path, controlnet_cpds_path

    def process_task(all_steps, async_task, callback, controlnet_canny_path, controlnet_cpds_path, current_task_id,
                     denoising_strength, final_scheduler_name, goals, initial_latent, steps, switch, positive_cond,
                     negative_cond, task, loras, tiled, use_expansion, width, height, base_progress, preparation_steps,
                     total_count, show_intermediate_results, persist_image=True):
        if async_task.last_stop is not False:
            ldm_patched.modules.model_management.interrupt_current_processing()
        if 'cn' in goals:
            for cn_flag, cn_path in [
                (flags.cn_canny, controlnet_canny_path),
                (flags.cn_cpds, controlnet_cpds_path)
            ]:
                for cn_img, cn_stop, cn_weight in async_task.cn_tasks[cn_flag]:
                    positive_cond, negative_cond = core.apply_controlnet(
                        positive_cond, negative_cond,
                        pipeline.loaded_ControlNets[cn_path], cn_img, cn_weight, 0, cn_stop)
        imgs = pipeline.process_diffusion(
            positive_cond=positive_cond,
            negative_cond=negative_cond,
            steps=steps,
            switch=switch,
            width=width,
            height=height,
            image_seed=task['task_seed'],
            callback=callback,
            sampler_name=async_task.sampler_name,
            scheduler_name=final_scheduler_name,
            latent=initial_latent,
            denoise=denoising_strength,
            tiled=tiled,
            cfg_scale=async_task.cfg_scale,
            refiner_swap_method=async_task.refiner_swap_method,
            disable_preview=async_task.disable_preview
        )
        del positive_cond, negative_cond  # Save memory
        if inpaint_worker.current_task is not None:
            imgs = [inpaint_worker.current_task.post_process(x) for x in imgs]
        current_progress = int(base_progress + (100 - preparation_steps) / float(all_steps) * steps)
        if should_censor(async_task.black_out_nsfw):
            progressbar(async_task, current_progress, 'Checking for NSFW content ...')
            imgs = default_censor(imgs)
        progressbar(async_task, current_progress, f'Saving image {current_task_id + 1}/{total_count} to system ...')
        img_paths = save_and_log(async_task, height, imgs, task, use_expansion, width, loras, persist_image)
        yield_result(async_task, img_paths, current_progress, async_task.black_out_nsfw, False,
                     do_not_show_finished_images=not show_intermediate_results or async_task.disable_intermediate_results)

        return imgs, img_paths, current_progress

    def apply_patch_settings(async_task):
        patch_settings[pid] = PatchSettings(
            async_task.sharpness,
            async_task.adm_scaler_end,
            async_task.adm_scaler_positive,
            async_task.adm_scaler_negative,
            async_task.controlnet_softness,
            async_task.adaptive_cfg
        )

    def save_and_log(async_task, height, imgs, task, use_expansion, width, loras, persist_image=True) -> list:
        img_paths = []
        for x in imgs:
            d = [('Prompt', 'prompt', task['log_positive_prompt']),
                 ('Negative Prompt', 'negative_prompt', task['log_negative_prompt']),
                 ('Fooocus V2 Expansion', 'prompt_expansion', task['expansion']),
                 ('Styles', 'styles',
                  str(task['styles'] if not use_expansion else [fooocus_expansion] + task['styles'])),
                 ('Performance', 'performance', async_task.performance_selection.value),
                 ('Steps', 'steps', async_task.steps),
                 ('Resolution', 'resolution', str((width, height))),
                 ('Guidance Scale', 'guidance_scale', async_task.cfg_scale),
                 ('Sharpness', 'sharpness', async_task.sharpness),
                 ('ADM Guidance', 'adm_guidance', str((
                     modules.patch.patch_settings[pid].positive_adm_scale,
                     modules.patch.patch_settings[pid].negative_adm_scale,
                     modules.patch.patch_settings[pid].adm_scaler_end))),
                 ('Base Model', 'base_model', async_task.base_model_name),
                 ('Refiner Model', 'refiner_model', async_task.refiner_model_name),
                 ('Refiner Switch', 'refiner_switch', async_task.refiner_switch)]

            if async_task.refiner_model_name != 'None':
                if async_task.overwrite_switch > 0:
                    d.append(('Overwrite Switch', 'overwrite_switch', async_task.overwrite_switch))
                if async_task.refiner_swap_method != flags.refiner_swap_method:
                    d.append(('Refiner Swap Method', 'refiner_swap_method', async_task.refiner_swap_method))
            if modules.patch.patch_settings[pid].adaptive_cfg != modules.config.default_cfg_tsnr:
                d.append(
                    ('CFG Mimicking from TSNR', 'adaptive_cfg', modules.patch.patch_settings[pid].adaptive_cfg))

            if async_task.clip_skip > 1:
                d.append(('CLIP Skip', 'clip_skip', async_task.clip_skip))
            d.append(('Sampler', 'sampler', async_task.sampler_name))
            d.append(('Scheduler', 'scheduler', async_task.scheduler_name))
            d.append(('VAE', 'vae', async_task.vae_name))
            d.append(('Seed', 'seed', str(task['task_seed'])))

            if async_task.freeu_enabled:
                d.append(('FreeU', 'freeu',
                          str((async_task.freeu_b1, async_task.freeu_b2, async_task.freeu_s1, async_task.freeu_s2))))

            for li, (n, w) in enumerate(loras):
                if n != 'None':
                    d.append((f'LoRA {li + 1}', f'lora_combined_{li + 1}', f'{n} : {w}'))

            metadata_parser = None
            if async_task.save_metadata_to_images:
                metadata_parser = modules.meta_parser.get_metadata_parser(async_task.metadata_scheme)
                metadata_parser.set_data(task['log_positive_prompt'], task['positive'],
                                         task['log_negative_prompt'], task['negative'],
                                         async_task.steps, async_task.base_model_name, async_task.refiner_model_name,
                                         loras, async_task.vae_name)
            d.append(('Metadata Scheme', 'metadata_scheme',
                      async_task.metadata_scheme.value if async_task.save_metadata_to_images else async_task.save_metadata_to_images))
            d.append(('Version', 'version', 'Fooocus v' + fooocus_version.version))

            img_to_save = x
            if getattr(async_task, '_apply_face_lock', False) and getattr(async_task, '_face_lock_ref', None) is not None:
                try:
                    from modules.face_pass import apply_face_lock
                    free_first = not getattr(async_task, '_face_lock_vram_freed', False)
                    img_to_save = apply_face_lock(x, async_task._face_lock_ref, free_vram_first=free_first)
                    async_task._face_lock_vram_freed = True
                except Exception as e:
                    print(f'[Sunside FaceLock] ignored error, saving original: {e}')
                    img_to_save = x

            img_paths.append(log(
                img_to_save, d, metadata_parser, async_task.output_format, task, persist_image,
                filename_prefix=getattr(async_task, 'export_prefix', None)
            ))

        return img_paths

    def apply_control_nets(async_task, height, ip_adapter_face_path, ip_adapter_path, width, current_progress):
        for task in async_task.cn_tasks[flags.cn_canny]:
            cn_img, cn_stop, cn_weight = task
            cn_img = resize_image(HWC3(cn_img), width=width, height=height)

            if not async_task.skipping_cn_preprocessor:
                cn_img = preprocessors.canny_pyramid(cn_img, async_task.canny_low_threshold,
                                                     async_task.canny_high_threshold)

            cn_img = HWC3(cn_img)
            task[0] = core.numpy_to_pytorch(cn_img)
            if async_task.debugging_cn_preprocessor:
                yield_result(async_task, cn_img, current_progress, async_task.black_out_nsfw, do_not_show_finished_images=True)
        for task in async_task.cn_tasks[flags.cn_cpds]:
            cn_img, cn_stop, cn_weight = task
            cn_img = resize_image(HWC3(cn_img), width=width, height=height)

            if not async_task.skipping_cn_preprocessor:
                cn_img = preprocessors.cpds(cn_img)

            cn_img = HWC3(cn_img)
            task[0] = core.numpy_to_pytorch(cn_img)
            if async_task.debugging_cn_preprocessor:
                yield_result(async_task, cn_img, current_progress, async_task.black_out_nsfw, do_not_show_finished_images=True)
        for task in async_task.cn_tasks[flags.cn_ip]:
            cn_img, cn_stop, cn_weight = task
            cn_img = HWC3(cn_img)

            # https://github.com/tencent-ailab/IP-Adapter/blob/d580c50a291566bbf9fc7ac0f760506607297e6d/README.md?plain=1#L75
            cn_img = resize_image(cn_img, width=224, height=224, resize_mode=0)

            task[0] = ip_adapter.preprocess(cn_img, ip_adapter_path=ip_adapter_path)
            if async_task.debugging_cn_preprocessor:
                yield_result(async_task, cn_img, current_progress, async_task.black_out_nsfw, do_not_show_finished_images=True)
        for task in async_task.cn_tasks[flags.cn_ip_face]:
            cn_img, cn_stop, cn_weight = task
            cn_img = HWC3(cn_img)

            if not async_task.skipping_cn_preprocessor:
                cn_img = extras.face_crop.crop_image(cn_img)

            # https://github.com/tencent-ailab/IP-Adapter/blob/d580c50a291566bbf9fc7ac0f760506607297e6d/README.md?plain=1#L75
            cn_img = resize_image(cn_img, width=224, height=224, resize_mode=0)

            task[0] = ip_adapter.preprocess(cn_img, ip_adapter_path=ip_adapter_face_path)
            if async_task.debugging_cn_preprocessor:
                yield_result(async_task, cn_img, current_progress, async_task.black_out_nsfw, do_not_show_finished_images=True)
        all_ip_tasks = async_task.cn_tasks[flags.cn_ip] + async_task.cn_tasks[flags.cn_ip_face]
        if len(all_ip_tasks) > 0:
            pipeline.final_unet = ip_adapter.patch_model(pipeline.final_unet, all_ip_tasks)

    def apply_vary(async_task, uov_method, denoising_strength, uov_input_image, switch, current_progress, advance_progress=False):
        if 'subtle' in uov_method:
            denoising_strength = 0.5
        if 'strong' in uov_method:
            denoising_strength = 0.85
        if async_task.overwrite_vary_strength > 0:
            denoising_strength = async_task.overwrite_vary_strength
        shape_ceil = get_image_shape_ceil(uov_input_image)
        if shape_ceil < 1024:
            print(f'[Vary] Image is resized because it is too small.')
            shape_ceil = 1024
        elif shape_ceil > 2048:
            print(f'[Vary] Image is resized because it is too big.')
            shape_ceil = 2048
        uov_input_image = set_image_shape_ceil(uov_input_image, shape_ceil)
        initial_pixels = core.numpy_to_pytorch(uov_input_image)
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'VAE encoding ...')
        candidate_vae, _ = pipeline.get_candidate_vae(
            steps=async_task.steps,
            switch=switch,
            denoise=denoising_strength,
            refiner_swap_method=async_task.refiner_swap_method
        )
        initial_latent = core.encode_vae(vae=candidate_vae, pixels=initial_pixels)
        B, C, H, W = initial_latent['samples'].shape
        width = W * 8
        height = H * 8
        print(f'Final resolution is {str((width, height))}.')
        return uov_input_image, denoising_strength, initial_latent, width, height, current_progress

    def apply_inpaint(async_task, initial_latent, inpaint_head_model_path, inpaint_image,
                      inpaint_mask, inpaint_parameterized, denoising_strength, inpaint_respective_field, switch,
                      inpaint_disable_initial_latent, current_progress, skip_apply_outpaint=False,
                      advance_progress=False):
        if not skip_apply_outpaint:
            inpaint_image, inpaint_mask = apply_outpaint(async_task, inpaint_image, inpaint_mask)

        inpaint_worker.current_task = inpaint_worker.InpaintWorker(
            image=inpaint_image,
            mask=inpaint_mask,
            use_fill=denoising_strength > 0.99,
            k=inpaint_respective_field
        )
        if async_task.debugging_inpaint_preprocessor:
            yield_result(async_task, inpaint_worker.current_task.visualize_mask_processing(), 100,
                         async_task.black_out_nsfw, do_not_show_finished_images=True)
            raise EarlyReturnException

        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'VAE Inpaint encoding ...')
        inpaint_pixel_fill = core.numpy_to_pytorch(inpaint_worker.current_task.interested_fill)
        inpaint_pixel_image = core.numpy_to_pytorch(inpaint_worker.current_task.interested_image)
        inpaint_pixel_mask = core.numpy_to_pytorch(inpaint_worker.current_task.interested_mask)
        candidate_vae, candidate_vae_swap = pipeline.get_candidate_vae(
            steps=async_task.steps,
            switch=switch,
            denoise=denoising_strength,
            refiner_swap_method=async_task.refiner_swap_method
        )
        latent_inpaint, latent_mask = core.encode_vae_inpaint(
            mask=inpaint_pixel_mask,
            vae=candidate_vae,
            pixels=inpaint_pixel_image)
        latent_swap = None
        if candidate_vae_swap is not None:
            if advance_progress:
                current_progress += 1
            progressbar(async_task, current_progress, 'VAE SD15 encoding ...')
            latent_swap = core.encode_vae(
                vae=candidate_vae_swap,
                pixels=inpaint_pixel_fill)['samples']
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'VAE encoding ...')
        latent_fill = core.encode_vae(
            vae=candidate_vae,
            pixels=inpaint_pixel_fill)['samples']
        inpaint_worker.current_task.load_latent(
            latent_fill=latent_fill, latent_mask=latent_mask, latent_swap=latent_swap)
        if inpaint_parameterized:
            pipeline.final_unet = inpaint_worker.current_task.patch(
                inpaint_head_model_path=inpaint_head_model_path,
                inpaint_latent=latent_inpaint,
                inpaint_latent_mask=latent_mask,
                model=pipeline.final_unet
            )
        if not inpaint_disable_initial_latent:
            initial_latent = {'samples': latent_fill}
        B, C, H, W = latent_fill.shape
        height, width = H * 8, W * 8
        final_height, final_width = inpaint_worker.current_task.image.shape[:2]
        print(f'Final resolution is {str((final_width, final_height))}, latent is {str((width, height))}.')

        return denoising_strength, initial_latent, width, height, current_progress

    def apply_outpaint(async_task, inpaint_image, inpaint_mask):
        if len(async_task.outpaint_selections) > 0:
            H, W, C = inpaint_image.shape
            if 'top' in async_task.outpaint_selections:
                inpaint_image = np.pad(inpaint_image, [[int(H * 0.3), 0], [0, 0], [0, 0]], mode='edge')
                inpaint_mask = np.pad(inpaint_mask, [[int(H * 0.3), 0], [0, 0]], mode='constant',
                                      constant_values=255)
            if 'bottom' in async_task.outpaint_selections:
                inpaint_image = np.pad(inpaint_image, [[0, int(H * 0.3)], [0, 0], [0, 0]], mode='edge')
                inpaint_mask = np.pad(inpaint_mask, [[0, int(H * 0.3)], [0, 0]], mode='constant',
                                      constant_values=255)

            H, W, C = inpaint_image.shape
            if 'left' in async_task.outpaint_selections:
                inpaint_image = np.pad(inpaint_image, [[0, 0], [int(W * 0.3), 0], [0, 0]], mode='edge')
                inpaint_mask = np.pad(inpaint_mask, [[0, 0], [int(W * 0.3), 0]], mode='constant',
                                      constant_values=255)
            if 'right' in async_task.outpaint_selections:
                inpaint_image = np.pad(inpaint_image, [[0, 0], [0, int(W * 0.3)], [0, 0]], mode='edge')
                inpaint_mask = np.pad(inpaint_mask, [[0, 0], [0, int(W * 0.3)]], mode='constant',
                                      constant_values=255)

            inpaint_image = np.ascontiguousarray(inpaint_image.copy())
            inpaint_mask = np.ascontiguousarray(inpaint_mask.copy())
            async_task.inpaint_strength = 1.0
            async_task.inpaint_respective_field = 1.0
        return inpaint_image, inpaint_mask

    def apply_upscale(async_task, uov_input_image, uov_method, switch, current_progress, advance_progress=False):
        H, W, C = uov_input_image.shape
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, f'Upscaling image from {str((W, H))} ...')
        uov_input_image = perform_upscale(uov_input_image)
        print(f'Image upscaled.')
        if '1.5x' in uov_method:
            f = 1.5
        elif '2x' in uov_method:
            f = 2.0
        else:
            f = 1.0
        shape_ceil = get_shape_ceil(H * f, W * f)
        if shape_ceil < 1024:
            print(f'[Upscale] Image is resized because it is too small.')
            uov_input_image = set_image_shape_ceil(uov_input_image, 1024)
            shape_ceil = 1024
        else:
            uov_input_image = resample_image(uov_input_image, width=W * f, height=H * f)
        image_is_super_large = shape_ceil > 2800
        if 'fast' in uov_method:
            direct_return = True
        elif image_is_super_large:
            print('Image is too large. Directly returned the SR image. '
                  'Usually directly return SR image at 4K resolution '
                  'yields better results than SDXL diffusion.')
            direct_return = True
        else:
            direct_return = False
        if direct_return:
            return direct_return, uov_input_image, None, None, None, None, None, current_progress

        tiled = True
        denoising_strength = 0.382
        if async_task.overwrite_upscale_strength > 0:
            denoising_strength = async_task.overwrite_upscale_strength
        initial_pixels = core.numpy_to_pytorch(uov_input_image)
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'VAE encoding ...')
        candidate_vae, _ = pipeline.get_candidate_vae(
            steps=async_task.steps,
            switch=switch,
            denoise=denoising_strength,
            refiner_swap_method=async_task.refiner_swap_method
        )
        initial_latent = core.encode_vae(
            vae=candidate_vae,
            pixels=initial_pixels, tiled=True)
        B, C, H, W = initial_latent['samples'].shape
        width = W * 8
        height = H * 8
        print(f'Final resolution is {str((width, height))}.')
        return direct_return, uov_input_image, denoising_strength, initial_latent, tiled, width, height, current_progress

    def apply_overrides(async_task, steps, height, width):
        if async_task.overwrite_step > 0:
            steps = async_task.overwrite_step
        switch = int(round(async_task.steps * async_task.refiner_switch))
        if async_task.overwrite_switch > 0:
            switch = async_task.overwrite_switch
        if async_task.overwrite_width > 0:
            width = async_task.overwrite_width
        if async_task.overwrite_height > 0:
            height = async_task.overwrite_height
        return steps, switch, width, height

    def process_prompt(async_task, prompt, negative_prompt, base_model_additional_loras, image_number, disable_seed_increment, use_expansion, use_style,
                       use_synthetic_refiner, current_progress, advance_progress=False):
        prompts = remove_empty_str([safe_str(p) for p in prompt.splitlines()], default='')
        negative_prompts = remove_empty_str([safe_str(p) for p in negative_prompt.splitlines()], default='')
        prompt = prompts[0]
        negative_prompt = negative_prompts[0]
        if prompt == '':
            # disable expansion when empty since it is not meaningful and influences image prompt
            use_expansion = False
        extra_positive_prompts = prompts[1:] if len(prompts) > 1 else []
        extra_negative_prompts = negative_prompts[1:] if len(negative_prompts) > 1 else []
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'Loading models ...')
        lora_filenames = modules.util.remove_performance_lora(modules.config.lora_filenames,
                                                              async_task.performance_selection)
        loras, prompt = parse_lora_references_from_prompt(prompt, async_task.loras,
                                                          modules.config.default_max_lora_number,
                                                          lora_filenames=lora_filenames)
        loras += async_task.performance_loras
        pipeline.refresh_everything(refiner_model_name=async_task.refiner_model_name,
                                    base_model_name=async_task.base_model_name,
                                    loras=loras, base_model_additional_loras=base_model_additional_loras,
                                    use_synthetic_refiner=use_synthetic_refiner, vae_name=async_task.vae_name)
        pipeline.set_clip_skip(async_task.clip_skip)
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'Processing prompts ...')
        tasks = []
        for i in range(image_number):
            if disable_seed_increment:
                task_seed = async_task.seed % (constants.MAX_SEED + 1)
            else:
                task_seed = (async_task.seed + i) % (constants.MAX_SEED + 1)  # randint is inclusive, % is not

            task_rng = random.Random(task_seed)  # may bind to inpaint noise in the future
            task_prompt = apply_wildcards(prompt, task_rng, i, async_task.read_wildcards_in_order)
            task_prompt = apply_arrays(task_prompt, i)
            task_negative_prompt = apply_wildcards(negative_prompt, task_rng, i, async_task.read_wildcards_in_order)
            task_extra_positive_prompts = [apply_wildcards(pmt, task_rng, i, async_task.read_wildcards_in_order) for pmt
                                           in
                                           extra_positive_prompts]
            task_extra_negative_prompts = [apply_wildcards(pmt, task_rng, i, async_task.read_wildcards_in_order) for pmt
                                           in
                                           extra_negative_prompts]

            positive_basic_workloads = []
            negative_basic_workloads = []

            task_styles = async_task.style_selections.copy()
            if use_style:
                placeholder_replaced = False

                for j, s in enumerate(task_styles):
                    if s == random_style_name:
                        s = get_random_style(task_rng)
                        task_styles[j] = s
                    p, n, style_has_placeholder = apply_style(s, positive=task_prompt)
                    if style_has_placeholder:
                        placeholder_replaced = True
                    positive_basic_workloads = positive_basic_workloads + p
                    negative_basic_workloads = negative_basic_workloads + n

                if not placeholder_replaced:
                    positive_basic_workloads = [task_prompt] + positive_basic_workloads
            else:
                positive_basic_workloads.append(task_prompt)

            negative_basic_workloads.append(task_negative_prompt)  # Always use independent workload for negative.

            positive_basic_workloads = positive_basic_workloads + task_extra_positive_prompts
            negative_basic_workloads = negative_basic_workloads + task_extra_negative_prompts

            positive_basic_workloads = remove_empty_str(positive_basic_workloads, default=task_prompt)
            negative_basic_workloads = remove_empty_str(negative_basic_workloads, default=task_negative_prompt)

            tasks.append(dict(
                task_seed=task_seed,
                task_prompt=task_prompt,
                task_negative_prompt=task_negative_prompt,
                positive=positive_basic_workloads,
                negative=negative_basic_workloads,
                expansion='',
                c=None,
                uc=None,
                positive_top_k=len(positive_basic_workloads),
                negative_top_k=len(negative_basic_workloads),
                log_positive_prompt='\n'.join([task_prompt] + task_extra_positive_prompts),
                log_negative_prompt='\n'.join([task_negative_prompt] + task_extra_negative_prompts),
                styles=task_styles
            ))
        if use_expansion:
            if advance_progress:
                current_progress += 1
            for i, t in enumerate(tasks):

                progressbar(async_task, current_progress, f'Preparing Fooocus text #{i + 1} ...')
                expansion = pipeline.final_expansion(t['task_prompt'], t['task_seed'])
                print(f'[Prompt Expansion] {expansion}')
                t['expansion'] = expansion
                t['positive'] = copy.deepcopy(t['positive']) + [expansion]  # Deep copy.
        if advance_progress:
            current_progress += 1
        for i, t in enumerate(tasks):
            progressbar(async_task, current_progress, f'Encoding positive #{i + 1} ...')
            t['c'] = pipeline.clip_encode(texts=t['positive'], pool_top_k=t['positive_top_k'])
        if advance_progress:
            current_progress += 1
        for i, t in enumerate(tasks):
            if abs(float(async_task.cfg_scale) - 1.0) < 1e-4:
                t['uc'] = pipeline.clone_cond(t['c'])
            else:
                progressbar(async_task, current_progress, f'Encoding negative #{i + 1} ...')
                t['uc'] = pipeline.clip_encode(texts=t['negative'], pool_top_k=t['negative_top_k'])
        return tasks, use_expansion, loras, current_progress

    def apply_freeu(async_task):
        print(f'FreeU is enabled!')
        pipeline.final_unet = core.apply_freeu(
            pipeline.final_unet,
            async_task.freeu_b1,
            async_task.freeu_b2,
            async_task.freeu_s1,
            async_task.freeu_s2
        )

    def patch_discrete(unet, scheduler_name):
        return core.opModelSamplingDiscrete.patch(unet, scheduler_name, False)[0]

    def patch_edm(unet, scheduler_name):
        return core.opModelSamplingContinuousEDM.patch(unet, scheduler_name, 120.0, 0.002)[0]

    def patch_samplers(async_task):
        final_scheduler_name = async_task.scheduler_name

        if async_task.scheduler_name in ['lcm', 'tcd']:
            final_scheduler_name = 'sgm_uniform'
            if pipeline.final_unet is not None:
                pipeline.final_unet = patch_discrete(pipeline.final_unet, async_task.scheduler_name)
            if pipeline.final_refiner_unet is not None:
                pipeline.final_refiner_unet = patch_discrete(pipeline.final_refiner_unet, async_task.scheduler_name)

        elif async_task.scheduler_name == 'edm_playground_v2.5':
            final_scheduler_name = 'karras'
            if pipeline.final_unet is not None:
                pipeline.final_unet = patch_edm(pipeline.final_unet, async_task.scheduler_name)
            if pipeline.final_refiner_unet is not None:
                pipeline.final_refiner_unet = patch_edm(pipeline.final_refiner_unet, async_task.scheduler_name)

        return final_scheduler_name

    def set_hyper_sd_defaults(async_task, current_progress, advance_progress=False):
        print('Enter Hyper-SD mode.')
        if advance_progress:
            current_progress += 1
        progressbar(async_task, current_progress, 'Downloading Hyper-SD components ...')
        async_task.performance_loras += [(modules.config.downloading_sdxl_hyper_sd_lora(), 0.8)]
        if async_task.refiner_model_name != 'None':
            print(f'Refiner disabled in Hyper-SD mode.')
        async_task.refiner_model_name = 'None'
        async_task.sampler_name = 'dpmpp_sde_gpu'
        async_task.scheduler_name = 'karras'
        async_task.sharpness = 0.0
        async_task.cfg_scale = 1.0
        async_task.adaptive_cfg = 1.0
        async_task.refiner_switch = 1.0
        async_task.adm_scaler_positive = 1.0
        async_task.adm_scaler_negative = 1.0
        async_task.adm_scaler_end = 0.0
        return current_progress

    def set_lightning_defaults(async_task, current_progress, advance_progress=False):
        print('Enter Lightning mode.')
        if advance_progress:
            current_progress += 1
        progressbar(async_task, 1, 'Downloading Lightning components ...')
        async_task.performance_loras += [(modules.config.downloading_sdxl_lightning_lora(), 1.0)]
        if async_task.refiner_model_name != 'None':
            print(f'Refiner disabled in Lightning mode.')
        async_task.refiner_model_name = 'None'
        async_task.sampler_name = 'euler'
        async_task.scheduler_name = 'sgm_uniform'
        async_task.sharpness = 0.0
        async_task.cfg_scale = 1.0
        async_task.adaptive_cfg = 1.0
        async_task.refiner_switch = 1.0
        async_task.adm_scaler_positive = 1.0
        async_task.adm_scaler_negative = 1.0
        async_task.adm_scaler_end = 0.0
        return current_progress

    def set_lcm_defaults(async_task, current_progress, advance_progress=False):
        print('Enter LCM mode.')
        if advance_progress:
            current_progress += 1
        progressbar(async_task, 1, 'Downloading LCM components ...')
        async_task.performance_loras += [(modules.config.downloading_sdxl_lcm_lora(), 1.0)]
        if async_task.refiner_model_name != 'None':
            print(f'Refiner disabled in LCM mode.')
        async_task.refiner_model_name = 'None'
        async_task.sampler_name = 'lcm'
        async_task.scheduler_name = 'lcm'
        async_task.sharpness = 0.0
        async_task.cfg_scale = 1.0
        async_task.adaptive_cfg = 1.0
        async_task.refiner_switch = 1.0
        async_task.adm_scaler_positive = 1.0
        async_task.adm_scaler_negative = 1.0
        async_task.adm_scaler_end = 0.0
        return current_progress

    def apply_image_input(async_task, base_model_additional_loras, clip_vision_path, controlnet_canny_path,
                          controlnet_cpds_path, goals, inpaint_head_model_path, inpaint_image, inpaint_mask,
                          inpaint_parameterized,  ip_adapter_face_path, ip_adapter_path, ip_negative_path,
                          skip_prompt_processing, use_synthetic_refiner):
        if (async_task.current_tab == 'uov' or (
                async_task.current_tab == 'ip' and async_task.mixing_image_prompt_and_vary_upscale)) \
                and async_task.uov_method != flags.disabled.casefold() and async_task.uov_input_image is not None:
            async_task.uov_input_image, skip_prompt_processing, async_task.steps = prepare_upscale(
                async_task, goals, async_task.uov_input_image, async_task.uov_method, async_task.performance_selection,
                async_task.steps, 1, skip_prompt_processing=skip_prompt_processing)
        if (async_task.current_tab == 'inpaint' or (
                async_task.current_tab == 'ip' and async_task.mixing_image_prompt_and_inpaint)) \
                and isinstance(async_task.inpaint_input_image, dict):
            inpaint_image = async_task.inpaint_input_image['image']
            inpaint_mask = async_task.inpaint_input_image['mask'][:, :, 0]

            if async_task.inpaint_advanced_masking_checkbox:
                if isinstance(async_task.inpaint_mask_image_upload, dict):
                    if (isinstance(async_task.inpaint_mask_image_upload['image'], np.ndarray)
                            and isinstance(async_task.inpaint_mask_image_upload['mask'], np.ndarray)
                            and async_task.inpaint_mask_image_upload['image'].ndim == 3):
                        async_task.inpaint_mask_image_upload = np.maximum(
                            async_task.inpaint_mask_image_upload['image'],
                            async_task.inpaint_mask_image_upload['mask'])
                if isinstance(async_task.inpaint_mask_image_upload,
                              np.ndarray) and async_task.inpaint_mask_image_upload.ndim == 3:
                    H, W, C = inpaint_image.shape
                    async_task.inpaint_mask_image_upload = resample_image(async_task.inpaint_mask_image_upload,
                                                                          width=W, height=H)
                    async_task.inpaint_mask_image_upload = np.mean(async_task.inpaint_mask_image_upload, axis=2)
                    async_task.inpaint_mask_image_upload = (async_task.inpaint_mask_image_upload > 127).astype(
                        np.uint8) * 255
                    inpaint_mask = np.maximum(inpaint_mask, async_task.inpaint_mask_image_upload)

            if int(async_task.inpaint_erode_or_dilate) != 0:
                inpaint_mask = erode_or_dilate(inpaint_mask, async_task.inpaint_erode_or_dilate)

            if async_task.invert_mask_checkbox:
                inpaint_mask = 255 - inpaint_mask

            inpaint_image = HWC3(inpaint_image)
            if isinstance(inpaint_image, np.ndarray) and isinstance(inpaint_mask, np.ndarray) \
                    and (np.any(inpaint_mask > 127) or len(async_task.outpaint_selections) > 0):
                progressbar(async_task, 1, 'Downloading upscale models ...')
                modules.config.downloading_upscale_model()
                if inpaint_parameterized:
                    progressbar(async_task, 1, 'Downloading inpainter ...')
                    inpaint_head_model_path, inpaint_patch_model_path = modules.config.downloading_inpaint_models(
                        async_task.inpaint_engine)
                    base_model_additional_loras += [(inpaint_patch_model_path, 1.0)]
                    print(f'[Inpaint] Current inpaint model is {inpaint_patch_model_path}')
                    if async_task.refiner_model_name == 'None':
                        use_synthetic_refiner = True
                        async_task.refiner_switch = 0.8
                else:
                    inpaint_head_model_path, inpaint_patch_model_path = None, None
                    print(f'[Inpaint] Parameterized inpaint is disabled.')
                if async_task.inpaint_additional_prompt != '':
                    if async_task.prompt == '':
                        async_task.prompt = async_task.inpaint_additional_prompt
                    else:
                        async_task.prompt = async_task.inpaint_additional_prompt + '\n' + async_task.prompt
                goals.append('inpaint')
        if async_task.current_tab == 'ip' or \
                async_task.mixing_image_prompt_and_vary_upscale or \
                async_task.mixing_image_prompt_and_inpaint:
            goals.append('cn')
            progressbar(async_task, 1, 'Downloading control models ...')
            if len(async_task.cn_tasks[flags.cn_canny]) > 0:
                controlnet_canny_path = modules.config.downloading_controlnet_canny()
            if len(async_task.cn_tasks[flags.cn_cpds]) > 0:
                controlnet_cpds_path = modules.config.downloading_controlnet_cpds()
            if len(async_task.cn_tasks[flags.cn_ip]) > 0:
                clip_vision_path, ip_negative_path, ip_adapter_path = modules.config.downloading_ip_adapters('ip')
            if len(async_task.cn_tasks[flags.cn_ip_face]) > 0:
                clip_vision_path, ip_negative_path, ip_adapter_face_path = modules.config.downloading_ip_adapters(
                    'face')
        if async_task.current_tab == 'enhance' and async_task.enhance_input_image is not None:
            goals.append('enhance')
            skip_prompt_processing = True
            async_task.enhance_input_image = HWC3(async_task.enhance_input_image)
        return base_model_additional_loras, clip_vision_path, controlnet_canny_path, controlnet_cpds_path, inpaint_head_model_path, inpaint_image, inpaint_mask, ip_adapter_face_path, ip_adapter_path, ip_negative_path, skip_prompt_processing, use_synthetic_refiner

    def prepare_upscale(async_task, goals, uov_input_image, uov_method, performance, steps, current_progress,
                        advance_progress=False, skip_prompt_processing=False):
        uov_input_image = HWC3(uov_input_image)
        if 'vary' in uov_method:
            goals.append('vary')
        elif 'upscale' in uov_method:
            goals.append('upscale')
            if 'fast' in uov_method:
                skip_prompt_processing = True
                steps = 0
            else:
                steps = performance.steps_uov()

            if advance_progress:
                current_progress += 1
            progressbar(async_task, current_progress, 'Downloading upscale models ...')
            modules.config.downloading_upscale_model()
        return uov_input_image, skip_prompt_processing, steps

    def prepare_enhance_prompt(prompt: str, fallback_prompt: str):
        if safe_str(prompt) == '' or len(remove_empty_str([safe_str(p) for p in prompt.splitlines()], default='')) == 0:
            prompt = fallback_prompt

        return prompt

    def stop_processing(async_task, processing_start_time):
        async_task.processing = False
        processing_time = time.perf_counter() - processing_start_time
        print(f'Processing time (total): {processing_time:.2f} seconds')

    def process_enhance(all_steps, async_task, callback, controlnet_canny_path, controlnet_cpds_path,
                        ip_adapter_face_path, ip_adapter_path,
                        current_progress, current_task_id, denoising_strength, inpaint_disable_initial_latent,
                        inpaint_engine, inpaint_respective_field, inpaint_strength,
                        prompt, negative_prompt, final_scheduler_name, goals, height, img, mask,
                        preparation_steps, steps, switch, tiled, total_count, use_expansion, use_style,
                        use_synthetic_refiner, width, show_intermediate_results=True, persist_image=True):
        base_model_additional_loras = []
        inpaint_head_model_path = None
        inpaint_parameterized = inpaint_engine != 'None'  # inpaint_engine = None, improve detail
        initial_latent = None

        prompt = prepare_enhance_prompt(prompt, async_task.prompt)
        negative_prompt = prepare_enhance_prompt(negative_prompt, async_task.negative_prompt)

        if 'vary' in goals:
            img, denoising_strength, initial_latent, width, height, current_progress = apply_vary(
                async_task, async_task.enhance_uov_method, denoising_strength, img, switch, current_progress)
        if 'upscale' in goals:
            direct_return, img, denoising_strength, initial_latent, tiled, width, height, current_progress = apply_upscale(
                async_task, img, async_task.enhance_uov_method, switch, current_progress)
            if direct_return:
                d = [('Upscale (Fast)', 'upscale_fast', '2x')]
                if should_censor(async_task.black_out_nsfw):
                    progressbar(async_task, current_progress, 'Checking for NSFW content ...')
                    img = default_censor(img)
                progressbar(async_task, current_progress, f'Saving image {current_task_id + 1}/{total_count} to system ...')
                uov_image_path = log(img, d, output_format=async_task.output_format, persist_image=persist_image)
                yield_result(async_task, uov_image_path, current_progress, async_task.black_out_nsfw, False,
                             do_not_show_finished_images=not show_intermediate_results or async_task.disable_intermediate_results)
                return current_progress, img, prompt, negative_prompt

        if 'inpaint' in goals and inpaint_parameterized:
            progressbar(async_task, current_progress, 'Downloading inpainter ...')
            inpaint_head_model_path, inpaint_patch_model_path = modules.config.downloading_inpaint_models(
                inpaint_engine)
            if inpaint_patch_model_path not in base_model_additional_loras:
                base_model_additional_loras += [(inpaint_patch_model_path, 1.0)]
        progressbar(async_task, current_progress, 'Preparing enhance prompts ...')
        # positive and negative conditioning aren't available here anymore, process prompt again
        tasks_enhance, use_expansion, loras, current_progress = process_prompt(
            async_task, prompt, negative_prompt, base_model_additional_loras, 1, True,
            use_expansion, use_style, use_synthetic_refiner, current_progress)
        task_enhance = tasks_enhance[0]
        goals_enhance = list(goals)
        injected_canny = 0
        injected_cpds = 0

        if async_task.pro_mode_enabled and async_task.pro_mode_structure_control_enabled:
            structure_source = HWC3(img)
            if async_task.pro_mode_structure_use_canny and controlnet_canny_path is not None:
                async_task.cn_tasks[flags.cn_canny].append([
                    np.ascontiguousarray(structure_source.copy()),
                    float(async_task.pro_mode_structure_canny_stop),
                    float(async_task.pro_mode_structure_canny_weight)
                ])
                injected_canny = 1
            if async_task.pro_mode_structure_use_cpds and controlnet_cpds_path is not None:
                async_task.cn_tasks[flags.cn_cpds].append([
                    np.ascontiguousarray(structure_source.copy()),
                    float(async_task.pro_mode_structure_cpds_stop),
                    float(async_task.pro_mode_structure_cpds_weight)
                ])
                injected_cpds = 1

            if injected_canny + injected_cpds > 0:
                if 'cn' not in goals_enhance:
                    goals_enhance.append('cn')
                apply_control_nets(async_task, height, ip_adapter_face_path, ip_adapter_path, width, current_progress)

        if async_task.freeu_enabled:
            apply_freeu(async_task)
        patch_samplers(async_task)
        if 'inpaint' in goals:
            denoising_strength, initial_latent, width, height, current_progress = apply_inpaint(
                async_task, None, inpaint_head_model_path, img, mask,
                inpaint_parameterized, inpaint_strength,
                inpaint_respective_field, switch, inpaint_disable_initial_latent,
                current_progress, True)
        try:
            imgs, img_paths, current_progress = process_task(all_steps, async_task, callback, controlnet_canny_path,
                                                             controlnet_cpds_path, current_task_id, denoising_strength,
                                                             final_scheduler_name, goals_enhance, initial_latent, steps,
                                                             switch, task_enhance['c'], task_enhance['uc'], task_enhance,
                                                             loras, tiled, use_expansion, width, height, current_progress,
                                                             preparation_steps, total_count, show_intermediate_results,
                                                             persist_image)
        finally:
            if injected_canny > 0:
                del async_task.cn_tasks[flags.cn_canny][-injected_canny:]
            if injected_cpds > 0:
                del async_task.cn_tasks[flags.cn_cpds][-injected_cpds:]

        del task_enhance['c'], task_enhance['uc']  # Save memory
        return current_progress, imgs[0], prompt, negative_prompt

    def enhance_upscale(all_steps, async_task, base_progress, callback, controlnet_canny_path, controlnet_cpds_path,
                        ip_adapter_face_path, ip_adapter_path,
                        current_task_id, denoising_strength, done_steps_inpainting, done_steps_upscaling, enhance_steps,
                        prompt, negative_prompt, final_scheduler_name, height, img, preparation_steps, switch, tiled,
                        total_count, use_expansion, use_style, use_synthetic_refiner, width, persist_image=True):
        # reset inpaint worker to prevent tensor size issues and not mix upscale and inpainting
        inpaint_worker.current_task = None

        current_progress = int(base_progress + (100 - preparation_steps) / float(all_steps) * (done_steps_upscaling + done_steps_inpainting))
        goals_enhance = []
        img, skip_prompt_processing, steps = prepare_upscale(
            async_task, goals_enhance, img, async_task.enhance_uov_method, async_task.performance_selection,
            enhance_steps, current_progress)
        steps, _, _, _ = apply_overrides(async_task, steps, height, width)
        exception_result = ''
        if len(goals_enhance) > 0:
            try:
                current_progress, img, prompt, negative_prompt = process_enhance(
                    all_steps, async_task, callback, controlnet_canny_path, controlnet_cpds_path,
                    ip_adapter_face_path, ip_adapter_path, current_progress, current_task_id, denoising_strength, False,
                    'None', 0.0, 0.0, prompt, negative_prompt, final_scheduler_name,
                    goals_enhance, height, img, None, preparation_steps, steps, switch, tiled, total_count,
                    use_expansion, use_style, use_synthetic_refiner, width, persist_image=persist_image)

            except ldm_patched.modules.model_management.InterruptProcessingException:
                if async_task.last_stop == 'skip':
                    print('User skipped')
                    async_task.last_stop = False
                    # also skip all enhance steps for this image, but add the steps to the progress bar
                    if async_task.enhance_uov_processing_order == flags.enhancement_uov_before:
                        done_steps_inpainting += len(async_task.enhance_ctrls) * enhance_steps
                    exception_result = 'continue'
                else:
                    print('User stopped')
                    exception_result = 'break'
            finally:
                done_steps_upscaling += steps
        return current_task_id, done_steps_inpainting, done_steps_upscaling, img, exception_result

    @torch.no_grad()
    @torch.inference_mode()
    def handler(async_task: AsyncTask):
        preparation_start_time = time.perf_counter()
        async_task.processing = True

        async_task.outpaint_selections = [o.lower() for o in async_task.outpaint_selections]
        base_model_additional_loras = []
        async_task.uov_method = async_task.uov_method.casefold()
        async_task.enhance_uov_method = async_task.enhance_uov_method.casefold()

        if fooocus_expansion in async_task.style_selections:
            use_expansion = True
            async_task.style_selections.remove(fooocus_expansion)
        else:
            use_expansion = False

        use_style = len(async_task.style_selections) > 0

        if async_task.base_model_name == async_task.refiner_model_name:
            print(f'Refiner disabled because base model and refiner are same.')
            async_task.refiner_model_name = 'None'

        current_progress = 0
        if async_task.performance_selection == Performance.EXTREME_SPEED:
            set_lcm_defaults(async_task, current_progress, advance_progress=True)
        elif async_task.performance_selection == Performance.LIGHTNING:
            set_lightning_defaults(async_task, current_progress, advance_progress=True)
        elif async_task.performance_selection == Performance.HYPER_SD:
            set_hyper_sd_defaults(async_task, current_progress, advance_progress=True)

        print(f'[Parameters] Adaptive CFG = {async_task.adaptive_cfg}')
        print(f'[Parameters] CLIP Skip = {async_task.clip_skip}')
        print(f'[Parameters] Sharpness = {async_task.sharpness}')
        print(f'[Parameters] ControlNet Softness = {async_task.controlnet_softness}')
        print(f'[Parameters] ADM Scale = '
              f'{async_task.adm_scaler_positive} : '
              f'{async_task.adm_scaler_negative} : '
              f'{async_task.adm_scaler_end}')
        print(f'[Parameters] Seed = {async_task.seed}')

        apply_patch_settings(async_task)

        print(f'[Parameters] CFG = {async_task.cfg_scale}')

        initial_latent = None
        denoising_strength = 1.0
        tiled = False

        width, height = async_task.aspect_ratios_selection.replace('×', ' ').split(' ')[:2]
        width, height = int(width), int(height)

        skip_prompt_processing = False

        inpaint_worker.current_task = None
        inpaint_parameterized = async_task.inpaint_engine != 'None'
        inpaint_image = None
        inpaint_mask = None
        inpaint_head_model_path = None

        use_synthetic_refiner = False

        controlnet_canny_path = None
        controlnet_cpds_path = None
        clip_vision_path, ip_negative_path, ip_adapter_path, ip_adapter_face_path = None, None, None, None

        goals = []
        tasks = []
        current_progress = 1

        if async_task.input_image_checkbox:
            base_model_additional_loras, clip_vision_path, controlnet_canny_path, controlnet_cpds_path, inpaint_head_model_path, inpaint_image, inpaint_mask, ip_adapter_face_path, ip_adapter_path, ip_negative_path, skip_prompt_processing, use_synthetic_refiner = apply_image_input(
                async_task, base_model_additional_loras, clip_vision_path, controlnet_canny_path, controlnet_cpds_path,
                goals, inpaint_head_model_path, inpaint_image, inpaint_mask, inpaint_parameterized, ip_adapter_face_path,
                ip_adapter_path, ip_negative_path, skip_prompt_processing, use_synthetic_refiner)

        controlnet_canny_path, controlnet_cpds_path = prepare_pro_mode_structure_control(
            async_task, controlnet_canny_path, controlnet_cpds_path
        )

        # Load or unload CNs
        progressbar(async_task, current_progress, 'Loading control models ...')
        pipeline.refresh_controlnets([controlnet_canny_path, controlnet_cpds_path])
        ip_adapter.load_ip_adapter(clip_vision_path, ip_negative_path, ip_adapter_path)
        ip_adapter.load_ip_adapter(clip_vision_path, ip_negative_path, ip_adapter_face_path)

        async_task.steps, switch, width, height = apply_overrides(async_task, async_task.steps, height, width)

        print(f'[Parameters] Sampler = {async_task.sampler_name} - {async_task.scheduler_name}')
        print(f'[Parameters] Steps = {async_task.steps} - {switch}')

        progressbar(async_task, current_progress, 'Initializing ...')

        loras = async_task.loras
        if not skip_prompt_processing:
            tasks, use_expansion, loras, current_progress = process_prompt(async_task, async_task.prompt, async_task.negative_prompt,
                                                         base_model_additional_loras, async_task.image_number,
                                                         async_task.disable_seed_increment, use_expansion, use_style,
                                                         use_synthetic_refiner, current_progress, advance_progress=True)

        if len(goals) > 0:
            current_progress += 1
            progressbar(async_task, current_progress, 'Image processing ...')

        configure_pro_mode_detail_pass(async_task)
        should_enhance = async_task.enhance_checkbox and (async_task.enhance_uov_method != flags.disabled.casefold() or len(async_task.enhance_ctrls) > 0)

        if 'vary' in goals:
            async_task.uov_input_image, denoising_strength, initial_latent, width, height, current_progress = apply_vary(
                async_task, async_task.uov_method, denoising_strength, async_task.uov_input_image, switch,
                current_progress)

        if 'upscale' in goals:
            direct_return, async_task.uov_input_image, denoising_strength, initial_latent, tiled, width, height, current_progress = apply_upscale(
                async_task, async_task.uov_input_image, async_task.uov_method, switch, current_progress,
                advance_progress=True)
            if direct_return:
                d = [('Upscale (Fast)', 'upscale_fast', '2x')]
                if should_censor(async_task.black_out_nsfw):
                    progressbar(async_task, 100, 'Checking for NSFW content ...')
                    async_task.uov_input_image = default_censor(async_task.uov_input_image)
                progressbar(async_task, 100, 'Saving image to system ...')
                uov_input_image_path = log(async_task.uov_input_image, d, output_format=async_task.output_format)
                yield_result(async_task, uov_input_image_path, 100, async_task.black_out_nsfw, False,
                             do_not_show_finished_images=True)
                return

        if 'inpaint' in goals:
            try:
                denoising_strength, initial_latent, width, height, current_progress = apply_inpaint(async_task,
                                                                                                    initial_latent,
                                                                                                    inpaint_head_model_path,
                                                                                                    inpaint_image,
                                                                                                    inpaint_mask,
                                                                                                    inpaint_parameterized,
                                                                                                    async_task.inpaint_strength,
                                                                                                    async_task.inpaint_respective_field,
                                                                                                    switch,
                                                                                                    async_task.inpaint_disable_initial_latent,
                                                                                                    current_progress,
                                                                                                    advance_progress=True)
            except EarlyReturnException:
                return

        if 'cn' in goals:
            apply_control_nets(async_task, height, ip_adapter_face_path, ip_adapter_path, width, current_progress)
            if async_task.debugging_cn_preprocessor:
                return

        if async_task.freeu_enabled:
            apply_freeu(async_task)

        # async_task.steps can have value of uov steps here when upscale has been applied
        steps, _, _, _ = apply_overrides(async_task, async_task.steps, height, width)

        images_to_enhance = []
        if 'enhance' in goals:
            if getattr(async_task, 'fix_face_enabled', False):
                n = max(1, int(getattr(async_task, 'fix_face_variants', 1)))
                base_img = async_task.enhance_input_image
                images_to_enhance += [np.ascontiguousarray(base_img.copy()) for _ in range(n)]
                async_task.image_number = n
                height, width, _ = base_img.shape
                print(f'[Sunside FixFace] queued {n} face variant(s) from Image Number')
            else:
                async_task.image_number = 1
                images_to_enhance += [async_task.enhance_input_image]
                height, width, _ = async_task.enhance_input_image.shape
            # input image already provided, processing is skipped
            steps = 0
            yield_result(async_task, async_task.enhance_input_image, current_progress, async_task.black_out_nsfw, False,
                         async_task.disable_intermediate_results)

        all_steps = steps * async_task.image_number

        if async_task.enhance_checkbox and async_task.enhance_uov_method != flags.disabled.casefold():
            enhance_upscale_steps = async_task.performance_selection.steps()
            if 'upscale' in async_task.enhance_uov_method:
                if 'fast' in async_task.enhance_uov_method:
                    enhance_upscale_steps = 0
                else:
                    enhance_upscale_steps = async_task.performance_selection.steps_uov()
            enhance_upscale_steps, _, _, _ = apply_overrides(async_task, enhance_upscale_steps, height, width)
            enhance_upscale_steps_total = async_task.image_number * enhance_upscale_steps
            all_steps += enhance_upscale_steps_total

        if async_task.enhance_checkbox and len(async_task.enhance_ctrls) != 0:
            enhance_steps, _, _, _ = apply_overrides(async_task, async_task.original_steps, height, width)
            all_steps += async_task.image_number * len(async_task.enhance_ctrls) * enhance_steps

        all_steps = max(all_steps, 1)

        print(f'[Parameters] Denoising Strength = {denoising_strength}')

        if isinstance(initial_latent, dict) and 'samples' in initial_latent:
            log_shape = initial_latent['samples'].shape
        else:
            log_shape = f'Image Space {(height, width)}'

        print(f'[Parameters] Initial Latent shape: {log_shape}')

        preparation_time = time.perf_counter() - preparation_start_time
        print(f'Preparation time: {preparation_time:.2f} seconds')

        final_scheduler_name = patch_samplers(async_task)
        print(f'Using {final_scheduler_name} scheduler.')

        async_task.yields.append(['preview', (current_progress, 'Moving model to GPU ...', None)])

        processing_start_time = time.perf_counter()

        preparation_steps = current_progress
        total_count = async_task.image_number

        def callback(step, x0, x, total_steps, y):
            if step == 0:
                async_task.callback_steps = 0
            async_task.callback_steps += (100 - preparation_steps) / float(all_steps)
            async_task.yields.append(['preview', (
                int(current_progress + async_task.callback_steps),
                f'Sampling step {step + 1}/{total_steps}, image {current_task_id + 1}/{total_count} ...', y)])

        show_intermediate_results = len(tasks) > 1 or async_task.should_enhance
        persist_image = not async_task.should_enhance or not async_task.save_final_enhanced_image_only

        for current_task_id, task in enumerate(tasks):
            progressbar(async_task, current_progress, f'Preparing task {current_task_id + 1}/{async_task.image_number} ...')
            execution_start_time = time.perf_counter()

            try:
                imgs, img_paths, current_progress = process_task(all_steps, async_task, callback, controlnet_canny_path,
                                                                 controlnet_cpds_path, current_task_id,
                                                                 denoising_strength, final_scheduler_name, goals,
                                                                 initial_latent, async_task.steps, switch, task['c'],
                                                                 task['uc'], task, loras, tiled, use_expansion, width,
                                                                 height, current_progress, preparation_steps,
                                                                 async_task.image_number, show_intermediate_results,
                                                                 persist_image)

                current_progress = int(preparation_steps + (100 - preparation_steps) / float(all_steps) * async_task.steps * (current_task_id + 1))
                images_to_enhance += imgs

            except ldm_patched.modules.model_management.InterruptProcessingException:
                if async_task.last_stop == 'skip':
                    print('User skipped')
                    async_task.last_stop = False
                    continue
                else:
                    print('User stopped')
                    break

            del task['c'], task['uc']  # Save memory
            execution_time = time.perf_counter() - execution_start_time
            print(f'Generating and saving time: {execution_time:.2f} seconds')

        if not async_task.should_enhance:
            print(f'[Enhance] Skipping, preconditions aren\'t met')
            stop_processing(async_task, processing_start_time)
            return

        progressbar(async_task, current_progress, 'Processing enhance ...')

        active_enhance_tabs = len(async_task.enhance_ctrls)
        should_process_enhance_uov = async_task.enhance_uov_method != flags.disabled.casefold()
        enhance_uov_before = False
        enhance_uov_after = False
        if should_process_enhance_uov:
            active_enhance_tabs += 1
            enhance_uov_before = async_task.enhance_uov_processing_order == flags.enhancement_uov_before
            enhance_uov_after = async_task.enhance_uov_processing_order == flags.enhancement_uov_after
        total_count = len(images_to_enhance) * active_enhance_tabs
        async_task.images_to_enhance_count = len(images_to_enhance)

        base_progress = current_progress
        current_task_id = -1
        done_steps_upscaling = 0
        done_steps_inpainting = 0
        enhance_steps, _, _, _ = apply_overrides(async_task, async_task.original_steps, height, width)
        exception_result = None
        for index, img in enumerate(images_to_enhance):
            async_task.enhance_stats[index] = 0
            enhancement_image_start_time = time.perf_counter()

            last_enhance_prompt = async_task.prompt
            last_enhance_negative_prompt = async_task.negative_prompt

            if enhance_uov_before:
                current_task_id += 1
                persist_image = not async_task.save_final_enhanced_image_only or active_enhance_tabs == 0
                current_task_id, done_steps_inpainting, done_steps_upscaling, img, exception_result = enhance_upscale(
                    all_steps, async_task, base_progress, callback, controlnet_canny_path, controlnet_cpds_path,
                    ip_adapter_face_path, ip_adapter_path,
                    current_task_id, denoising_strength, done_steps_inpainting, done_steps_upscaling, enhance_steps,
                    async_task.prompt, async_task.negative_prompt, final_scheduler_name, height, img, preparation_steps,
                    switch, tiled, total_count, use_expansion, use_style, use_synthetic_refiner, width, persist_image)
                async_task.enhance_stats[index] += 1

                if exception_result == 'continue':
                    continue
                elif exception_result == 'break':
                    break

            # inpaint for all other tabs
            for enhance_mask_dino_prompt_text, enhance_prompt, enhance_negative_prompt, enhance_mask_model, enhance_mask_cloth_category, enhance_mask_sam_model, enhance_mask_text_threshold, enhance_mask_box_threshold, enhance_mask_sam_max_detections, enhance_inpaint_disable_initial_latent, enhance_inpaint_engine, enhance_inpaint_strength, enhance_inpaint_respective_field, enhance_inpaint_erode_or_dilate, enhance_mask_invert in async_task.enhance_ctrls:
                current_task_id += 1
                current_progress = int(base_progress + (100 - preparation_steps) / float(all_steps) * (done_steps_upscaling + done_steps_inpainting))
                progressbar(async_task, current_progress, f'Preparing enhancement {current_task_id + 1}/{total_count} ...')
                enhancement_task_start_time = time.perf_counter()
                is_last_enhance_for_image = (current_task_id + 1) % active_enhance_tabs == 0 and not enhance_uov_after
                persist_image = not async_task.save_final_enhanced_image_only or is_last_enhance_for_image

                extras = {}
                if enhance_mask_model == 'sam':
                    print(f'[Enhance] Searching for "{enhance_mask_dino_prompt_text}"')
                elif enhance_mask_model == 'u2net_cloth_seg':
                    extras['cloth_category'] = enhance_mask_cloth_category

                # Fix Face: never use rembg/SAM/DINO (CuPy/numpy breaks on Colab) — facexlib bbox only
                if getattr(async_task, 'fix_face_enabled', False):
                    from modules.face_fix_mask import face_bbox_mask
                    print('[Sunside FixFace] building face mask (facexlib, no SAM/rembg)')
                    mask = face_bbox_mask(img)
                    if mask is None:
                        print('[Sunside FixFace] no face found — skip variant')
                        continue
                    dino_detection_count = 1
                    sam_detection_count = 1
                    sam_detection_on_mask_count = 1
                else:
                    if generate_mask_from_image is None:
                        print(f'[Enhance] Mask generation unavailable, skipping: {_inpaint_mask_import_error}')
                        continue

                    mask, dino_detection_count, sam_detection_count, sam_detection_on_mask_count = generate_mask_from_image(
                        img, mask_model=enhance_mask_model, extras=extras, sam_options=SAMOptions(
                            dino_prompt=enhance_mask_dino_prompt_text,
                            dino_box_threshold=enhance_mask_box_threshold,
                            dino_text_threshold=enhance_mask_text_threshold,
                            dino_erode_or_dilate=async_task.dino_erode_or_dilate,
                            dino_debug=async_task.debugging_dino,
                            max_detections=enhance_mask_sam_max_detections,
                            model_type=enhance_mask_sam_model,
                        ))

                if mask is None:
                    print('[Enhance] empty mask, skipping')
                    continue
                if len(mask.shape) == 3:
                    mask = mask[:, :, 0]

                if int(enhance_inpaint_erode_or_dilate) != 0:
                    mask = erode_or_dilate(mask, enhance_inpaint_erode_or_dilate)

                if enhance_mask_invert:
                    mask = 255 - mask

                if async_task.debugging_enhance_masks_checkbox:
                    async_task.yields.append(['preview', (current_progress, 'Loading ...', mask)])
                    yield_result(async_task, mask, current_progress, async_task.black_out_nsfw, False,
                                 async_task.disable_intermediate_results)
                    async_task.enhance_stats[index] += 1

                print(f'[Enhance] {dino_detection_count} boxes detected')
                print(f'[Enhance] {sam_detection_count} segments detected in boxes')
                print(f'[Enhance] {sam_detection_on_mask_count} segments applied to mask')

                if not getattr(async_task, 'fix_face_enabled', False):
                    if enhance_mask_model == 'sam' and (dino_detection_count == 0 or not async_task.debugging_dino and sam_detection_on_mask_count == 0):
                        print(f'[Enhance] No "{enhance_mask_dino_prompt_text}" detected, skipping')
                        continue

                goals_enhance = ['inpaint']

                try:
                    if getattr(async_task, 'fix_face_enabled', False):
                        import modules.constants as constants
                        base = int(getattr(async_task, '_fix_face_seed_base', async_task.seed))
                        async_task.seed = (base + index) % (constants.MAX_SEED + 1)
                        print(f'[Sunside FixFace] variant {index + 1}/{len(images_to_enhance)} seed={async_task.seed}')

                    current_progress, img, enhance_prompt_processed, enhance_negative_prompt_processed = process_enhance(
                        all_steps, async_task, callback, controlnet_canny_path, controlnet_cpds_path,
                        ip_adapter_face_path, ip_adapter_path,
                        current_progress, current_task_id, denoising_strength, enhance_inpaint_disable_initial_latent,
                        enhance_inpaint_engine, enhance_inpaint_respective_field, enhance_inpaint_strength,
                        enhance_prompt, enhance_negative_prompt, final_scheduler_name, goals_enhance, height, img, mask,
                        preparation_steps, enhance_steps, switch, tiled, total_count, use_expansion, use_style,
                        use_synthetic_refiner, width, persist_image=persist_image)
                    async_task.enhance_stats[index] += 1

                    if (should_process_enhance_uov and async_task.enhance_uov_processing_order == flags.enhancement_uov_after
                            and async_task.enhance_uov_prompt_type == flags.enhancement_uov_prompt_type_last_filled):
                        if enhance_prompt_processed != '':
                            last_enhance_prompt = enhance_prompt_processed
                        if enhance_negative_prompt_processed != '':
                            last_enhance_negative_prompt = enhance_negative_prompt_processed

                except ldm_patched.modules.model_management.InterruptProcessingException:
                    if async_task.last_stop == 'skip':
                        print('User skipped')
                        async_task.last_stop = False
                        continue
                    else:
                        print('User stopped')
                        exception_result = 'break'
                        break
                finally:
                    done_steps_inpainting += enhance_steps

                enhancement_task_time = time.perf_counter() - enhancement_task_start_time
                print(f'Enhancement time: {enhancement_task_time:.2f} seconds')

            if exception_result == 'break':
                break

            if enhance_uov_after:
                current_task_id += 1
                # last step in enhance, always save
                persist_image = True
                current_task_id, done_steps_inpainting, done_steps_upscaling, img, exception_result = enhance_upscale(
                    all_steps, async_task, base_progress, callback, controlnet_canny_path, controlnet_cpds_path,
                    ip_adapter_face_path, ip_adapter_path,
                    current_task_id, denoising_strength, done_steps_inpainting, done_steps_upscaling, enhance_steps,
                    last_enhance_prompt, last_enhance_negative_prompt, final_scheduler_name, height, img,
                    preparation_steps, switch, tiled, total_count, use_expansion, use_style, use_synthetic_refiner,
                    width, persist_image)
                async_task.enhance_stats[index] += 1
                
                if exception_result == 'continue':
                    continue
                elif exception_result == 'break':
                    break

            enhancement_image_time = time.perf_counter() - enhancement_image_start_time
            print(f'Enhancement image time: {enhancement_image_time:.2f} seconds')

        stop_processing(async_task, processing_start_time)
        return

    while True:
        time.sleep(0.01)
        if len(async_tasks) > 0:
            task = async_tasks.pop(0)

            try:
                handler(task)
                apply_pro_mode_ranking(task)
                if task.generate_image_grid:
                    build_image_wall(task)
                task.yields.append(['finish', task.results])
                pipeline.prepare_text_encoder(async_call=True)
            except:
                traceback.print_exc()
                task.yields.append(['finish', task.results])
            finally:
                if pid in modules.patch.patch_settings:
                    del modules.patch.patch_settings[pid]
    pass


threading.Thread(target=worker, daemon=True).start()

import json
import constants as cst
from base_model import (
    ModelEnum,
    InpaintingBase,
    UpscaleBase,
    TextToImagebase,
    ImageToImageBase,
    AvatarBase,
    OutpaintingBase,
)
from typing import Dict, Any, Tuple, List
from utils.base64_utils import base64_to_image
import os
from loguru import logger
import copy
import random


class PayloadModifier:
    def __init__(self):
        self._payloads = {}
        self._load_workflows()

    def _load_workflows(self):
        directory = cst.WORKFLOWS_DIR
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "r") as file:
                    try:
                        data = json.load(file)
                        self._payloads[os.path.splitext(filename)[0]] = data
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON from {filename}: {e}")

    def modify_inpaint(self, input_data: InpaintingBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["inpaint"])
        init_img = base64_to_image(input_data.init_image)
        init_img.save(f"{cst.COMFY_INPUT_PATH}init.png")
        mask_img = base64_to_image(input_data.mask_image)
        mask_img.save(f"{cst.COMFY_INPUT_PATH}mask.png")
        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        payload["Sampler"]["inputs"]["cfg"] = input_data.cfg_scale

        positive_prompt, negative_prompt = input_data.prompt, input_data.negative_prompt

        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["noise_seed"] = seed
        return payload

    def modify_outpaint(self, input_data: OutpaintingBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["outpaint"])
        init_img = base64_to_image(input_data.init_image)
        init_img.save(f"{cst.COMFY_INPUT_PATH}init.png")

        positive_prompt, negative_prompt = input_data.prompt, input_data.negative_prompt
        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt

        for position in input_data.pad_values:
            payload["Outpaint_pad"]["inputs"][position] = input_data.pad_values[position]

        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["noise_seed"] = seed
        return payload

    def modify_text_to_image(self, input_data: TextToImagebase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads[f"{input_data.model}"])

        positive_prompt, negative_prompt = input_data.prompt, input_data.negative_prompt
        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        payload["Latent"]["inputs"]["width"] = input_data.width
        payload["Latent"]["inputs"]["height"] = input_data.height
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        if "flux" in input_data.model:
            payload["Seed"]["inputs"]["noise_seed"] = seed
            payload["Guidance"]["inputs"]["guidance"] = input_data.cfg_scale
        else:
            payload["Negative_prompt"]["inputs"]["text"] += negative_prompt
            payload["Sampler"]["inputs"]["cfg"] = input_data.cfg_scale
            payload["Sampler"]["inputs"]["seed"] = seed

        return payload

    def modify_image_to_image(self, input_data: ImageToImageBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads[f"{input_data.model}"])
        init_img = base64_to_image(input_data.init_image)
        init_img.save(f"{cst.COMFY_INPUT_PATH}init.png")

        positive_prompt, negative_prompt = input_data.prompt, input_data.negative_prompt
        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        payload["Sampler"]["inputs"]["denoise"] = 1 - input_data.image_strength
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        if "flux" in input_data.model:
            payload["Seed"]["inputs"]["noise_seed"] = seed
            payload["Guidance"]["inputs"]["guidance"] = input_data.cfg_scale
        else:
            payload["Negative_prompt"]["inputs"]["text"] += negative_prompt
            payload["Sampler"]["inputs"]["cfg"] = input_data.cfg_scale
            payload["Sampler"]["inputs"]["seed"] = seed

        logger.debug(f"payload: {payload}")
        return payload

    def modify_upscale(self, input_data: UpscaleBase) -> Dict[str, Any]:
        workflow_name = "upscale_sampled" if input_data.sampled else "upscale"
        payload = copy.deepcopy(self._payloads[workflow_name])
        init_img = base64_to_image(input_data.init_image)
        init_img.save(f"{cst.COMFY_INPUT_PATH}init.png")
        return payload

    def modify_avatar(self, input_data: AvatarBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["instantid"])
        init_img = base64_to_image(input_data.init_image)
        init_img.save(f"{cst.COMFY_INPUT_PATH}init.png")

        positive_prompt, negative_prompt = input_data.prompt, input_data.negative_prompt
        payload["Prompt"]["inputs"]["text"] += positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt

        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["seed"] = seed
        payload["Sampler_initial"]["inputs"]["seed"] = seed
        payload["Latent"]["inputs"]["width"] = input_data.width
        payload["Latent"]["inputs"]["height"] = input_data.height
        payload["InstantID"]["inputs"]["ip_weight"] = input_data.ipadapter_strength
        payload["InstantID"]["inputs"]["cn_strength"] = input_data.control_strength
        return payload

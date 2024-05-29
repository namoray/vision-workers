import json
import constants as cst
from base_model import (
    InpaintingBase,
    UpscaleBase,
    Txt2ImgBase,
    Img2ImgBase,
    AvatarBase,
    OutpaintingBase,
)
from typing import Dict, Any, Tuple, List
from utils.base64_utils import base64_to_image
import os
import copy
import random


def _extract_positive_and_negative_prompts(
    text_prompts: List[Dict[str, Any]],
) -> Tuple[str, str]:
    positive_prompt = ""
    negative_prompt = ""

    for prompt in text_prompts:
        weight = prompt.get("weight", None)
        if weight is None or weight >= 0:
            positive_prompt += " " + prompt["text"]
        else:
            negative_prompt += " " + prompt["text"]

    return positive_prompt.strip(), negative_prompt.strip()


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
                        print(f"Error decoding JSON from {filename}: {e}")

    def modify_inpaint(self, input_data: InpaintingBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["inpaint"])
        payload["Image_loader"]["inputs"]["image"] = input_data.init_image
        payload["Mask_loader"]["inputs"]["mask"] = input_data.mask_image
        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        payload["Sampler"]["inputs"]["cfg"] = input_data.cfg_scale

        positive_prompt, negative_prompt = _extract_positive_and_negative_prompts(
            input_data.text_prompts
        )

        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["noise_seed"] = seed
        return payload

    def modify_outpaint(self, input_data: OutpaintingBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["outpaint"])
        payload["Image_loader"]["inputs"]["image"] = input_data.init_image

        positive_prompt, negative_prompt = _extract_positive_and_negative_prompts(
            input_data.text_prompts
        )
        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt

        for position in input_data.pad_values:
            payload["Outpaint_pad"]["inputs"][position] = input_data.pad_values[
                position
            ]

        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["noise_seed"] = seed
        return payload

    def modify_txt2img(self, input_data: Txt2ImgBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads[f"txt2img_{input_data.engine}"])

        positive_prompt, negative_prompt = _extract_positive_and_negative_prompts(
            input_data.text_prompts
        )
        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt

        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        payload["Sampler"]["inputs"]["cfg"] = input_data.cfg_scale
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["seed"] = seed
        payload["Latent"]["inputs"]["width"] = input_data.width
        payload["Latent"]["inputs"]["height"] = input_data.height
        return payload

    def modify_img2img(self, input_data: Img2ImgBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads[f"img2img_{input_data.engine}"])
        payload["Image_loader"]["inputs"]["image"] = input_data.init_image

        positive_prompt, negative_prompt = _extract_positive_and_negative_prompts(
            input_data.text_prompts
        )
        payload["Prompt"]["inputs"]["text"] = positive_prompt
        payload["Negative_prompt"]["inputs"]["text"] += negative_prompt

        payload["Sampler"]["inputs"]["steps"] = input_data.steps
        payload["Sampler"]["inputs"]["cfg"] = input_data.cfg_scale
        seed = input_data.seed
        if seed == 0:
            seed = random.randint(1, 2**16)
        payload["Sampler"]["inputs"]["seed"] = seed
        payload["Sampler"]["inputs"]["denoise"] = 1 - input_data.image_strength
        return payload

    def modify_upscale(self, input_data: UpscaleBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["upscale"])
        payload["Image_loader"]["inputs"]["image"] = input_data.init_image
        return payload

    def modify_avatar(self, input_data: AvatarBase) -> Dict[str, Any]:
        payload = copy.deepcopy(self._payloads["instantid"])
        payload["Image_loader"]["inputs"]["image"] = input_data.init_image

        positive_prompt, negative_prompt = _extract_positive_and_negative_prompts(
            input_data.text_prompts
        )
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
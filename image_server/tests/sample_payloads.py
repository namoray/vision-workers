SAMPLE_PAYLOAD_PROTEUS = {
    "prompt": "dolphin",
    "negative_prompt": "",
    "steps": 30,
    "model": "proteusV0.5.safetensors",
    "cfg_scale": 7,
    "height": 1024,
    "width": 1024,
    "seed": 0,
    "sampler": "dpmpp_2m_sde_gpu",
    "scheduler": "karras",
}

SAMPLE_PAYLOAD_DREAMSHAPER = {
  "prompt": "a man on moon",
  "negative_prompt": "",
  "steps": 5,
  "model": "DreamShaperXL_Lightning-SFW.safetensors",
  "cfg_scale": 2,
  "height": 1024,
  "width": 1024,
  "seed": 0,
  "sampler": "dpmpp_sde_gpu",
  "scheduler": "karras"
}

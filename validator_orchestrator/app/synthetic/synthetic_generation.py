from app import incoming_models
from app import utility_models
import markovify
import datasets
import random
from app import utils
import diskcache
from app import constants

# def generate_params(engine: utility_models.EngineEnum, params_to_vary: List[str]):
#     params = {}

#     for param in request_models.ALLOWED_PARAMS_FOR_ENGINE[engine]:
#         if param in params_to_vary:
#             value = request_models.ALLOWED_PARAMS_FOR_ENGINE[engine][param]["generator"]()
#             params[param] = value
#     return params

dataset = datasets.load_dataset("multi-train/coco_captions_1107")
text = [i["query"] for i in dataset["train"]]
markov_text_generation_model = markovify.Text(" ".join(text))
cache = diskcache.Cache("./image_cache")
MAX_SEED = 4294967295


def _get_markov_sentence(max_words: int = 10) -> str:
    text = None
    while text is None:
        text = markov_text_generation_model.make_sentence(max_words=max_words)
    return text


async def generate_chat_synthetic(model: str) -> incoming_models.ChatIncoming:
    user_content = _get_markov_sentence(max_words=80)
    messages = [
        utility_models.Message(
            content=user_content, role=utility_models.Role.user.value
        )
    ]

    if random.random() < 0.1:
        messages.append(
            utility_models.Message(
                content=_get_markov_sentence(max_words=80),
                role=utility_models.Role.assistant.value,
            )
        )
        messages.append(
            utility_models.Message(
                content=_get_markov_sentence(max_words=80),
                role=utility_models.Role.user.value,
            )
        )
    return incoming_models.ChatIncoming(
        messages=messages,
        top_p=1,
        seed=random.randint(1, MAX_SEED),
        temperature=round(random.random(), 1),
        max_tokens=1024,
        model=model,
    )


async def generate_text_to_image_synthetic(
    engine: str,
) -> incoming_models.TextToImageIncoming:
    positive_text = _get_markov_sentence(max_words=20)
    text_prompts = [utility_models.TextPrompt(text=positive_text, weight=1.0)]
    seed = random.randint(1, MAX_SEED)

    if engine == utility_models.EngineEnum.PLAYGROUND.value:
        height = 1024
        width = 1024
        cfg_scale = 4.0
        steps = 30
    elif engine == utility_models.EngineEnum.PROTEUS.value:
        height = 1280
        width = 1280
        cfg_scale = 2.0
        steps = 8
    elif engine == utility_models.EngineEnum.DREAMSHAPER.value:
        height = 1024
        width = 1024
        cfg_scale = 3.5
        steps = 8
    else:
        raise ValueError(f"Engine {engine} not supported")

    return incoming_models.TextToImageIncoming(
        text_prompts=text_prompts,
        seed=seed,
        engine=engine,
        height=height,
        width=width,
        cfg_scale=cfg_scale,
        steps=steps,
    )


async def generate_image_to_image_synthetic(
    engine: str,
) -> incoming_models.ImageToImageIncoming:
    positive_text = _get_markov_sentence(max_words=20)
    text_prompts = [utility_models.TextPrompt(text=positive_text, weight=1.0)]
    seed = random.randint(1, MAX_SEED)

    if engine == utility_models.EngineEnum.PLAYGROUND.value:
        height = 1024
        width = 1024
        cfg_scale = 4.0
        steps = 30
        image_strength = 0.5
    elif engine == utility_models.EngineEnum.PROTEUS.value:
        height = 1280
        width = 1280
        cfg_scale = 2.0
        steps = 8
        image_strength = 0.5
    elif engine == utility_models.EngineEnum.DREAMSHAPER.value:
        height = 1024
        width = 1024
        cfg_scale = 3.5
        steps = 8
        image_strength = 0.5
    else:
        raise ValueError(f"Engine {engine} not supported")

    init_image = await utils.get_random_image_b64(cache)

    return incoming_models.ImageToImageIncoming(
        init_image=init_image,
        image_strength=image_strength,
        text_prompts=text_prompts,
        seed=seed,
        engine=engine,
        height=height,
        width=width,
        cfg_scale=cfg_scale,
        steps=steps,
    )


async def generate_inpaint_synthetic() -> incoming_models.InpaintIncoming:
    positive_text = _get_markov_sentence(max_words=20)
    text_prompts = [utility_models.TextPrompt(text=positive_text, weight=1.0)]
    seed = random.randint(1, MAX_SEED)

    init_image = await utils.get_random_image_b64(cache)
    mask_image = utils.generate_mask_with_circle(init_image)

    return incoming_models.InpaintIncoming(
        text_prompts=text_prompts,
        init_image=init_image,
        ipadapter_strength=0.5,
        control_strength=0.5,
        seed=seed,
        mask_image=mask_image,
        height=1016,
        width=1016,
        steps=8,
    )


async def generate_avatar_synthetic() -> incoming_models.AvatarIncoming:
    positive_text = _get_markov_sentence(max_words=20)
    text_prompts = [utility_models.TextPrompt(text=positive_text, weight=1.0)]
    seed = random.randint(1, MAX_SEED)

    init_image = utils.get_randomly_edited_face_picture_for_avatar()

    return incoming_models.AvatarIncoming(
        init_image=init_image,
        text_prompts=text_prompts,
        ipadapter_strength=0.5,
        control_strength=0.5,
        height=1280,
        width=1280,
        seed=seed,
        steps=8,
    )


async def generate_upscale_synthetic() -> incoming_models.UpscaleIncoming:
    init_image = await utils.get_random_image_b64(cache)
    init_image = utils.resize_image(init_image)

    return incoming_models.UpscaleIncoming(
        image=init_image,
    )


async def generate_clip_synthetic() -> incoming_models.ClipEmbeddingsIncoming:
    init_image = await utils.get_random_image_b64(cache)

    if init_image is None:
        raise ValueError("No images found")

    return incoming_models.ClipEmbeddingsIncoming(
        image_b64s=[init_image],
    )


async def generate_sota_synthetic() -> None:
    nsfw_prompt = True
    while nsfw_prompt:
        positive_text = _get_markov_sentence(max_words=20)[:-1]
        for bad_word in constants.MJ_BANNED_WORDS:
            if bad_word in positive_text:
                nsfw_prompt = True
                break
            else:
                nsfw_prompt = False
    seed = random.randint(1, MAX_SEED)

    positive_text += f"  --seed {seed} --ar 1:1  --v 6"

    return incoming_models.SotaIncoming(prompt=positive_text)

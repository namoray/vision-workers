from pydantic_settings import BaseSettings
from app import models
from app.checking import checking_functions, speed_scoring_functions
from app.synthetic import synthetic_generation
from app import utility_models
from enum import Enum


class Settings(BaseSettings):
    version: str = "1.0.0"
    environment: str = "prod"
    debug: bool = False
    cors_origins: list[str] = ["*"]


class Endpoints(Enum):
    text_to_image = "/txt2img"
    image_to_image = "/img2img"
    avatar = "/avatar"
    inpaint = "/inpaint"
    upscale = "/upscale"
    clip_embeddings = "/clip-embeddings"


settings = Settings()


BASE_URL = "http://localhost:6919"


task_configs = models.TaskConfigMapping(
    tasks={
        models.Tasks.chat_bittensor_finetune.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="tau-vision/sn6-finetune",
                half_precision=False,
            ),
            checking_function=checking_functions.check_text_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_chat,
            endpoint=BASE_URL + "/generate_text",
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.bittensor_finetune.value
            },
            task=models.Tasks.chat_bittensor_finetune,
        ),
        models.Tasks.chat_mixtral.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-GPTQ",
                half_precision=True,
                revision="gptq-8bit-128g-actorder_True",
            ),
            endpoint=BASE_URL + "/generate_text",
            checking_function=checking_functions.check_text_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_chat,
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.mixtral.value
            },
            task=models.Tasks.chat_mixtral,
        ),
        models.Tasks.chat_llama_3.value: models.TaskConfig(
            server_needed=models.ServerType.LLM,
            load_model_config=models.ModelConfigDetails(
                model="casperhansen/llama-3-70b-instruct-awq",
                half_precision=True,
                tokenizer="tau-vision/llama-3-tokenizer-fix",
            ),
            endpoint=BASE_URL + "/generate_text",
            checking_function=checking_functions.check_text_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_chat,
            synthetic_generation_function=synthetic_generation.generate_chat_synthetic,
            synthetic_generation_params={
                "model": utility_models.ChatModels.llama_3.value
            },
            task=models.Tasks.chat_llama_3,
        ),
        models.Tasks.proteus_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            # todo: change this
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PROTEUS.value
            },
            task=models.Tasks.proteus_text_to_image,
        ),
        models.Tasks.playground_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            # todo: change this
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PLAYGROUND.value
            },
            task=models.Tasks.playground_text_to_image,
        ),
        models.Tasks.dreamshaper_text_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            # todo: change this
            endpoint=BASE_URL + Endpoints.text_to_image.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_text_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.DREAMSHAPER.value
            },
            task=models.Tasks.dreamshaper_text_to_image,
        ),
        models.Tasks.proteus_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            # todo: change this
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PROTEUS.value
            },
            task=models.Tasks.proteus_image_to_image,
        ),
        models.Tasks.playground_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.PLAYGROUND.value
            },
            task=models.Tasks.playground_image_to_image,
        ),
        models.Tasks.dreamshaper_image_to_image.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.image_to_image.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_image_to_image_synthetic,
            synthetic_generation_params={
                "engine": utility_models.EngineEnum.DREAMSHAPER.value
            },
            task=models.Tasks.dreamshaper_image_to_image,
        ),
        models.Tasks.avatar.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.avatar.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_avatar_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.avatar,
        ),
        models.Tasks.jugger_inpainting.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.inpaint.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_inpaint_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.jugger_inpainting,
        ),
        models.Tasks.upscale.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.upscale.value,
            checking_function=checking_functions.check_image_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_images,
            synthetic_generation_function=synthetic_generation.generate_upscale_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.upscale,
        ),
        models.Tasks.clip_image_embeddings.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.clip_embeddings.value,
            checking_function=checking_functions.check_clip_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_clip,
            synthetic_generation_function=synthetic_generation.generate_clip_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.clip_image_embeddings,
        ),
        models.Tasks.sota.value: models.TaskConfig(
            server_needed=models.ServerType.IMAGE,
            load_model_config=None,
            endpoint=BASE_URL + Endpoints.clip_embeddings.value,
            checking_function=checking_functions.check_sota_result,
            speed_scoring_function=speed_scoring_functions.speed_scoring_sota,
            synthetic_generation_function=synthetic_generation.generate_sota_synthetic,
            synthetic_generation_params={},
            task=models.Tasks.sota,
        ),
    }
)

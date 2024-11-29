from app import schemas
from typing import List, Union
from app import models
from app.inference import toxic
from app.inference.state import EngineState
import json


async def _get_last_message_content(messages: List[models.Message]):
    if len(messages) == 0:
        return None
    last_prompt = messages[-1]
    return last_prompt.content


async def infer(
    request: Union[schemas.TextRequestModel, schemas.CompletionRequest],
    engine_state: EngineState,
    toxic_engine: models.ToxicEngine,
    base_completion: bool = False
):
    if type(request) == schemas.TextRequestModel:
        last_message_content = await _get_last_message_content(request.messages)
    else:
        last_message_content = request.prompt
    if toxic.prompt_is_toxic(toxic_engine, last_message_content):
        for o in "I am sorry, but that last request was deemed toxic, I am unable to answer.".split(" "):
            yield o + " "
    else:
        # Forward the request to the model process and stream the response back
        request_info = models.RequestInfo(**request.dict())
        request_info.base_completion = True
        response_stream = engine_state.forward_request(request_info)
        async for line in response_stream:
            if line:
                yield line + "\n\n"

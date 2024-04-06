from app import schemas


from typing import List
from app import models
from app.inference import toxic


async def _get_last_message_content(messages: List[models.Message]):
    if len(messages) == 0:
        return None
    last_prompt = messages[-1]
    return last_prompt.content


async def infer(
    request: schemas.TextRequestModel,
    engine: models.LLMEngine,
    toxic_engine: models.ToxicEngine,
):
    last_message_content = await _get_last_message_content(request.messages)
    if toxic.prompt_is_toxic(toxic_engine, last_message_content):
        for o in "I am sorry, but that last request was deemed toxic, I am unable to answer.".split(
            " "
        ):
            yield o + " "
        pass
    else:
        # below line does nothing before i came in, so just commented it out
        # prompt = await grab_the_right_prompt(request.messages)
        # TODO: FIX THIS
        async for chunk in engine.completion_method(engine, request):
            yield chunk

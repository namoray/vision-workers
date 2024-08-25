from fastapi import Request
from app.inference import state

async def get_engine_state(request: Request) -> state.modelState:
    return request.app.state.model_state
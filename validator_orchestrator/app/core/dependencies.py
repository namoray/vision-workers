from app import server_management
from fastapi import Request


async def get_server_manager(
    request: Request,
) -> server_management.ServerManager:
    return request.app.state.server_manager

import os
import signal
import subprocess
import httpx
from typing import Dict, Any
import asyncio
from app import models

from loguru import logger


class ServerManager:
    """
    This class manages starting, stopping, and handling of language and image servers.
    """

    cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", None)

    llm_command = "uvicorn --lifespan on --port 6919 --host 0.0.0.0  app.asgi:app"
    if cuda_visible_devices is not None:
        llm_command = f"CUDA_VISIBLE_DEVICES={cuda_visible_devices} {llm_command}"
    SERVER_COMMANDS = {
        models.ServerType.LLM: llm_command,
        models.ServerType.IMAGE: "./entrypoint_vali.sh warmup=false",
    }
    SERVER_DIRECTORIES = {
        models.ServerType.LLM: "../llm_server",
        models.ServerType.IMAGE: "../image_server",
    }

    def __init__(self):
        self.server_process = None
        self.llm_server_is_running: bool = False
        self.image_server_is_running: bool = False

    def _kill_process_on_port(self, port):
        """
        Kill the process running on the given port.
        """
        process = subprocess.Popen(
            ["lsof", "-i", f":{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, _ = process.communicate()
        for process_line in str(stdout.decode("utf-8")).split("\n")[1:]:
            data = process_line.split()
            if len(data) <= 1:
                continue
            pid = data[1]
            os.kill(int(pid), signal.SIGKILL)

    async def is_server_healthy(self) -> bool:
        """
        Check if server is healthy.
        """
        server_is_healthy = False
        async with httpx.AsyncClient(timeout=5) as client:
            while not server_is_healthy:
                try:
                    response = await client.get("http://localhost:6919")
                    server_is_healthy = response.status_code == 200
                    if not server_is_healthy:
                        await asyncio.sleep(2)
                except httpx.RequestError:
                    await asyncio.sleep(2)
                except KeyboardInterrupt:
                    break
        return server_is_healthy

    async def load_model(self, load_model_config: Dict[str, Any]) -> None:
        """
        Load a new model configuration
        """
        await self.is_server_healthy()
        try:
            async with httpx.AsyncClient(timeout=600) as client:
                response = await client.post(
                    url="http://127.0.0.1:6919/load_model",
                    json=load_model_config,
                )
            return response
        except httpx.HTTPError:
            raise Exception("Timeout when loading model :(")

    async def start_server(self, server_type: str):
        """
        Start a server of the given type.
        """

        if server_type == models.ServerType.LLM and self.llm_server_is_running:
            return
        if server_type == models.ServerType.IMAGE and self.image_server_is_running:
            return

        await self.stop_server()
        self._kill_process_on_port(6919)
        command = self.SERVER_COMMANDS[server_type]
        server_dir = self.SERVER_DIRECTORIES[server_type]

        logger.info(f"Starting server: {server_type} 🦄")
        self.server_process = subprocess.Popen(command, shell=True, cwd=server_dir)

        # Wait until server is healthy
        await self.is_server_healthy()

        if server_type == models.ServerType.LLM:
            self.llm_server_is_running = True
        elif server_type == models.ServerType.IMAGE:
            self.image_server_is_running = True

    async def stop_server(self):
        """
        Stop the currently running server.
        """
        if self.server_process:
            logger.info("Stopping the running server 😈")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
            self.llm_server_is_running = False
            self.image_server_is_running = False

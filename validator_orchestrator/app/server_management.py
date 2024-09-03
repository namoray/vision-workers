import os
import subprocess
from time import sleep
import httpx
from typing import Dict, Any
import asyncio
from loguru import logger
from app.Workers import worker_config
from app.core.models import ServerType
from app.core.constants import AI_SERVER_PORT


class ServerManager:
    """
    This class manages starting, stopping, and handling of language and image servers.
    """

    cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", None)
    if cuda_visible_devices is not None:
        gpus = cuda_visible_devices
    else:
        gpus = "all"

    docker_run_flags = f"--gpus {gpus} --runtime=nvidia"

    def __init__(self):
        self.server_process = None
        self.servers = {worker_config.name: worker_config for worker_config in worker_config.workers}
        self.running_servers = {worker_config.name: False for worker_config in worker_config.workers}

    def _kill_process_on_port(self, port):
        """
        Stop and remove Docker container running on the given port.
        """
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                check=True,
            )
            container_id = result.stdout.strip()

            if container_id:
                subprocess.run(["docker", "stop", container_id], check=True)
                subprocess.run(["docker", "rm", container_id], check=True)
                logger.info(f"Successfully stopped and removed the container running on port {port}.")
            else:
                logger.info(f"No container is running on port {port}.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop the container running on port {port}: {e}")

    async def is_server_healthy(
        self,
        port: int,
        sleep_time: int = 5,
        total_attempts: int = 12 * 10 * 2,  # 20 minutes worth
    ) -> tuple[bool, str | None]:
        """
        Check if server is healthy.
        """
        server_is_healthy = False
        i = 0
        await asyncio.sleep(sleep_time)
        async with httpx.AsyncClient(timeout=5) as client:
            while not server_is_healthy:
                try:
                    logger.info("Pinging " + f"http://localhost:{port}")
                    response = await client.get(f"http://localhost:{port}")
                    server_is_healthy = response.status_code == 200
                    if not server_is_healthy:
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.info(f"Server {port} is healthy!")
                        return server_is_healthy, response.content.decode()
                except httpx.RequestError:
                    await asyncio.sleep(sleep_time)
                except KeyboardInterrupt:
                    break
                i += 1
                if i > total_attempts:
                    break
        return server_is_healthy, None

    async def load_model(self, load_model_config: Dict[str, Any]) -> None:
        """
        Load a new model configuration
        """
        try:
            logger.debug(f"Loading model with config: {load_model_config}")
            async with httpx.AsyncClient(timeout=1200) as client:
                server_name = os.getenv("CURRENT_SERVER_NAME")
                response = await client.post(
                    url=f"http://localhost:{AI_SERVER_PORT}/load_model",
                    json=load_model_config,
                )
            return response
        except httpx.HTTPError:
            raise Exception("Timeout when loading model :(")

    async def start_server(self, server_type: ServerType):
        """
        Start a server with the given name.
        """
        server_name = server_type.value
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in {list(self.servers.keys())}")
            return
        server_config = self.servers[server_name]

        logger.info(f"Starting server: {server_name}. First checking if anything is running on 6919...")
        server_is_up, response_content = await self.is_server_healthy(
            port=server_config.port,
            sleep_time=1,
            total_attempts=3,
        )
        if response_content == "LLM":
            self.running_servers[ServerType.LLM.value] = True
        elif response_content is not None:
            self.running_servers[ServerType.IMAGE.value] = True

        if self.running_servers.get(server_name, False) and server_is_up:
            # Check no other server is running on the same port
            for server, is_running in self.running_servers.items():
                if is_running and server != server_name:
                    logger.info(f"The server {server} is running on the same port as {server_name}. Stopping it...")
                    return
            logger.info(f"Running servers: {self.running_servers}. Killing and restarting {server_name}")
        else:
            logger.info(f"Running servers: {self.running_servers}. Killing and restarting {server_name}")

        self._kill_process_on_port(server_config.port)
        subprocess.Popen(f"docker rm -f {server_config.name}", shell=True).wait()
        sleep(2)

        command = (
            f"docker run -d --rm --name {server_config.name} "
            + " ".join([f"-v {volume}:{mount_path}" for volume, mount_path in server_config.volumes.items()])
            + f" {self.docker_run_flags} "
            + f"-p {server_config.port}:{server_config.port} "
            + f"--network {server_config.network} "
            + f"{server_config.docker_image}"
        )

        logger.info(f"Starting server: {server_config.name} 🦄")

        self.server_process = subprocess.Popen(command, shell=True)

        server_is_up = await self.is_server_healthy(
            server_config.port,
        )
        if not server_is_up:
            raise Exception(f"Timeout when starting server {server_name}")

        os.environ["CURRENT_SERVER_NAME"] = server_config.name
        self.running_servers[server_name] = True

    async def stop_server(self):
        """
        Stop the currently running server.
        """
        logger.info(f"Here!")
        for server_name, is_running in self.running_servers.items():
            if is_running:
                logger.info(f"Stopping the running server container {server_name} 😈")

                try:
                    subprocess.run(["docker", "stop", server_name], check=True)
                    subprocess.run(["docker", "rm", server_name], check=True)
                    logger.info(f"Successfully stopped and removed the container: {server_name}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to stop the container {server_name}: {e}")

                self.running_servers[server_name] = False

        self.server_process = None

    def _is_container_running(self, container_name: str) -> bool:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={container_name}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return container_name in result.stdout.split()
        except subprocess.CalledProcessError:
            return False

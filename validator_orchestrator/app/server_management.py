import os
import subprocess
from time import sleep
import httpx
from typing import Dict, Any
import asyncio
from loguru import logger
from app.config import checking_server_configs, get_checking_server_config
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
        self.running_servers = {checking_server_config.name: False for checking_server_config in checking_server_configs}

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
        server_name: str = "localhost",
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
                    logger.info("Pinging " + f"http://{server_name}:{port}")
                    response = await client.get(f"http://{server_name}:{port}")
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

    async def load_model(self, load_model_config: Dict[str, Any], server_name) -> None:
        """
        Load a new model configuration
        """
        try:
            logger.debug(f"Loading model with config: {load_model_config}")
            async with httpx.AsyncClient(timeout=1200) as client:
                response = await client.post(
                    url=f"http://{server_name}:{AI_SERVER_PORT}/load_model",
                    json=load_model_config,
                )
            return response
        except httpx.HTTPError:
            raise Exception("Timeout when loading model :(")

    async def start_server(self, server_type: ServerType):
        """
        Start a server with the given name.
        """
        server_config = get_checking_server_config(server_type)


        if server_config is None:
            logger.error(f"Server {server_type.value} not found in the server config")
            return

        logger.info(f"Starting server: {server_config.name}. First checking if anything is running on {server_config.port}...")
        desired_server_is_online, response_content = await self.is_server_healthy(
            port=server_config.port,
            sleep_time=1,
            total_attempts=3,
            server_name=server_config.name,
        )
        # LLM server returns "LLM" in the response, Image returns an empty string but still a 200...
        self.running_servers[server_config.name] = desired_server_is_online

        logger.debug(f"Desired server: {server_config.name}. Is running: {desired_server_is_online}.")

        if  not desired_server_is_online:
            # Check no other server is running on the same port
            logger.info(f"Running servers: {self.running_servers}. Killing anything on port {server_config.port}...")
            self._kill_process_on_port(server_config.port)
            subprocess.Popen(f"docker rm -f {server_config.name}", shell=True).wait()
            for server in self.running_servers:
                self.running_servers[server] = False
        elif some_server_is_online and desired_server_is_running:
            logger.info(f"Running servers: {self.running_servers}. This is correct, so doing nothing...")
            return
        
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
            server_name=server_config.name,
        )
        if not server_is_up:
            raise Exception(f"Timeout when starting server {server_config.name}")

        self.running_servers[server_config.name] = True

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

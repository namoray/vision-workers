import os
import constants as cst
import json
import utils.api_gate as api_gate
from loguru import logger

# Warmup script to run all workflows once in order to cache the models in VRAM
logger.info("Warming up...")

directory = cst.WARMUP_WORKFLOWS_DIR
for filename in os.listdir(directory):
    if filename.endswith(".json"):
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as file:
            try:
                payload = json.load(file)
                image = api_gate.generate(payload)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {filename}: {e}")

logger.info("Warmup Completed")

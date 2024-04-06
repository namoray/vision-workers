import os
import constants as cst
import json
import utils.api_gate as api_gate

# Warmup script to run all workflows once in order to cache the models in VRAM
print("Warming up...")

directory = cst.WARMUP_WORKFLOWS_DIR
for filename in os.listdir(directory):
    if filename.endswith(".json"):
        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as file:
            try:
                payload = json.load(file)
                image = api_gate.generate(payload)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")

print("Warmup Completed")

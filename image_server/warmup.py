import os
import constants as cst
import json
import utils.api_gate as api_gate
import argparse

# Warmup script to run all workflows once in order to cache the models in VRAM
print("Warming up...")

parser = argparse.ArgumentParser(description='Args for highvram or normalvram')
parser.add_argument('--highvram', action='store_true', help='Enable high VRAM mode')
args = parser.parse_args()

directory = cst.WARMUP_WORKFLOWS_DIR

if args.highvram:
        with open(f"{directory}/highvram/warmup.json", "r") as file:
                try:
                    payload = json.load(file)
                    image = api_gate.generate(payload)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {filename}: {e}")
else:
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

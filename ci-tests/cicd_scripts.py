import sys
import time
import requests
import json

def create_instance(api_key, instance_name, gpu_type, docker_image, port):
    url = "https://runpod-manager.onrender.com/create-instance"
    headers = {
        "Content-Type": "application/json",
        "API_KEY": api_key
    }
    data = {
        "instance_name": instance_name,
        "gpu_type": gpu_type,
        "disk_volume": 500,
        "docker_image": docker_image,
        "ports": f"{port}/http",
        "cuda_versions": ["11.8", "12.0", "12.1", "12.2", "12.3", "12.4"],
        "env_vars": {}
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to create instance. Error: {e}")
        sys.exit(1)
    
    response_json = response.json()
    instance_id = response_json.get('id')

    if not instance_id:
        print(f"Failed to create instance. Response: {response_json}")
        sys.exit(1)

    return instance_id

def check_instance_status(instance_id, port):
    url = f"https://{instance_id}-{port}.proxy.runpod.net/docs"
    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return "RUNNING"
    except Exception as e:
        print(f"Failed to check instance status. Error: {e}")
        return "IDLE"

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python ci-tests/cicd_scripts.py <API_KEY> <INSTANCE_NAME> <GPU_TYPE> <DOCKER_IMAGE> <PORT>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    instance_name = sys.argv[2]
    gpu_type = sys.argv[3]
    docker_image = sys.argv[4]
    port = sys.argv[5]

    instance_id = create_instance(api_key, instance_name, gpu_type, docker_image, port)
    print(f"Instance ID: {instance_id}")

    for _ in range(180):
        status = check_instance_status(instance_id, port.split('/')[0])
        if status == "RUNNING":
            print(instance_id)
            sys.exit(0)
        time.sleep(10)
    
    print(f"Instance did not reach RUNNING status within the expected time.")
    sys.exit(1)
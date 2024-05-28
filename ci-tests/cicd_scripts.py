import sys
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
        "cuda_versions": ["11.8", "12.0", "12.1", "12.2", "12.3"],
        "env_vars": {}
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Failed to create instance. HTTP Code: {response.status_code}, Response: {response.text}")
        sys.exit(1)
    
    try:
        response_json = response.json()
        instance_id = response_json.get('id')
        desired_status = response_json.get('desiredStatus')
    except:
        print(f"Failed to create instance. Response: {response_json}")
        sys.exit(1)

    if not instance_id or desired_status != "RUNNING":
        print(f"Failed to create instance. Response: {response_json}")
        sys.exit(1)

    return instance_id

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
    print(instance_id)
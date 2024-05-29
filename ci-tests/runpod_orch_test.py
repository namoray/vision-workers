import sys
import time
import requests

def runpod_orch_test_llm(instance_id, orch_port, test_json_file):
    url = f"https://{instance_id}-{orch_port}.proxy.runpod.net/check-result"
    headers = {
        "Content-Type": "application/json"
    }

    with open(test_json_file, 'rb') as f:
        data = f.read()

    attempt = 0
    max_attempts = 15
    success = False
    response_body = ""

    while attempt < max_attempts:
        print(f"Attempt: {attempt + 1}")
        try:
            response = requests.post(url, headers=headers, data=data)
            http_code = response.status_code
            response_body = response.text
            print(f"Response Status Code: {http_code}")
            print(f"Response Body: {response_body}")

            if http_code == 200:
                success = True
                break
        except requests.RequestException as e:
            print(f"Request failed: {e}")

        print(f"Retrying in {attempt * 2 + 1} seconds...")
        time.sleep(attempt * 2 + 1)
        attempt += 1

    if not success:
        print(f"Request failed after {max_attempts} attempts.")
        sys.exit(1)

    print("Request succeeded.")
    print(f"::set-output name=response::{response_body}")

def test_runpod_orch_image(instance_id, orch_port, test_json_file):
    url = f"https://{instance_id}-{orch_port}.proxy.runpod.net/check-result"
    headers = {
        "Content-Type": "application/json"
    }

    with open(test_json_file, 'rb') as f:
        data = f.read()

    attempt = 0
    max_attempts = 10
    success = False
    response_body = ""

    while attempt < max_attempts:
        print(f"Attempt: {attempt + 1}")
        try:
            response = requests.post(url, headers=headers, data=data, timeout=800)
            http_code = response.status_code
            response_body = response.text
            print(f"Response Status Code: {http_code}")
            print(f"Response Body: {response_body}")

            if http_code == 200:
                success = True
                break
        except requests.RequestException as e:
            print(f"Request failed: {e}")

        print(f"Retrying in {attempt * 2 + 1} seconds...")
        time.sleep(attempt * 2 + 1)
        attempt += 1

    if not success:
        print(f"Request failed after {max_attempts} attempts.")
        sys.exit(1)

    print("Request succeeded.")
    print(f"::set-output name=response::{response_body}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python ci-tests/orchestrator_tests.py <function_name> [args...]")
        sys.exit(1)

    function_name = sys.argv[1]

    if function_name == "runpod_orch_test_llm":
        if len(sys.argv) != 5:
            print("Usage: python ci-tests/orchestrator_tests.py runpod_orch_test_llm <INSTANCE_ID> <ORCH_PORT> <TEST_JSON_FILE>")
            sys.exit(1)
        instance_id = sys.argv[2]
        orch_port = sys.argv[3]
        test_json_file = sys.argv[4]
        runpod_orch_test_llm(instance_id, orch_port, test_json_file)
    elif function_name == "test_runpod_orch_image":
        if len(sys.argv) != 5:
            print("Usage: python ci-tests/orchestrator_tests.py test_runpod_orch_image <INSTANCE_ID> <ORCH_PORT> <TEST_JSON_FILE>")
            sys.exit(1)
        instance_id = sys.argv[2]
        orch_port = sys.argv[3]
        test_json_file = sys.argv[4]
        test_runpod_orch_image(instance_id, orch_port, test_json_file)
    else:
        print(f"Unknown function name: {function_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()
import sys
import time
import requests

def load_model(instance_id, llm_port, test_json_file):
    url = f"https://{instance_id}-{llm_port}.proxy.runpod.net/load_model"
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
            response = requests.post(url, headers=headers, data=data, timeout=500)
            http_code = response.status_code
            response_body = response.text
            print(f"Response Status Code: {http_code}")
            print(f"Response Body: {response_body}")

            if http_code == 200:
                success = True
                break
        except Exception as e:
            print(f"Request failed: {e}")

        time.sleep(10)
        attempt += 1

    if not success:
        print(f"Request failed after {max_attempts} attempts.")
        sys.exit(1)

    print("Request succeeded.")
    print(f"::set-output name=response::{response_body}")

def test_llm(instance_id, llm_port, test_json_file):
    url = f"https://{instance_id}-{llm_port}.proxy.runpod.net/generate_text"
    headers = {
        "Content-Type": "application/json"
    }

    with open(test_json_file, 'rb') as f:
        data = f.read()

    attempt = 0
    max_attempts = 9
    success = False
    response_body = ""

    while attempt < max_attempts:
        print(f"Attempt: {attempt + 1}")
        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            http_code = response.status_code
            response_body = response.text
            print(f"Response Status Code: {http_code}")
            print(f"Response Body: {response_body}")

            if http_code == 200:
                success = True
                break
        except requests.RequestException as e:
            print(f"Request failed: {e}")

        time.sleep(10)
        attempt += 1

    if not success:
        print(f"Request failed after {max_attempts} attempts.")
        sys.exit(1)

    print("Request succeeded.")
    print(f"::set-output name=response::{response_body}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python ci-tests/llm_tests.py <function_name> [args...]")
        sys.exit(1)

    function_name = sys.argv[1]

    if function_name == "load_model":
        if len(sys.argv) != 5:
            print("Usage: python ci-tests/llm_tests.py load_model <INSTANCE_ID> <LLM_PORT> <TEST_JSON_FILE>")
            sys.exit(1)
        instance_id = sys.argv[2]
        llm_port = sys.argv[3]
        test_json_file = sys.argv[4]
        load_model(instance_id, llm_port, test_json_file)
    elif function_name == "test_llm":
        if len(sys.argv) != 5:
            print("Usage: python ci-tests/llm_tests.py test_llm <INSTANCE_ID> <LLM_PORT> <TEST_JSON_FILE>")
            sys.exit(1)
        instance_id = sys.argv[2]
        llm_port = sys.argv[3]
        test_json_file = sys.argv[4]
        test_llm(instance_id, llm_port, test_json_file)
    else:
        print(f"Unknown function name: {function_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()
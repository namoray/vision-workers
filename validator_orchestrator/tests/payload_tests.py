import asyncio
import requests
from sample_payloads import SAMPLE_CHAT_8B


async def test_payload() -> None:
    payload = SAMPLE_CHAT_8B
    ping_it = requests.post("http://localhost:6920/check-result", json=payload)

if __name__ == "__main__":
    asyncio.run(test_payload())
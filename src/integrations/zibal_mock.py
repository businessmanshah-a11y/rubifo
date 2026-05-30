from uuid import uuid4
from urllib.parse import quote
from typing import Tuple


class ZibalMockGateway:
    """Local Zibal-compatible payment simulator for checkout QA."""

    provider = "zibal_mock"

    def __init__(self, web_base_url: str):
        self.web_base_url = web_base_url.rstrip("/")

    async def request_payment(
        self, amount: int, description: str, callback_url: str = None
    ) -> Tuple[bool, dict]:
        if amount <= 0:
            return False, {"message": "Invalid amount"}

        track_id = f"RUBIFO-{uuid4().hex[:12].upper()}"
        return True, {
            "track_id": track_id,
            "payment_url": f"{self.web_base_url}/mock/zibal/start/{quote(track_id)}",
            "provider": self.provider,
        }

    async def verify_payment(self, track_id: str, amount: int, success: str) -> Tuple[bool, str]:
        if success == "1":
            return True, f"MOCK-ZIBAL-{track_id}"
        return False, "Mock Zibal payment was not successful"


def create_zibal_mock_gateway(web_base_url: str) -> ZibalMockGateway:
    return ZibalMockGateway(web_base_url)

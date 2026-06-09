import aiohttp
from typing import Tuple
from src.logger import logger

ZIBAL_REQUEST_URL = "https://gateway.zibal.ir/v1/request"
ZIBAL_VERIFY_URL = "https://gateway.zibal.ir/v1/verify"
ZIBAL_START_URL = "https://gateway.zibal.ir/start/{track_id}"


class ZibalGateway:
    """Integration with Zibal payment gateway."""

    provider = "zibal"

    def __init__(self, merchant: str):
        self.merchant = merchant
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def request_payment(
        self, amount: int, description: str, callback_url: str = None
    ) -> Tuple[bool, dict]:
        """Request payment from Zibal.

        Returns:
            (True, {"track_id": str, "payment_url": str, "provider": str}) on success
            (False, {"message": str}) on failure
        """
        payload = {
            "merchant": self.merchant,
            "amount": amount,
            "callbackUrl": callback_url or "https://rubifo.ir/payment/callback",
            "description": description,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(ZIBAL_REQUEST_URL, json=payload) as resp:
                    data = await resp.json()
                    result = data.get("result")
                    if result == 100:
                        track_id = str(data["trackId"])
                        payment_url = ZIBAL_START_URL.format(track_id=track_id)
                        logger.info(f"Zibal payment requested: trackId={track_id}, amount={amount}")
                        return True, {
                            "track_id": track_id,
                            "payment_url": payment_url,
                            "provider": self.provider,
                        }
                    logger.error(f"Zibal request error: result={result}, data={data}")
                    return False, {"message": f"Zibal error: {result}"}

        except (aiohttp.ClientError, TimeoutError) as e:
            logger.error(f"Zibal HTTP error: {e}")
            return False, {"message": f"Connection error: {e}"}
        except Exception as e:
            logger.error(f"Zibal request exception: {e}")
            return False, {"message": str(e)}

    async def verify_payment(self, track_id: str, amount: int, success: str = None) -> Tuple[bool, str]:
        """Verify payment with Zibal.

        Args:
            track_id: trackId from Zibal callback
            amount: Expected amount (for logging/validation)
            success: success param from callback query string (unused, Zibal verifies server-side)

        Returns:
            (True, ref_number_str) on success
            (False, error_message) on failure
        """
        payload = {
            "merchant": self.merchant,
            "trackId": int(track_id),
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(ZIBAL_VERIFY_URL, json=payload) as resp:
                    data = await resp.json()
                    result = data.get("result")
                    if result == 100:
                        ref_number = str(data.get("refNumber", track_id))
                        logger.info(f"Zibal payment verified: trackId={track_id}, refNumber={ref_number}")
                        return True, ref_number
                    if result == 201:
                        ref_number = str(data.get("refNumber", track_id))
                        logger.warning(f"Zibal payment already verified: trackId={track_id}")
                        return True, ref_number
                    logger.warning(f"Zibal verify failed: result={result}, trackId={track_id}")
                    return False, f"Zibal verify error: {result}"

        except (aiohttp.ClientError, TimeoutError) as e:
            logger.error(f"Zibal verify HTTP error: {e}")
            return False, f"Connection error: {e}"
        except Exception as e:
            logger.error(f"Zibal verify exception: {e}")
            return False, str(e)


def create_zibal_gateway(merchant: str = None) -> ZibalGateway:
    from src.config import ZIBAL_MERCHANT_ID
    return ZibalGateway(merchant or ZIBAL_MERCHANT_ID)

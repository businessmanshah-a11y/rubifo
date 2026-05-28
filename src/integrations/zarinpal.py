import aiohttp
from typing import Tuple
from src.config import ZARINPAL_MERCHANT_ID
from src.logger import logger


class ZarinpalGateway:
    """Integration with Zarinpal payment gateway."""

    def __init__(self, merchant_id: str, sandbox: bool = True):
        self.merchant_id = merchant_id
        self.sandbox = sandbox
        self.base_url = (
            "https://sandbox.zarinpal.com/pg"
            if sandbox
            else "https://www.zarinpal.com/pg"
        )
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def request_payment(
        self, amount: int, description: str, callback_url: str = None
    ) -> Tuple[bool, str]:
        """Request payment link from Zarinpal.

        Args:
            amount: Amount in Rials
            description: Payment description
            callback_url: Callback URL after payment

        Returns:
            Tuple of (success, payment_url_or_error_message)
        """
        if not callback_url:
            callback_url = "https://rubifo.ir/payment/callback"

        payload = {
            "MerchantID": self.merchant_id,
            "Amount": amount,
            "Description": description,
            "CallbackURL": callback_url,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/rest/WebGate.json", json=payload
                ) as resp:
                    data = await resp.json()

                    status_value = data.get("Status", data.get("result"))
                    if status_value == 100 or status_value == "100":
                        authority = data.get("Authority") or data.get("authority")
                        url = f"{self.base_url}/StartPay/{authority}"
                        logger.info(
                            f"Payment request created: {authority}, amount: {amount}"
                        )
                        return True, url

                    status = data.get("Status", data.get("result"))
                    logger.error(f"Zarinpal error: {status}")
                    return False, f"Payment request failed: {status}"

        except (aiohttp.ClientError, TimeoutError) as e:
            logger.error(f"Zarinpal HTTP error: {e}")
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error(f"Zarinpal request error: {e}")
            return False, str(e)

    async def verify_payment(self, authority: str, amount: int) -> Tuple[bool, str]:
        """Verify payment with Zarinpal.

        Args:
            authority: Authority from payment callback
            amount: Amount in Rials

        Returns:
            Tuple of (success, reference_id_or_error_message)
        """
        payload = {
            "MerchantID": self.merchant_id,
            "Authority": authority,
            "Amount": amount,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/rest/WebGate.json", json=payload
                ) as resp:
                    data = await resp.json()

                    status_value = data.get("Status", data.get("result"))
                    if status_value == 100 or status_value == "100":
                        ref_id = data.get("RefID", data.get("ref_id", ""))
                        logger.info(f"Payment verified: {authority}, RefID: {ref_id}")
                        return True, ref_id

                    status = data.get("Status", data.get("result"))
                    logger.warning(f"Payment verification failed: {status}")
                    return False, f"Verification failed: {status}"

        except (aiohttp.ClientError, TimeoutError) as e:
            logger.error(f"Zarinpal verification HTTP error: {e}")
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            logger.error(f"Zarinpal verification error: {e}")
            return False, str(e)


def create_zarinpal_gateway(sandbox: bool = True) -> ZarinpalGateway:
    """Factory function to create Zarinpal gateway instance.

    Args:
        sandbox: Whether to use sandbox environment

    Returns:
        ZarinpalGateway instance
    """
    return ZarinpalGateway(ZARINPAL_MERCHANT_ID, sandbox)

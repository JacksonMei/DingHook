"""Small wrapper to send messages to DingTalk custom robot"""

import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import logging
import os
from typing import List, Optional

from . import config

logger = logging.getLogger(__name__)
# If set, do not perform network requests and instead log/send success
DISABLE_NETWORK = os.environ.get("DINGBOT_DISABLE_NETWORK")


def _signed_url(access_token: str, secret: str) -> str:
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}"
    return url


def send_text(
    access_token: str,
    secret: str,
    msg: str,
    at_user_ids: Optional[List[str]] = None,
    at_mobiles: Optional[List[str]] = None,
    is_at_all: bool = False,
) -> dict:
    """Send a simple text message to the DingTalk robot."""
    url = _signed_url(access_token, secret)

    body = {
        "at": {
            "isAtAll": bool(is_at_all),
            "atUserIds": at_user_ids or [],
            "atMobiles": at_mobiles or [],
        },
        "text": {"content": msg},
        "msgtype": "text",
    }
    headers = {"Content-Type": "application/json"}
    if DISABLE_NETWORK:
        # Simulate success response when network disabled for local testing
        data = {"errcode": 0, "errmsg": "network disabled (local test)", "simulated": True}
        logger.info("send_text (simulated): %s", data)
        return data

    resp = requests.post(url, json=body, headers=headers, timeout=10)
    try:
        data = resp.json()
    except Exception:
        data = {"status_code": resp.status_code, "text": resp.text}
    logger.info("send_text response: %s", data)
    return data


def send_text_from_env(msg: str, at_user_ids: Optional[List[str]] = None):
    if not config.ACCESS_TOKEN or not config.SECRET:
        raise RuntimeError("ACCESS_TOKEN and SECRET must be set in environment or config")
    return send_text(config.ACCESS_TOKEN, config.SECRET, msg, at_user_ids=at_user_ids)

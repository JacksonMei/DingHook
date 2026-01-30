#!/usr/bin/env python3
"""
钉钉机器人回调服务器
接收钉钉群聊消息并回复
"""

import os
import sys
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json
from flask import Flask, request, jsonify
from typing import Dict, Any

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SECRET = os.getenv("SECRET")
BASE_URL = "https://oapi.dingtalk.com/robot/send"

app = Flask(__name__)


# 添加请求日志中间件
@app.before_request
def log_request():
    print(f"=== 收到请求 ===")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"方法: {request.method}")
    print(f"路径: {request.path}")
    print(f"来源IP: {request.remote_addr}")
    print(f"Headers: {dict(request.headers)}")
    if request.method == "POST":
        print(f"Body: {request.get_data(as_text=True)}")
    print(f"================\n")
    sys.stdout.flush()


def generate_sign(secret: str) -> tuple:
    """生成签名和时间戳"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_dingtalk(message: str, title: str = None) -> bool:
    """发送钉钉消息"""
    timestamp, sign = generate_sign(SECRET)
    url = f"{BASE_URL}?access_token={ACCESS_TOKEN}&timestamp={timestamp}&sign={sign}"

    if title:
        # Markdown 格式
        body = {"msgtype": "markdown", "markdown": {"title": title, "text": message}}
    else:
        # 文本格式
        body = {"msgtype": "text", "text": {"content": message}}

    try:
        resp = requests.post(
            url, json=body, headers={"Content-Type": "application/json"}, timeout=10
        )
        result = resp.json()
        return result.get("errcode") == 0
    except Exception as e:
        print(f"发送失败: {e}", file=sys.stderr)
        return False


def verify_signature(timestamp: str, sign: str) -> bool:
    """验证钉钉回调签名"""
    string_to_sign = f"{timestamp}\n{SECRET}"
    hmac_code = hmac.new(
        SECRET.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    expected_sign = base64.b64encode(hmac_code).decode("utf-8")
    return expected_sign == sign


def process_message(content: str, sender_name: str) -> str:
    """处理接收到的消息并生成回复"""
    # 简单的回复逻辑，你可以在这里集成 Claude API 或其他 AI 服务
    content = content.strip()

    if content.startswith("/help"):
        return "可用命令:\n/help - 显示帮助\n/ping - 测试机器人\n/time - 获取当前时间"

    elif content.startswith("/ping"):
        return "pong! 机器人运行正常 ✅"

    elif content.startswith("/time"):
        from datetime import datetime

        return f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    else:
        # 默认回复 - 这里可以接入 Claude API
        return f"收到来自 {sender_name} 的消息: {content}\n\n(这里可以接入 AI 对话功能)"


@app.route("/", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "message": "DingTalk Bot Server is running"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """处理钉钉回调"""
    try:
        # 获取请求数据
        data = request.json
        print(f"收到钉钉回调: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # 验证签名 (如果钉钉发送了签名)
        timestamp = request.headers.get("timestamp")
        sign = request.headers.get("sign")
        # if timestamp and sign:
        #     if not verify_signature(timestamp, sign):
        #         print("签名验证失败")
        #         return jsonify({"errcode": 1, "errmsg": "Invalid signature"}), 403

        # 处理不同类型的消息
        msg_type = data.get("msgtype")

        if msg_type == "text":
            # 文本消息
            content = data.get("text", {}).get("content", "")
            sender_name = data.get("senderNick", "Unknown")

            # 生成回复
            reply = process_message(content, sender_name)

            # 发送回复
            if reply:
                success = send_dingtalk(reply)
                if success:
                    print(f"回复成功: {reply}")
                else:
                    print(f"回复失败")

        return jsonify({"errcode": 0, "errmsg": "ok"})

    except Exception as e:
        print(f"处理回调失败: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"errcode": 1, "errmsg": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"钉钉机器人服务器启动在端口 {port}")
    print(f"Webhook URL: http://0.0.0.0:{port}/webhook")
    app.run(host="0.0.0.0", port=port, debug=True)
    # NOTE: Do NOT store real tokens or secrets in the repository.
    # Example webhook URL (redacted): https://oapi.dingtalk.com/robot/send?access_token=REDACTED
    # If secrets are accidentally committed, revoke/rotate them immediately and remove them from Git history.

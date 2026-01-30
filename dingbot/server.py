"""Webhook server for DingTalk robot messages.

Supports mini-commands:
- /remember <interval_seconds> <text>  -> saves a periodic memory for the sender
- /forget <id>                         -> deletes a memory by id
- /memories                            -> list sender's memories
- /help /ping /time                    -> basic utility

On ordinary messages, the server forwards the message + recent memories to the `agent` which returns
a JSON-style response {"reply": <text>, optional "save_memory": {...}}.
Replies to incoming messages will @ the sender when sender id is available.
"""

import time
import json
import logging
from flask import Flask, request, jsonify

from . import sender, agent, memory, config, scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def init_app(start_scheduler: bool = True):
    """Initialize DB and optionally start the background scheduler."""
    memory.init_db()
    if start_scheduler:
        scheduler.start()



@app.before_request
def log_request():
    logger.info("Received request: %s %s from %s", request.method, request.path, request.remote_addr)


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "DingBot Server is running"})


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json or {}
        logger.info("Webhook payload: %s", json.dumps(data, ensure_ascii=False))

        msg_type = data.get("msgtype")
        if msg_type != "text":
            return jsonify({"errcode": 0, "errmsg": "ignored non-text"})

        content = data.get("text", {}).get("content", "").strip()
        sender_name = data.get("senderNick") or data.get("senderName") or "Unknown"
        # attempt to find an ID to @
        sender_id = data.get("senderId") or data.get("senderStaffId") or data.get("userid")

        # commands
        if content.startswith("/help"):
            reply = "可用命令:\n/remember <interval_seconds> <text> - 保存记忆并按周期推送\n/forget <id> - 删除记忆\n/memories - 列出你的记忆\n/ping - 测试机器人\n/time - 获取当前时间"
            if sender_id:
                sender.send_text_from_env(reply, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(reply)
            return jsonify({"errcode": 0, "errmsg": "ok"})

        if content.startswith("/ping"):
            reply = "pong! 机器人运行正常 ✅"
            if sender_id:
                sender.send_text_from_env(reply, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(reply)
            return jsonify({"errcode": 0, "errmsg": "ok"})

        if content.startswith("/time"):
            from datetime import datetime

            reply = f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            if sender_id:
                sender.send_text_from_env(reply, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(reply)
            return jsonify({"errcode": 0, "errmsg": "ok"})

        if content.startswith("/remember"):
            parts = content.split(maxsplit=2)
            if len(parts) < 3:
                err = "用法: /remember <interval_seconds> <text>"
                if sender_id:
                    sender.send_text_from_env(err, at_user_ids=[sender_id])
                else:
                    sender.send_text_from_env(err)
                return jsonify({"errcode": 1, "errmsg": "bad request"}), 400
            try:
                interval = int(parts[1])
            except ValueError:
                err = "interval_seconds 必须为整数（秒）"
                if sender_id:
                    sender.send_text_from_env(err, at_user_ids=[sender_id])
                else:
                    sender.send_text_from_env(err)
                return jsonify({"errcode": 1, "errmsg": "bad interval"}), 400
            text_to_remember = parts[2]
            uid = sender_id or sender_name
            mem_id = memory.add_memory(uid, text_to_remember, interval)
            reply = f"已记录记忆 id={mem_id}, 每 {interval} 秒推送一次。"
            if sender_id:
                sender.send_text_from_env(reply, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(reply)
            return jsonify({"errcode": 0, "errmsg": "ok"})

        if content.startswith("/forget"):
            parts = content.split(maxsplit=1)
            if len(parts) < 2:
                err = "用法: /forget <id>"
                if sender_id:
                    sender.send_text_from_env(err, at_user_ids=[sender_id])
                else:
                    sender.send_text_from_env(err)
                return jsonify({"errcode": 1, "errmsg": "bad request"}), 400
            try:
                mid = int(parts[1])
                memory.delete_memory(mid)
                reply = f"已删除记忆 id={mid}"
            except Exception:
                reply = "指定 id 无效或不存在"
            if sender_id:
                sender.send_text_from_env(reply, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(reply)
            return jsonify({"errcode": 0, "errmsg": "ok"})

        if content.startswith("/memories"):
            uid = sender_id or sender_name
            mems = memory.list_user_memories(uid)
            if not mems:
                txt = "你没有记忆。使用 /remember 添加一个。"
            else:
                lines = [f"id={m['id']} interval={m['interval']}s: {m['content']}" for m in mems]
                txt = "\n".join(lines)
            if sender_id:
                sender.send_text_from_env(txt, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(txt)
            return jsonify({"errcode": 0, "errmsg": "ok"})

        # 普通消息：记录到本地文件并转发给 agent
        from .memory_file import append_user_message
        from flask import Response
        append_user_message(sender_id or sender_name, content)
        result = agent.analyze_and_reply(content, sender_name, user_id=sender_id or sender_name)
        reply = result.get("reply") or "抱歉，未能生成回复。"
        # 发送给钉钉会话（@ sender when available)；错误不应阻断对调用方的响应
        try:
            if sender_id:
                sender.send_text_from_env(reply, at_user_ids=[sender_id])
            else:
                sender.send_text_from_env(reply)
        except Exception:
            logger.exception("Failed to send message via sender; will still return reply to webhook caller")
        # 返回纯文本回复给 webhook 调用方（不要返回 JSON）
        return Response(reply, mimetype='text/plain')

    except Exception as exc:
        logger.exception("Failed to process webhook: %s", exc)
        return jsonify({"errcode": 1, "errmsg": str(exc)}), 500


if __name__ == "__main__":
    # initialize DB and start scheduler
    init_app(start_scheduler=True)

    port = int(__import__("os").environ.get("PORT", 8080))
    logger.info("Starting DingBot server on port %s", port)
    # Run without the auto-reloader to ensure environment variables are stable in this process
    app.run(host="0.0.0.0", port=port, debug=False)

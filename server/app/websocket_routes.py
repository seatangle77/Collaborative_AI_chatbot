from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import supabase_client
from app.ai_provider import generate_response  # ✅ 统一管理 AI API 提供商
import json
import asyncio

websocket_router = APIRouter()

# 存储 WebSocket 连接
connected_clients = {}

# 记录消息计数
message_count = {}
last_ai_summary = {}  # 记录上次 AI 生成的总结

@websocket_router.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str):
    """WebSocket 连接管理"""
    await websocket.accept()
    
    if group_id not in connected_clients:
        connected_clients[group_id] = []
        message_count[group_id] = 0
        last_ai_summary[group_id] = None  

    connected_clients[group_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 收到 WebSocket 数据: {data}")  # ✅ 添加日志，查看原始数据

            received_data = json.loads(data)

            # ✅ 处理前端触发 AI 总结请求
            if received_data.get("type") == "trigger_ai_summary":
                ai_provider = received_data.get("aiProvider", "xai")  # ✅ 确保解析 aiProvider
                print(f"🚀 触发 AI 总结: group_id={group_id}, 使用 API: {ai_provider}")

                if not ai_provider:  # ✅ 变量名修正
                    print("❌ 错误: AI 提供商 (`ai_provider`) 为空，无法生成总结")
                    return

                print(f"🚀 触发 AI 总结: group_id={group_id}，使用 API: {ai_provider}")
                await push_ai_summary(group_id, ai_provider)
                message_count[group_id] = 0  
                continue  

            # ✅ 处理常规聊天消息
            await push_chat_message(group_id, received_data)

            message_count[group_id] += 1  
            print(f"📩 WebSocket 收到消息: {data} (group {group_id} - 计数 {message_count[group_id]})")

            # ✅ **每 3 条消息触发 AI 生成**
            if message_count[group_id] >= 3:
                api_provider = os.getenv("DEFAULT_AI_PROVIDER", "xai")  # ✅ 默认值改为 `.env`
                print(f"🚀 触发 AI 实时总结: group_id={group_id}，使用 API: {api_provider}")
                await push_ai_summary(group_id, api_provider)
                message_count[group_id] = 0  # ✅ 计数归零

    except WebSocketDisconnect:
        connected_clients[group_id].remove(websocket)
        if len(connected_clients[group_id]) == 0:
            del connected_clients[group_id]


# ✅ **推送聊天消息**
async def push_chat_message(group_id, message):
    """仅推送 WebSocket，不存入数据库"""

    if not message or "message" not in message or not message["message"].strip():
        print(f"⚠️ 跳过空消息: {message}")
        return

    chat_message_entry = {
        "group_id": group_id,
        "user_id": message.get("user_id"),
        "message": message.get("message"),
        "role": message.get("role", "user"),
        "created_at": message.get("created_at"),  # ✅ 使用 routes.py 的入库时间
        "message_type": message.get("message_type", "text"),
        "sender_type": message.get("sender_type", "user"),
        "chatbot_id": message.get("chatbot_id"),
        "speaking_duration": message.get("speaking_duration", 0),
        "session_id": message.get("session_id")
    }

    # ✅ **仅推送 WebSocket，不再存数据库**
    if group_id in connected_clients:
        message_payload = json.dumps({"type": "message", "message": chat_message_entry})
        for client in connected_clients[group_id]:
            await client.send_text(message_payload)

    print(f"📤 聊天消息已通过 WebSocket 发送: {chat_message_entry}")


# ✅ **推送 AI 会议总结**
async def push_ai_summary(group_id: str, api_provider: str):
    """触发 AI 生成会议总结，使用前端指定的 AI 提供商"""
    if not api_provider:
        print("❌ `api_provider` 为空，无法生成 AI 总结")
        return

    print(f"🚀 生成 AI 总结: group_id={group_id}，使用 API: {api_provider}")

    # ✅ 获取当前 session
    session = (
        supabase_client.table("chat_sessions")
        .select("id")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if not session:
        print("❌ 没有找到当前活跃 session")
        return
    session_id = session[0]["id"]

    # ✅ 获取最近 10 条聊天记录
    chat_history = (
        supabase_client.table("chat_messages")
        .select("id, user_id, message")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
        .data
    )

    if not chat_history:
        print("❌ 没有找到聊天记录")
        return

    print(f"📖 获取到最近 {len(chat_history)} 条聊天记录")

    conversation = "\n".join([msg["message"] for msg in chat_history])
    previous_summary = last_ai_summary.get(group_id, "")

    ai_prompt = f"历史总结:\n{previous_summary}\n\n最新聊天:\n{conversation}"
    
    ai_response = generate_response(ai_prompt, "real_time_summary", "default", api_provider)

    if not ai_response or ai_response.strip() == "":
        print("❌ AI 生成失败，跳过入库")
        return

    print(f"🤖 AI 会议总结生成成功: {ai_response}")

    last_ai_summary[group_id] = ai_response

    summary_entry = {
        "group_id": group_id,
        "session_id": session_id,
        "summary_text": ai_response,
        "summary_time": "now()",
    }

    supabase_client.table("chat_summaries").insert(summary_entry).execute()

    if group_id in connected_clients:
        summary_payload = json.dumps({
            "type": "ai_summary",
            "summary_text": ai_response,
            "api_provider": api_provider  # ✅ 返回使用的 AI 供应商
        })
        for client in connected_clients[group_id]:
            await client.send_text(summary_payload)

    print(f"📤 AI 会议总结已通过 WebSocket 发送: {ai_response}")
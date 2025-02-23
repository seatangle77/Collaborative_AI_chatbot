from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import supabase_client
from app.xai_api import generate_ai_response  # ✅ AI 生成工具
import json
import uuid

websocket_router = APIRouter()

# 存储连接的客户端，每个 group_id 对应一组 WebSocket 客户端
connected_clients = {}

@websocket_router.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str):
    await websocket.accept()
    if group_id not in connected_clients:
        connected_clients[group_id] = []
    connected_clients[group_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"收到 WebSocket 消息: {data}")

            # 广播消息给所有连接的客户端
            for client in connected_clients[group_id]:
                await client.send_text(data)

    except WebSocketDisconnect:
        connected_clients[group_id].remove(websocket)
        if len(connected_clients[group_id]) == 0:
            del connected_clients[group_id]

# 推送聊天消息
async def push_chat_message(group_id, message):
    if not message or "message" not in message or not message["message"].strip():
        print(f"⚠️ 跳过发送空消息: {message}")
        return

    # 🔹 确保 message 是对象，而不是数组
    if isinstance(message, list):  
        message = message[0]  # 取出列表中的第一个对象

    if group_id in connected_clients:
        message_payload = json.dumps({"type": "message", "message": message}, default=str)
        for client in connected_clients[group_id]:
            await client.send_text(message_payload)

    # ✅ **在用户发送消息后，调用 AI 见解生成**
    print(f"🚀 触发 AI 见解生成: group_id={group_id}")
    await push_ai_insights(group_id)  # 这里调用 AI 见解生成

# 推送议程数据更新
async def push_agenda_update(group_id, agenda_data):
    if group_id in connected_clients:
        agenda_payload = json.dumps({"agenda": agenda_data}, default=str)
        for client in connected_clients[group_id]:
            await client.send_text(agenda_payload)

# 推送 AI 分析结果
async def push_ai_analysis_update(group_id, analysis_data):
    if group_id in connected_clients:
        analysis_payload = json.dumps({"ai_analysis": analysis_data}, default=str)
        for client in connected_clients[group_id]:
            await client.send_text(analysis_payload)

# 推送讨论术语数据更新
async def push_discussion_terms_update(group_id, terms_data):
    if group_id in connected_clients:
        terms_payload = json.dumps({"discussion_terms": terms_data}, default=str)
        for client in connected_clients[group_id]:
            await client.send_text(terms_payload)


# ✅ **自动生成 AI 见解，并推送 WebSocket**
async def push_ai_insights(group_id):
    print(f"🚀 push 开始生成 AI 见解: group_id={group_id}")

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
    prompt = f"以下是小组讨论内容，请总结关键讨论点，并提出见解:\n{conversation}"

    # ✅ **调用 AI 生成接口**
    print(f"🧠 发送 Prompt 到 AI: {prompt}")
    ai_response = generate_ai_response(prompt)

    if not ai_response or ai_response.strip() == "":
        print("❌ AI 生成失败，跳过入库")
        return

    print(f"🤖 AI 见解生成成功: {ai_response}")

    message_id = chat_history[0]["id"]
    user_id = chat_history[0]["user_id"]

    # ✅ **检查 message_id 是否为 UUID，如果数据库是整数，则改为 None**
    if isinstance(message_id, str) and "-" in message_id:
        print(f"⚠️ message_id 是 UUID ({message_id})，数据库要求 INTEGER，存 NULL")
        message_id = None  # 或者 message_id = 0

    insight_entry = {
        #"id": None,  # `id` 是 `integer`，数据库应自动生成
        "group_id": group_id,
        "user_id": user_id,
        "message_id": message_id,  # ✅ 确保 message_id 格式正确
        "insight_text": ai_response,
        "created_at": "now()",
    }

    print(f"😩开始插入数据库: {ai_response}")

    # ✅ **尝试插入数据库**
    try:
        response = supabase_client.table("discussion_insights").insert(insight_entry).execute()
        print(f"✅ AI 见解已存入数据库: {response}")
    except Exception as e:
        print(f"❌ AI 见解入库失败: {e}")

    # 通过 WebSocket 发送 AI 见解
    if group_id in connected_clients:
        insight_payload = json.dumps({"type": "ai_insight", "insight_text": ai_response})
        for client in connected_clients[group_id]:
            await client.send_text(insight_payload)
    
    print(f"📤 AI 见解已通过 WebSocket 发送: {ai_response}")
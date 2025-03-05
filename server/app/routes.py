import os
import requests
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.database import supabase_client
from app.websocket_routes import (
    push_chat_message, 
    push_ai_summary  # ✅ 确保 WebSocket 触发 AI 会议总结
)

load_dotenv()

router = APIRouter()


# ========== 📌 用户管理 API ==========
@router.get("/api/users/")
async def get_users():
    return supabase_client.table("users").select("*").execute().data

@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    return supabase_client.table("users").select("*").eq("user_id", user_id).execute().data

# ========== 📌 小组管理 API ==========
@router.get("/api/groups/")
async def get_groups():
    return supabase_client.table("groups").select("*").execute().data

@router.get("/api/groups/{group_id}")
async def get_group(group_id: str):
    return supabase_client.table("groups").select("*").eq("id", group_id).execute().data

@router.get("/api/groups/{group_id}/members")
async def get_group_members(group_id: str):
    return supabase_client.table("group_memberships").select("*").eq("group_id", group_id).execute().data


# ========== 📌 AI 机器人管理 API ==========

@router.get("/api/ai_bots/")
async def get_ai_bots():
    """
    获取所有 AI 机器人信息
    """
    return supabase_client.table("ai_bots").select("*").execute().data

@router.get("/api/ai_bots/{bot_id}")
async def get_ai_bot(bot_id: str):
    """
    根据 AI 机器人 ID 获取具体的机器人信息
    """
    return supabase_client.table("ai_bots").select("*").eq("id", bot_id).execute().data

@router.get("/api/ai_bots/group/{group_id}")
async def get_ai_bots_by_group(group_id: str):
    """
    获取特定小组的 AI 机器人
    """
    return supabase_client.table("ai_bots").select("*").eq("group_id", group_id).execute().data

@router.get("/api/ai_bots/user/{user_id}")
async def get_ai_bots_by_user(user_id: str):
    """
    获取属于特定用户的 AI 机器人
    """
    return supabase_client.table("ai_bots").select("*").eq("user_id", user_id).execute().data

# ========== 📌 聊天 API ==========
@router.get("/api/chat/{group_id}")
async def get_chat_history(group_id: str):
    return (
        supabase_client.table("chat_messages")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

class ChatMessage(BaseModel):
    group_id: str
    user_id: Optional[str] = None
    chatbot_id: Optional[str] = None
    message: str
    role: str = Field(default="user")
    message_type: str = Field(default="text")
    sender_type: str = Field(default="user")
    speaking_duration: Optional[int] = 0
    session_id: Optional[str] = None

# ========== 📌 发送聊天消息 ==========

@router.post("/api/chat/send")
async def send_chat_message(payload: ChatMessage):
    """
    发送聊天消息，同时存入数据库并通过 WebSocket 推送
    """
    data = payload.dict()

    # ✅ **插入数据库**
    inserted_data = supabase_client.table("chat_messages").insert(data).execute().data

    if inserted_data:
        await push_chat_message(payload.group_id, inserted_data[0])  # ✅ WebSocket 推送消息

    return inserted_data

# ========== 📌 讨论会话 API ==========

@router.get("/api/sessions/{group_id}")
async def get_current_session(group_id: str):
    """
    获取指定小组的当前活跃 Session

    参数:
        - group_id (str): 讨论组 ID

    返回:
        - 该小组最新的 session 信息（如果有）
    """
    sessions = (
        supabase_client.table("chat_sessions")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)  # ✅ 语法一致性
        .limit(1)  # 只获取最新的 session
        .execute()
        .data
    )

    if not sessions:
        raise HTTPException(status_code=404, detail="未找到该小组的活跃 session")

    return sessions[0]

# ========== 📌 聊天议程 API ==========

@router.get("/api/chat/agenda/session/{session_id}")
async def get_agenda_by_session(session_id: str):
    """
    获取指定 session 关联的所有议程 (chat_agendas)

    参数:
        - session_id (str): 讨论会话 ID

    返回:
        - 该 session 相关的议程列表
    """
    agendas = (
        supabase_client.table("chat_agendas")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")  # ✅ 这里默认就是升序，不需要 `asc=True`
        .execute()
        .data
    )

    if not agendas:
        raise HTTPException(status_code=404, detail="未找到该 session 相关的议程")

    return agendas

# ========== 📌 AI 会议总结 API ==========
@router.get("/api/chat_summaries/{group_id}")
async def get_chat_summaries(group_id: str):
    """
    获取指定小组的 AI 会议总结
    """
    return (
        supabase_client.table("chat_summaries")
        .select("*")
        .eq("group_id", group_id)
        .order("summary_time", desc=True)
        .execute()
        .data
    )

@router.post("/api/chat_summaries/{group_id}")
async def trigger_ai_summary(group_id: str):
    """
    手动触发 AI 会议总结
    """
    await push_ai_summary(group_id)
    return {"message": "AI 会议总结已触发"}

@router.get("/api/chat_summaries/session/{session_id}")
async def get_chat_summaries_by_session(session_id: str):
    """
    获取特定 session 的 AI 总结
    """
    summaries = (
        supabase_client.table("chat_summaries")
        .select("*")
        .eq("session_id", session_id)
        .order("summary_time", desc=True)
        .execute()
        .data
    )

    if not summaries:
        return JSONResponse(
            content=[], 
            status_code=200, 
            headers={"Access-Control-Allow-Origin": "*"}  # ✅ 允许跨域
        )

    return JSONResponse(
        content=summaries, 
        status_code=200, 
        headers={"Access-Control-Allow-Origin": "*"}  # ✅ 允许跨域
    )
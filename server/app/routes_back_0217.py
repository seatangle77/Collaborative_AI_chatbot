import os
import requests
from pydantic import BaseModel
from dotenv import load_dotenv  # 读取 .env 文件
from fastapi import APIRouter, HTTPException
from app.database import supabase_client

# 载入 .env 配置
load_dotenv()

# 读取 Supabase 配置（如果有）
SCHOOL_GPT_API_URL = os.getenv("SCHOOL_GPT_API_URL")
SCHOOL_GPT_API_KEY = os.getenv("SCHOOL_GPT_API_KEY")

router = APIRouter()

# ========== 📌 用户管理 API ==========
@router.get("/api/users/")
async def get_users():
    """ 获取所有用户 """
    response = supabase_client.table("users").select("*").execute()
    return response.data

@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """ 获取单个用户信息 """
    response = supabase_client.table("users").select("*").eq("user_id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="用户未找到")
    return response.data[0]

# ========== 📌 小组管理 API ==========
@router.get("/api/groups/")
async def get_groups():
    """ 获取所有小组 """
    response = supabase_client.table("groups").select("*").execute()
    return response.data

@router.get("/api/groups/{group_id}")
async def get_group(group_id: str):
    """ 获取单个小组信息 """
    response = supabase_client.table("groups").select("*").eq("id", group_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="小组未找到")
    return response.data[0]

@router.get("/api/groups/{group_id}/members")
async def get_group_members(group_id: str):
    """ 获取小组成员 """
    response = supabase_client.table("group_memberships").select("*").eq("group_id", group_id).execute()
    return response.data

# ========== 📌 聊天 API ==========
@router.get("/api/chat/{group_id}")
async def get_chat_history(group_id: str):
    """ 获取某个小组的聊天记录 """
    response = supabase_client.table("chat_messages").select("*").eq("group_id", group_id).order("created_at", desc=True).execute()
    return response.data


class ChatMessage(BaseModel):
    group_id: str
    user_id: str
    message: str

@router.post("/api/chat/send")
async def send_chat_message(payload: ChatMessage):
    """ 发送消息到 chat_messages 表 """
    data = {
        "group_id": payload.group_id,
        "user_id": payload.user_id,
        "message": payload.message
    }
    response = supabase_client.table("chat_messages").insert(data).execute()
    return response.data

# ========== 📌 AI 机器人 API ==========

@router.get("/api/ai/bots/{group_id}")
async def get_ai_bot(group_id: str):
    """ 获取指定小组的AI机器人信息 """
    response = supabase_client.table("ai_bots").select("*").eq("group_id", group_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="未找到AI机器人")
    return response.data[0]
    
    # ========== 📌 聊天议程 API ==========
@router.get("/api/chat/agenda/{group_id}")
async def get_chat_agenda(group_id: str):
    """ 获取指定小组的聊天议程 """
    response = supabase_client.table("chat_agendas").select("*").eq("group_id", group_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="未找到聊天议程")
    return response.data

# ========== 📌 聊天实时汇总 API ==========
@router.get("/api/chat/summaries/{group_id}")
async def get_chat_summaries(group_id: str):
    """ 获取指定小组的聊天实时汇总 """
    response = supabase_client.table("chat_summaries").select("*").eq("group_id", group_id).order("summary_time", desc=True).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="未找到聊天实时汇总")
    return response.data

# ========== 📌 最近1分钟聊天总结 API ==========
@router.get("/api/chat/summary/latest/{group_id}")
async def get_latest_chat_summary(group_id: str):
    """ 获取指定小组的最近1分钟聊天总结 """
    response = supabase_client.table("chat_summaries").select("*").eq("group_id", group_id).order("summary_time", desc=True).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="未找到最近的聊天总结")
    return response.data[0]

# ========== 📌 讨论见解 API ==========
@router.get("/api/discussion/insights/{group_id}")
async def get_discussion_insights(group_id: str):
    """ 获取指定小组的讨论见解 """
    response = supabase_client.table("discussion_insights").select("*").eq("group_id", group_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="未找到讨论见解")
    return response.data

# ========== 📌 讨论术语 API ==========
@router.get("/api/discussion/terms/{group_id}")
async def get_discussion_terms(group_id: str):
    """ 获取指定小组的讨论术语 """
    response = supabase_client.table("discussion_terms").select("*").eq("group_id", group_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="未找到讨论术语")
    return response.data
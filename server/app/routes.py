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
class AIRequest(BaseModel):
    group_id: str
    user_message: str

@router.post("/api/ai/respond")
async def ai_respond(payload: AIRequest):
    """ 让 AI 机器人根据 group_id 生成回答 """
    group_id = payload.group_id
    user_message = payload.user_message

    # 从数据库获取与 group_id 关联的 AI bot
    ai_bot = supabase_client.table("ai_bots").select("*").eq("group_id", group_id).execute()
    if not ai_bot.data:
        return {"error": "AI bot not found"}

    bot_name = ai_bot.data[0]["name"]

    # 发送请求到学校的 GPT API
    request_payload = {
        "bot_name": bot_name,
        "user_message": user_message
    }
    headers = {"Authorization": f"Bearer {SCHOOL_GPT_API_KEY}"} if SCHOOL_GPT_API_KEY else {}

    try:
        # 向学校的 GPT API 发送请求
        response = requests.post(SCHOOL_GPT_API_URL, json=request_payload, headers=headers)
        response.raise_for_status()
        ai_reply = response.json().get("reply", "AI 没有返回消息")

        # 将 AI 生成的回复存入数据库
        supabase_client.table("chat_messages").insert({
            "group_id": group_id,
            "user_id": "ai_bot",
            "message": ai_reply
        }).execute()

        return {"bot_response": ai_reply}

    except requests.exceptions.RequestException as e:
        # 捕获请求异常并抛出 HTTP 500 错误
        raise HTTPException(status_code=500, detail=f"学校 API 请求失败: {str(e)}")
    
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

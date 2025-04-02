import os
import requests
from pydantic import BaseModel, Field
from typing import Optional, List 
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.ai_provider import generate_response
from app.database import supabase_client
from app.websocket_routes import (
    push_chat_message, 
    push_ai_summary  # ✅ 确保 WebSocket 触发 AI 会议总结
)
import datetime


load_dotenv()

router = APIRouter()


# ========== 📌 用户管理 API ==========
@router.get("/api/users/")
async def get_users():
    return supabase_client.table("users_info").select("*").execute().data

@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    return supabase_client.table("users_info").select("*").eq("user_id", user_id).execute().data

@router.get("/api/users/{user_id}/agent")
async def get_user_agent(user_id: str):
    """
    获取用户的 AI 代理信息 (agent_id, agent_name)
    """
    result = (
        supabase_client.table("users_info")
        .select("agent_id, personal_agents(name)")
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="未找到该用户的 AI 代理")

    agent_info = result.data[0]
    return {
        "agent_id": agent_info.get("agent_id"),
        "agent_name": agent_info.get("personal_agents", {}).get("name", "无 AI 代理"),
    }

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

class AgendaCreateRequest(BaseModel):
    group_id: str
    session_id: str
    agenda_title: str
    agenda_description: Optional[str] = ""
    status: Optional[str] = "not_started"

@router.post("/api/chat/agenda")
async def create_agenda(data: AgendaCreateRequest):
    """
    新增一个议程项
    """
    try:
        insert_data = {
            "group_id": data.group_id,
            "session_id": data.session_id,
            "agenda_title": data.agenda_title,
            "agenda_description": data.agenda_description,
            "status": data.status,
        }

        response = supabase_client.table("chat_agendas").insert(insert_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="新增议程失败")

        return {"message": "议程已创建", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建议程失败: {str(e)}")

class AgendaUpdateRequest(BaseModel):
    agenda_title: Optional[str] = None
    agenda_description: Optional[str] = None
    status: Optional[str] = None

@router.put("/api/chat/agenda/{agenda_id}")
async def update_agenda(agenda_id: str, update_data: AgendaUpdateRequest):
    """
    修改指定 agenda 的标题、描述或状态
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    update_response = (
        supabase_client.table("chat_agendas")
        .update(update_fields)
        .eq("id", agenda_id)
        .execute()
    )

    if not update_response.data:
        raise HTTPException(status_code=404, detail="未找到要更新的议程")

    latest = (
        supabase_client.table("chat_agendas")
        .select("*")
        .eq("id", agenda_id)
        .execute()
        .data[0]
    )

#    return {"message": "议程已更新", "data": latest}
    return {"message": "议程已更新", "data": latest}

@router.delete("/api/chat/agenda/{agenda_id}")
async def delete_agenda(agenda_id: str):
    """
    删除指定的议程项
    """
    try:
        response = (
            supabase_client.table("chat_agendas")
            .delete()
            .eq("id", agenda_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="未找到要删除的议程")
        return {"message": "议程已删除", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除议程失败: {str(e)}")

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

# ✅ 定义数据模型
class DiscussionInsightCreate(BaseModel):
    group_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message_text: str  # 用户查询的文本
    ai_provider: Optional[str] = "xai"  # AI 提供商
    agent_id: Optional[str] = None  # 新增字段

class DiscussionInsightResponse(BaseModel):
    id: int
    group_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    message_id: Optional[int]
    insight_text: str
    created_at: str

# ✅ 创建 AI 查询记录
@router.post("/api/discussion_insights", response_model=DiscussionInsightResponse)
async def create_discussion_insight(data: DiscussionInsightCreate):
    """
    通过 AI 进行跨学科术语查询，并存入 discussion_insights 表。
    """
    try:
        # ✅ 打印传入参数
        print("📥 接收到查询请求:")
        print(f"🔹 message_text: {data.message_text}")
        print(f"🔹 ai_provider: {data.ai_provider}")
        print(f"🔹 agent_id: {data.agent_id}")
        print(f"🔹 prompt_type: term_explanation")

        # ✅ 判断使用 agent_id 还是 bot_id（必须二选一）
        if "term_explanation" == "term_explanation":  # 你后续可以改为变量
            if not data.agent_id:
                raise HTTPException(status_code=400, detail="term_explanation 类型必须传入 agent_id")
            provider_bot_id = data.agent_id
        else:
            if not data.bot_id:
                raise HTTPException(status_code=400, detail="非 term_explanation 类型必须传入 bot_id")
            provider_bot_id = data.bot_id

        ai_response = generate_response(
            bot_id=provider_bot_id,
            main_prompt=data.message_text,
            prompt_type="term_explanation",
            api_provider=data.ai_provider,
            agent_id=data.agent_id
        )
        print("🤖 AI 返回内容:")
        print(ai_response)
        # ✅ 记录 AI 生成的查询结果
        new_insight = {
            "group_id": data.group_id,
            "session_id": data.session_id,
            "user_id": data.user_id,
            "message_id": None,  # 目前没有消息 ID，设为空
            "insight_text": ai_response,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "agent_id": data.agent_id,  # 新增记录 agent_id
        }

        # 插入数据库
        insert_response = supabase_client.from_("discussion_insights").insert(new_insight).execute()
        
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="插入数据库失败")

        return DiscussionInsightResponse(**insert_response.data[0])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

# ✅ 获取所有查询记录
@router.get("/api/discussion_insights", response_model=List[DiscussionInsightResponse])
async def get_all_discussion_insights():
    """
    获取所有查询记录
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")

# ✅ 按 `group_id` 获取查询记录
@router.get("/api/discussion_insights/{group_id}", response_model=List[DiscussionInsightResponse])
async def get_discussion_insights_by_group(group_id: str):
    """
    获取特定小组的查询记录
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*").eq("group_id", group_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")

# ✅ 按 `group_id` 和 `session_id` 获取查询记录
@router.get("/api/discussion_insights/{group_id}/{session_id}", response_model=List[DiscussionInsightResponse])
async def get_discussion_insights_by_session(group_id: str, session_id: str):
    """
    获取特定小组和会话的查询记录
    """
    try:
        response = supabase_client.from_("discussion_insights").select("*") \
            .eq("group_id", group_id) \
            .eq("session_id", session_id) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询记录失败: {str(e)}")

class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    group_goal: Optional[str] = None

@router.put("/api/groups/{group_id}")
async def update_group_info(group_id: str, update_data: GroupUpdateRequest):
    """
    更新小组的名称和目标
    """
    update_fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    response = (
        supabase_client.table("groups")
        .update(update_fields)
        .eq("id", group_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="未找到该小组或更新失败")

    return {"message": "小组信息已更新", "data": response.data[0]}

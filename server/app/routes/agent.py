from fastapi import APIRouter, HTTPException, Query, Body
from app.database import supabase_client
from app.generate_prompts import (
    generate_prompts_for_personal_agent,
    set_personal_prompt_version_active,
)
import traceback

router = APIRouter()


# 🎯 为某个用户的 AI Agent 生成 prompts（并激活最新版本）
@router.post("/api/personal_agents/generate_prompt/{agent_id}")
async def generate_prompt_for_personal_agent(agent_id: str):
    """
    为个人 AI Agent 生成 prompts（包含 term_explanation 和 knowledge_followup）
    并将生成的版本设为当前激活版本
    """
    try:
        new_versions = generate_prompts_for_personal_agent(agent_id)
        for item in new_versions:
            set_personal_prompt_version_active(item["agent_id"], item["prompt_type"], item["version"])
        return {
            "message": f"{agent_id} 的 prompts 已生成并激活",
            "data": new_versions,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# 📚 获取某个 AI Agent 的所有 prompt 历史版本（term_explanation 和 knowledge_followup）
@router.get("/api/personal_prompt_versions/{agent_id}")
async def get_personal_prompt_versions(agent_id: str):
    """
    获取指定个人 AI Agent 的 prompt 历史版本（term_explanation 和 knowledge_followup）
    """
    try:
        result = {}
        for prompt_type in ["term_explanation", "knowledge_followup"]:
            query = (
                supabase_client.table("agent_prompt_versions")
                .select("*")
                .eq("agent_id", agent_id)
                .eq("prompt_type", prompt_type)
                .order("created_at", desc=True)
            )
            query_result = query.execute().data
            for item in query_result:
                item["is_current"] = item.get("is_active", False)
            result[prompt_type] = query_result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取版本失败: {str(e)}")

        
# 📌 根据 agent_id 获取个人 AI Agent 的信息
@router.get("/api/personal_agents/{agent_id}")
async def get_personal_agent(agent_id: str):
    """
    获取指定 ID 的个人 AI Agent 信息
    """
    try:
        result = (
            supabase_client.table("personal_agents")
            .select("*")
            .eq("id", agent_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="未找到该 Agent")
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Agent 信息失败: {str(e)}")

# 🔄 更新个人 AI Agent 的模型字段
@router.put("/api/personal_agents/{agent_id}/model")
async def update_personal_agent_model(agent_id: str, model: str = Body(..., embed=True)):
    """
    更新个人 AI Agent 的模型字段（model）
    """
    try:
        update_response = (
            supabase_client.table("personal_agents")
            .update({"model": model})
            .eq("id", agent_id)
            .execute()
        )
        if not update_response.data:
            raise HTTPException(status_code=404, detail="更新失败，未找到该 Agent")
        return {"message": "模型已更新", "data": update_response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

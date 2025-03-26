import os
import json
import requests
from dotenv import load_dotenv
from app.prompt_loader import get_prompt_from_database

# ✅ 加载 .env 配置
load_dotenv()

# ✅ 读取 API 相关配置
HKUST_AI_API_KEY = os.getenv("SCHOOL_GPT_API_KEY")
HKUST_AI_API_BASE = os.getenv("SCHOOL_GPT_API_URL", "https://gpt-api.hkust-gz.edu.cn/v1")

def generate_ai_response(bot_id: str, main_prompt: str, history_prompt: str = None, prompt_type: str = "real_time_summary", model: str = "gpt-4"):
    """
    调用 HKUST GZ AI API 生成 AI 会议总结
    """
    if not HKUST_AI_API_KEY:
        return "❌ API Key 为空，请检查 `.env` 配置"

    prompt_data = get_prompt_from_database(bot_id, prompt_type)
    if prompt_data is None:
        return f"❌ '{prompt_type}' 的 prompt 未定义，请检查数据库。"

    try:
        max_words = prompt_data["max_words"]
        system_prompt = prompt_data["system_prompt"].replace("{max_words}", str(max_words))

        # ✅ 处理不同的 `prompt_type`
        if prompt_type == "real_time_summary":
            user_prompt = f"请在 {max_words} 词以内总结以下内容：\n\n{main_prompt}"
        elif prompt_type == "cognitive_guidance":
            user_prompt = f"请根据以下讨论内容，判断是否需要引导团队进一步讨论，并提供知识支持：\n\n{main_prompt}"
        elif prompt_type == "term_explanation":
            user_prompt = f"请在 {max_words} 词以内解释这个术语：\n\n{main_prompt}"
        else:
            return "❌ 不支持的 `prompt_type`"

        messages = [
            {"role": "system", "content": system_prompt},  
            {"role": "user", "content": user_prompt},  
        ]

        # ✅ 如果有历史消息，则插入 `assistant` 角色（但权重较低）
        if history_prompt:
            messages.append({"role": "assistant", "content": history_prompt})

        # ✅ 构造请求体
        payload = {
            "model": "gpt-4",  # ✅ 正确写法
            "messages": messages,
            "temperature": 1,
            "max_tokens": 280,

        }   

        # ✅ API 头部
        headers = {
            "Authorization": f"Bearer {HKUST_AI_API_KEY}",  # ✅ 确保是 `Bearer` 格式
            "Content-Type": "application/json"
        }

        # ✅ 确保 URL 正确（避免 `/chat/completions/chat/completions` 这种错误）
        api_url = f"{HKUST_AI_API_BASE}/chat/completions"
        print(f"📤 发送请求到 HKUST GZ AI: {api_url}")
        print(f"📦 请求 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        response = requests.post(api_url, json=payload, headers=headers)
        response_data = response.json()

        print(f"📥 API 响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

        # ✅ 解析 AI 响应
        if response.status_code == 200 and "choices" in response_data:
            ai_text = response_data["choices"][0]["message"]["content"].strip()
            return ai_text
        elif "error" in response_data:
            return f"❌ AI 生成失败: {response_data['error']['message']}"
        else:
            return f"❌ AI 生成失败，返回数据格式错误: {json.dumps(response_data, indent=2, ensure_ascii=False)}"
    
    except Exception as e:
        print(f"❌ HKUST GZ AI API 调用失败: {e}")
        return f"AI 生成失败，请稍后再试。错误详情: {str(e)}"
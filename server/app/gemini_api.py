import os
import json
import requests
from dotenv import load_dotenv
from app.prompt_loader import get_prompt_from_database

# ✅ 加载 .env
load_dotenv()

# ✅ 初始化 Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")


def generate_ai_response(bot_id: str, main_prompt: str, history_prompt: str = None,
                         prompt_type: str = "real_time_summary", model: str = "gemini-2.5-pro-exp-03-25"):
    """
    发送请求到 Gemini API，基于 prompt_type 选择不同的提示词
    """
    try:
        # ✅ 读取对应类型的 prompt
        prompt_data = get_prompt_from_database(bot_id, prompt_type)
        max_words = prompt_data["max_words"]
        system_prompt = prompt_data["system_prompt"].replace("{max_words}", str(max_words))

        # ✅ 构造用户 prompt
        if prompt_type == "real_time_summary":
            user_prompt = f"请在 {max_words} 词以内总结以下内容：\n\n{main_prompt}"
        elif prompt_type == "cognitive_guidance":
            user_prompt = f"请根据以下讨论内容，判断是否需要引导团队进一步讨论，并提供知识支持：\n\n{main_prompt}"
        elif prompt_type == "term_explanation":
            user_prompt = f"请在 {max_words} 词以内解释这个术语：\n\n{main_prompt}"
        else:
            return f"❌ 不支持的 prompt_type: {prompt_type}"

        # ✅ 构造 API 请求内容（仿 OpenAI 风格）
        messages = [system_prompt, user_prompt]
        if history_prompt:
            messages.append(history_prompt)

        api_payload = {
            "contents": [
                {
                    "parts": [{"text": "\n\n".join(messages)}]
                }
            ]
        }
        model = "gemini-2.5-pro-exp-03-25"
        # ✅ 请求信息
        api_url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={GEMINI_API_KEY}"
        headers = {
            "Content-Type": "application/json"
        }

        # ✅ 打印请求日志
        print("📤 发送请求到 Gemini API:")
        print(f"🔗 API URL: {api_url}")
        print(f"🔑 API Key: {'✅ 已设置' if GEMINI_API_KEY else '❌ 未设置'}")
        print(f"📦 Payload:\n{json.dumps(api_payload, indent=2, ensure_ascii=False)}")

        # ✅ 发起请求
        response = requests.post(api_url, headers=headers, json=api_payload)
        response_data = response.json()

        # ✅ 打印返回结果
        print(f"📥 Gemini API 响应:\n{json.dumps(response_data, indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and "candidates" in response_data:
            ai_text = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"✅ Gemini 响应文本:\n{ai_text}")
            return ai_text
        else:
            return f"❌ Gemini 响应失败: {json.dumps(response_data, ensure_ascii=False)}"

    except Exception as e:
        print(f"❌ Gemini API 请求失败: {e}")
        return f"AI 生成失败，请稍后再试。错误详情: {str(e)}"
import os
import json
from openai import OpenAI  
from dotenv import load_dotenv
from app.prompt_loader import get_prompt_from_database

# ✅ 加载 .env 配置
load_dotenv()

# ✅ 读取 API 相关配置
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_BASE = os.getenv("XAI_API_BASE", "https://api.x.ai/v1")

# ✅ 初始化 OpenAI 客户端
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url=XAI_API_BASE,
)

def generate_ai_response(bot_id: str, main_prompt: str, history_prompt: str = None, prompt_type: str = "real_time_summary", model: str = "grok-2-latest", agent_id: str = None):
    """
    发送请求到 xAI API，基于 prompt_type 选择不同的提示词 (prompt)
    """
    try:
        # ✅ 获取 prompt 数据
        if prompt_type == "term_explanation":
            if not agent_id:
                raise ValueError("term_explanation 类型必须提供 agent_id")
            prompt_data = get_prompt_from_database(
                bot_id=agent_id,
                prompt_type=prompt_type,
                agent_id=agent_id
            )
        else:
            if not bot_id:
                raise ValueError("非 term_explanation 类型必须提供 bot_id")
            prompt_data = get_prompt_from_database(
                bot_id=bot_id,
                prompt_type=prompt_type,
                agent_id=agent_id
            )
        
        max_words = prompt_data["max_words"]
        system_prompt = prompt_data["system_prompt"].replace("{max_words}", str(max_words))

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

        # ✅ 构造 API 请求数据
        api_payload = {
            "model": "grok-2-latest",
             "temperature": 1,
            "messages": messages,
            "max_tokens": 280,

        }

        # ✅ **打印即将发送的 API 请求参数**
        print("📤 model:")
        print("📤 发送请求到 xAI API:")
        print(f"🔗 API 网址: {XAI_API_BASE}")
        print(f"🔑 API Key: {'✅ 已设置' if XAI_API_KEY else '❌ 未设置'}")
        print(f"📦 请求 Payload:\n{json.dumps(api_payload, indent=2, ensure_ascii=False)}")

        # ✅ 发送 API 请求
        response = client.chat.completions.create(**api_payload)
        print(f"📥 原始响应对象: {response}")
        print(f"📥 原始响应 JSON: {getattr(response, 'model_dump_json', lambda: str(response))()}")

        # ✅ **打印 API 返回结果**
        print(f"📥 API 响应: {response}")

        ai_text = response.choices[0].message.content.strip()
        print(f"✅ xAI API 响应:\n{ai_text}")  # ✅ 打印 AI 生成的内容
        return ai_text
    except Exception as e:
        print("❌ xAI API 请求失败:")
        import traceback
        traceback.print_exc()
        return "AI 生成失败，请稍后再试。"
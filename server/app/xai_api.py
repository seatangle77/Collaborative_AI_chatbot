import os
from openai import OpenAI  # ✅ 正确导入新版 SDK
from dotenv import load_dotenv

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

def generate_ai_response(prompt: str, model: str = "grok-2-latest"):
    """
    发送请求到 xAI API，生成 AI 见解
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个智能助手，帮助用户理解讨论内容并生成见解。"},
                {"role": "user", "content": prompt},
            ],
        )
        ai_text = response.choices[0].message.content
        print(f"✅ xAI API 响应: {ai_text}")  # ✅ 打印 AI 生成的内容
        return ai_text
    except Exception as e:
        print(f"❌ xAI API 请求失败: {e}")
        return "AI 生成失败，请稍后再试。"

# ✅ **测试 AI 响应**
if __name__ == "__main__":
    test_prompt = "请总结以下对话的关键讨论点。"
    print(generate_ai_response(test_prompt))
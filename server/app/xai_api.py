import os
import json
from openai import OpenAI  
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

# ✅ 获取 `prompt.json` 的正确路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前 `xai_api.py` 所在的目录
PROMPT_PATH = os.path.join(BASE_DIR, "prompt.json")  # 生成 `prompt.json` 的完整路径

# ✅ 读取 JSON 配置，确保文件路径正确
try:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt_config = json.load(f)
except FileNotFoundError:
    print(f"❌ 错误：未找到 `prompt.json` 文件，检查路径是否正确：{PROMPT_PATH}")
    prompt_config = {}  # 避免后续 `KeyError`，但会导致 API 无法正确运行

def generate_ai_response(prompt: str, prompt_type: str = "real_time_summary", model: str = "grok-2-latest"):
    """
    发送请求到 xAI API，基于 prompt_type 选择不同的提示词 (prompt)
    """
    if prompt_type not in prompt_config:
        return f"❌ 未找到 '{prompt_type}' 对应的 prompt，请检查 `prompt.json`。"

    try:
        # ✅ 读取对应类型的 prompt
        prompt_data = prompt_config[prompt_type]
        max_words = prompt_data["max_words"]
        system_prompt = prompt_data["system_prompt"].replace("{max_words}", str(max_words))

        # ✅ 构造 API 请求数据
        api_payload = {
            "model": "grok-2-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请在 {max_words} 词以内总结以下内容：\n\n{prompt}"},
            ],
        }

        # ✅ **打印即将发送的 API 请求参数**
        print("📤 model:")
        print("📤 发送请求到 xAI API:")
        print(f"🔗 API 网址: {XAI_API_BASE}")
        print(f"🔑 API Key: {'✅ 已设置' if XAI_API_KEY else '❌ 未设置'}")
        print(f"📦 请求 Payload:\n{json.dumps(api_payload, indent=2, ensure_ascii=False)}")

        # ✅ 发送 API 请求
        response = client.chat.completions.create(**api_payload)

        # ✅ **打印 API 返回结果**
        print(f"📥 API 响应: {response}")

        ai_text = response.choices[0].message.content.strip()
        print(f"✅ xAI API 响应:\n{ai_text}")  # ✅ 打印 AI 生成的内容
        return ai_text
    except Exception as e:
        print(f"❌ xAI API 请求失败: {e}")
        return "AI 生成失败，请稍后再试。"
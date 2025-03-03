import os
from app.xai_api import generate_ai_response as generate_xai_response
from app.hkust_gz_ai_api import generate_ai_response as generate_hkust_response

# 读取默认 AI 提供商（支持 `xai` 或 `hkust_gz`）
DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "xai")  # 默认使用 xAI，可改成 "hkust_gz"

def generate_response(prompt: str, prompt_type: str = "real_time_summary", model: str = "grok-2-latest", api_provider: str = None):
    """
    统一管理 AI API 调用，支持 xAI 和 HKUST GZ AI 之间的切换。
    
    - `prompt`: 需要 AI 处理的文本内容
    - `prompt_type`: 使用的 prompt 类型，例如 `real_time_summary`
    - `model`: 具体使用的 AI 模型（如 `grok-2-latest` 或 `hkust-gz-latest`）
    - `api_provider`: 指定使用哪个 AI 提供商（`xai` 或 `hkust_gz`）
    """
    api_provider = api_provider or DEFAULT_AI_PROVIDER  # 如果没有传入，则使用默认提供商

    if api_provider == "xai":
        return generate_xai_response(prompt, prompt_type, model)
    elif api_provider == "hkust_gz":
        return generate_hkust_response(prompt, prompt_type, model)
    else:
        return f"❌ 未知的 AI 提供商 '{api_provider}'，请使用 'xai' 或 'hkust_gz'。"
import importlib.util
from jinja2 import Template
from supabase import create_client, Client
import os
import traceback

# 数据库连接
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 获取组数据
def get_group_data(group_id):
    group = supabase.table("groups").select("*").eq("id", group_id).single().execute().data
    agendas = supabase.table("chat_agendas").select("*").eq("group_id", group_id).order("created_at").execute().data
    member_ids = supabase.table("group_memberships").select("user_id").eq("group_id", group_id).execute().data
    user_ids = [m["user_id"] for m in member_ids]
    users = supabase.table("users_info").select("*").in_("user_id", user_ids).execute().data

    user_data = [
        {
            "name": user["name"],
            "academic_background": f"{user['academic_background']['major']}，研究方向：{user['academic_background']['research_focus']}",
            "academic_advantages": user["academic_advantages"].strip()
        }
        for user in users
    ]

    return_data = {
        "group_name": group["name"],
        "group": {
            "goal": group["group_goal"].strip()
        },
        "agenda_title": agendas[0]["agenda_title"] if agendas else "",
        "agenda_description": agendas[0]["agenda_description"] if agendas else "",
        "users": user_data
    }
    if user_data:
        return_data["user"] = user_data[0]
    return return_data

def load_default_prompts(path="default_prompts.py"):
    full_path = os.path.join(os.path.dirname(__file__), path)
    spec = importlib.util.spec_from_file_location("default_prompts", full_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DEFAULT_PROMPTS

def generate_prompts_for_group(group_id: str):
    try:
        prompts = load_default_prompts("default_prompts.py")
        bot = supabase.table("ai_bots").select("*").eq("group_id", group_id).single().execute().data
        if not bot:
            return
        bot_id = bot["id"]
        data = get_group_data(group_id)

        for prompt_name, content in prompts.items():
            try:
                template = Template(content["system_prompt"])
                filled_prompt = template.render(**data)
            except Exception as e:
                print(f"❌ 渲染失败 group_id={group_id}, prompt={prompt_name}: {e}")
                print("⚠️ 当前数据内容为：", data)
                continue
            field_name = f"{prompt_name}_systemprompt"
            
            existing_versions = supabase.table("ai_prompt_versions").select("template_version").eq("ai_bot_id", bot_id).eq("prompt_type", prompt_name).execute().data
            version_numbers = [int(v["template_version"].lstrip("v")) for v in existing_versions if v["template_version"].startswith("v") and v["template_version"][1:].isdigit()]
            new_version = max(version_numbers, default=0) + 1
            template_version = f"v{new_version}"
            
            supabase.table("ai_bots").update({field_name: filled_prompt}).eq("id", bot_id).execute()
            supabase.table("ai_prompt_versions").insert({
                "ai_bot_id": bot_id,
                "group_id": group_id,
                "prompt_type": prompt_name,
                "rendered_prompt": filled_prompt,
                "template_version": template_version,
                "source": "auto"
            }).execute()
            print(f"✅ Updated {field_name} for bot {bot['name']}")
    except Exception as e:
        print("🔥 生成 prompts 失败（全局异常）:")
        traceback.print_exc()

# 第三步：读取模板并替换
if __name__ == "__main__":
    all_bots = supabase.table("ai_bots").select("group_id").execute().data
    for b in all_bots:
        generate_prompts_for_group(b["group_id"])
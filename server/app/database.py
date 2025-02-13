import os
import supabase
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# 获取小组数据
# async def get_groups():
#     response = supabase_client.table("groups").select("*").execute()
#     return response.data
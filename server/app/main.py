from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router  # 导入所有的 API 路由
from app.websocket_routes import websocket_router  # 导入 WebSocket 路由

# ✅ 创建 FastAPI 实例
app = FastAPI()

# ✅ 允许的前端源
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ✅ 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 🚀 允许特定来源
    allow_credentials=True,  # 🚀 允许携带 Cookie/session
    allow_methods=["*"],  # 🚀 允许所有 HTTP 方法（GET, POST, OPTIONS, PUT, DELETE）
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Headers"],  # 🚀 明确允许 Content-Type
)

# ✅ WebSocket 需要手动添加 CORS 允许
@app.middleware("http")
async def websocket_cors_middleware(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# ✅ 处理 OPTIONS 预检请求，防止 CORS 拦截 POST 请求
@app.options("/api/chat/send/")
async def options_handler(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# ✅ 注册 API 路由
app.include_router(router)

# ✅ 注册 WebSocket 路由
app.include_router(websocket_router)

# ✅ 根路径测试 API
@app.get("/")
async def root():
    return {"message": "Welcome to Collaborative AI Chatbot API with WebSocket!"}
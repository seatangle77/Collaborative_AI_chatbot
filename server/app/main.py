from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router  # 导入所有的路由
from app.websocket_routes import websocket_router  # 新增的WebSocket路由


# 创建 FastAPI 实例
app = FastAPI()

# 允许的源，可以使用 "*" 来允许所有来源
origins = [
    "http://localhost",            # 允许 localhost 访问
    "http://localhost:5173",       # 允许 Vue 前端开发服务器访问
    "http://127.0.0.1:5173",      # 如果是本地开发，可能会用到此地址
    "http://localhost:3000",  # 允许前端访问
    "http://127.0.0.1:3000",  # 兼容不同方式
    
]

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许的 HTTP 方法
    allow_headers=["*"],  # 允许的请求头
)

# ✅ WebSocket 需要手动添加 CORS 支持
@app.middleware("http")
async def websocket_cors_middleware(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


# 将路由包含进来
app.include_router(router)
app.include_router(websocket_router)  # 引入WebSocket路由


@app.get("/")
async def root():
    return {"message": "Welcome to Collaborative AI Chatbot API with WebSocket!"}
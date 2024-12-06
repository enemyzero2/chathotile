from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from CLIENT.chat_client import ChatClient
import uvicorn
from typing import Dict, Optional
from pydantic import BaseModel
import threading
from datetime import datetime

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
chat_client: Optional[ChatClient] = None
client_lock = threading.Lock()

# WebSocket消息处理回调
def handle_ws_message(message: dict):
    print(f"收到WebSocket消息: {message}")
    # 这里可以添加消息处理逻辑
    pass

# ============ APP相关接口 ============
@app.post("/init-client")
async def init_chat_client():
    """初始化聊天客户端并连接到服务器"""
    global chat_client
    
    with client_lock:
        if chat_client is not None:
            return {"status": "error", "message": "客户端已经初始化"}
        
        try:
            chat_client = ChatClient(host="127.0.0.1", port=8888)
            chat_client.set_message_callback(handle_ws_message)
            if chat_client.connect(username="test_user"):  # 后续可以改为实际用户名
                return {"status": "success", "message": "客户端初始化成功"}
            else:
                chat_client = None
                return {"status": "error", "message": "客户端连接失败"}
        except Exception as e:
            chat_client = None
            return {"status": "error", "message": f"初始化失败: {str(e)}"}

@app.post("/close-client")
async def close_chat_client():
    """关闭聊天客户端连接"""
    global chat_client
    
    with client_lock:
        if chat_client is None:
            return {"status": "error", "message": "客户端未初始化"}
        
        try:
            chat_client.disconnect()
            chat_client = None
            return {"status": "success", "message": "客户端已关闭"}
        except Exception as e:
            return {"status": "error", "message": f"关闭失败: {str(e)}"}

# ============ User相关接口 ============
@app.get("/user/info")
async def get_user_info():
    """获取用户信息"""
    # 模拟用户数据，实际应该从数据库获取
    return {
        "id": 1,
        "name": "测试用户",
        "background": "这是一个测试用户",
        "avatar": None,
        "createdAt": datetime.now().isoformat()
    }

class UserProfileData(BaseModel):
    name: str
    background: str

@app.post("/user/profile")
async def save_user_profile(data: UserProfileData):
    """保存用户资料"""
    # 这里应该添加数据库保存逻辑
    return {"message": "资料保存成功"}

# ============ 启动服务器 ============
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8082)

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from SERVER.chat_server import ChatServer
from CLIENT.chat_client import ChatClient
import threading
import time
from datetime import datetime
from MODELS.models import Message, Chat, SendMessageData
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

chat_server = ChatServer(host="127.0.0.1", port=8888)

threading.Thread(target=chat_server.start, daemon=True).start()

# 初始化示例数据
chat_rooms = {
    1: Chat(
        id=1,
        name="公共聊天室",
        lastMessage="欢迎来到公共聊天室",
        time=datetime.now().isoformat(),
        members="all"
    ),
    2: Chat(
        id=2,
        name="技术交流",
        lastMessage="有人在线吗？",
        time=datetime.now().isoformat(),
        members="developers"
    )
}

chat_history = {
    1: [
        Message(
            id=1,
            content="欢迎来到公共聊天室",
            isSelf=False,
            createdAt=datetime.now().isoformat()
        )
    ],
    2: [
        Message(
            id=1,
            content="有人在线吗？",
            isSelf=False,
            createdAt=datetime.now().isoformat()
        )
    ]
}

# WebSocket连接管理
active_connections: Dict[str, WebSocket] = {}
# 为每个WebSocket连接创建对应的ChatClient
ws_clients: Dict[str, ChatClient] = {}

@app.get("/chats", response_model=List[Chat])
async def get_chats():
    return list(chat_rooms.values())

@app.get("/chats/{chat_id}/messages", response_model=List[Message])
async def get_messages(chat_id: int):
    return chat_history.get(chat_id, [])

@app.post("/messages", response_model=Message)
async def send_message(message_data: SendMessageData):
    new_message = Message(
        id=len(chat_history.get(message_data.chatId)) + 1,
        content=message_data.content,
        isSelf=message_data.isSelf,
        createdAt=datetime.now().isoformat()
    )

    if message_data.chatId not in chat_history:
        chat_history[message_data.chatId] = []
    chat_history[message_data.chatId].append(new_message)

    if message_data.chatId in chat_rooms:
        chat_rooms[message_data.chatId].lastMessage = message_data.content
        chat_rooms[message_data.chatId].time = datetime.now().isoformat()
    

    chat_server._broadcast({
        'type': 'chat',
        'content': message_data.content,
        'chatId': message_data.chatId,
        'isSelf': message_data.isSelf
    })

    return new_message

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket
    
    # 创建ChatClient实例
    client = ChatClient()
    ws_clients[username] = client
    
    # 设置消息回调，将ChatClient收到的消息转发到WebSocket
    def message_handler(message: dict):
        asyncio.create_task(websocket.send_json(message))
    
    client.set_message_callback(message_handler)
    
    # 连接到聊天服务器
    if not client.connect(username):
        await websocket.close()
        return
    
    try:
        while True:
            # 接收WebSocket消息并转发到ChatClient
            data = await websocket.receive_json()
            client.send_message(data['content'])
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # 清理连接
        if username in active_connections:
            del active_connections[username]
        if username in ws_clients:
            client.disconnect()
            del ws_clients[username]
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)


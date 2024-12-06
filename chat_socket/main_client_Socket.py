from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from CLIENT.chat_client import ChatClient
from MODELS import Message, Chat, UserProfileData
from typing import Dict, Optional
from pydantic import BaseModel
import threading
import asyncio
from datetime import datetime
import json
import uvicorn
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        logger.info("初始化ConnectionManager")
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_clients: Dict[str, ChatClient] = {}
        
        # 初始化聊天室数据
        self.chat_rooms: Dict[int, Chat] = {
            1: Chat(
                id=1,
                name="公共聊天室",
                type="group",
                lastMessage="欢迎来到聊天室",
                time=datetime.now().isoformat(),
                unreadCount=0,
                avatar=None
            )
        }
        logger.info("默认聊天室已创建")

    async def send_chat_list(self, username: str):
        """发送聊天室列表"""
        if username in self.active_connections:
            try:
                await self.active_connections[username].send_json({
                    'type': 'chat_list',
                    'chats': [chat.dict() for chat in self.chat_rooms.values()]
                })
                logger.debug(f"已发送聊天列表给用户 {username}")
            except Exception as e:
                logger.error(f"发送聊天列表失败: {e}", exc_info=True)

    async def connect(self, websocket: WebSocket, username: str):
        """处理新的WebSocket连接"""
        logger.info(f"用户 {username} 正在尝试连接")
        await websocket.accept()
        self.active_connections[username] = websocket
        logger.info(f"用户 {username} WebSocket连接成功")
        
        # 创建ChatClient实例
        client = ChatClient(host="127.0.0.1", port=8888)
        logger.info(f"为用户 {username} 创建ChatClient实例")
        
        async def message_handler(message: dict):
            try:
                logger.debug(f"处理来自用户 {username} 的消息: {message}")
                
                if username in self.active_connections:
                    ws = self.active_connections[username]
                    if message.get('type') == 'system':
                        ws_message = {
                            'type': 'system',
                            'content': message.get('content', ''),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        content = message.get('content', '{}')
                        if isinstance(content, str):
                            try:
                                msg_data = json.loads(content)
                            except json.JSONDecodeError:
                                msg_data = {'content': content}
                        else:
                            msg_data = content
                        
                        chat_id = msg_data.get('chatId', 1)
                        
                        if chat_id in self.chat_rooms:
                            self.chat_rooms[chat_id].lastMessage = msg_data.get('content', '')
                            self.chat_rooms[chat_id].time = datetime.now().isoformat()
                        
                        ws_message = {
                            'type': 'message',
                            'content': msg_data.get('content', ''),
                            'sender': username,
                            'timestamp': datetime.now().isoformat(),
                            'chatId': chat_id,
                            'isSelf': False
                        }
                    
                    logger.debug(f"消息处理完成，发送响应: {ws_message}")
                    await ws.send_json(ws_message)
                    
            except Exception as e:
                logger.error(f"处理消息时出错: {e}", exc_info=True)
                logger.error(f"原始消息内容: {message}")

        client.set_message_callback(message_handler)
        logger.info(f"用户 {username} 的消息处理器设置完成")
        
        # 连接到聊天服务器
        if client.connect(username):
            self.chat_clients[username] = client
            logger.info(f"用户 {username} 成功连接到聊天服务器")
            return client
        logger.error(f"用户 {username} 连接到聊天服务器失败")
        return None

    async def disconnect(self, username: str):
        """处理WebSocket断开连接"""
        logger.info(f"正在处理用户 {username} 的断开连接")
        try:
            if username in self.chat_clients:
                client = self.chat_clients[username]
                try:
                    client.disconnect()
                    logger.info(f"用户 {username} 的ChatClient已断开")
                except Exception as e:
                    logger.warning(f"断开客户端连接警告: {e}")
                finally:
                    del self.chat_clients[username]
            
            if username in self.active_connections:
                ws = self.active_connections[username]
                try:
                    if not ws.client_state.disconnected:
                        await ws.close()
                        logger.info(f"用户 {username} 的WebSocket连接已关闭")
                except Exception as e:
                    logger.warning(f"关闭WebSocket连接警告: {e}")
                finally:
                    del self.active_connections[username]
                    
        except Exception as e:
            logger.error(f"断开连接时发生错误: {e}", exc_info=True)

    async def create_chat(self, chat_data: dict) -> Chat:
        """创建新的聊天"""
        logger.info(f"正在创建新聊天: {chat_data}")
        chat_id = len(self.chat_rooms) + 1
        new_chat = Chat(
            id=chat_id,
            name=chat_data.get('name', f'聊天 {chat_id}'),
            type=chat_data.get('type', 'private'),
            lastMessage="",
            time=datetime.now().isoformat(),
            unreadCount=0,
            avatar=chat_data.get('avatar')
        )
        self.chat_rooms[chat_id] = new_chat
        logger.info(f"新聊天创建成功: {new_chat}")
        return new_chat

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        """获取特定聊天的信息"""
        return self.chat_rooms.get(chat_id)

    async def update_chat(self, chat_id: int, data: dict):
        """更新聊天信息"""
        if chat_id in self.chat_rooms:
            chat = self.chat_rooms[chat_id]
            for key, value in data.items():
                if hasattr(chat, key):
                    setattr(chat, key, value)

    async def delete_chat(self, chat_id: int):
        """删除聊天"""
        if chat_id in self.chat_rooms:
            del self.chat_rooms[chat_id]

manager = ConnectionManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    logger.info(f"收到来自用户 {username} 的WebSocket连接请求")
    client = None
    try:
        client = await manager.connect(websocket, username)
        if not client:
            logger.error(f"用户 {username} 连接失败")
            await websocket.close()
            return
        
        logger.info(f"用户 {username} 连接成功，发送聊天列表")
        await manager.send_chat_list(username)
        
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"收到用户 {username} 的消息: {data}")
                
                if data.get('type') == 'request_chat_list':
                    logger.info(f"用户 {username} 请求聊天列表")
                    await manager.send_chat_list(username)
                    continue
                elif data.get('type') == 'create_chat':
                    logger.info(f"用户 {username} 请求创建新聊天")
                    new_chat = await manager.create_chat(data.get('chatData', {}))
                    await manager.send_chat_list(username)
                    continue
                
                # 处理普通聊天消息
                message = {
                    'content': data.get('content', ''),
                    'chatId': data.get('chatId', 1),
                    'sender': username,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'message',
                    'isSelf': True
                }
                logger.debug(f"处理用户 {username} 的聊天消息: {message}")
                
                # 更新聊天室最后消息
                chat_id = message['chatId']
                if chat_id in manager.chat_rooms:
                    manager.chat_rooms[chat_id].lastMessage = message['content']
                    manager.chat_rooms[chat_id].time = message['timestamp']
                    logger.debug(f"更新聊天室 {chat_id} 的最后消息")
                
                client.send_message(json.dumps(message))
                logger.debug(f"消息已发送到聊天服务器")
                
            except WebSocketDisconnect:
                logger.info(f"客户端 {username} 断开连接")
                break
            except Exception as e:
                logger.error(f"处理客户端 {username} 消息时出错: {e}", exc_info=True)
                break
                
    except Exception as e:
        logger.error(f"WebSocket连接处理出错: {e}", exc_info=True)
    finally:
        if client:
            logger.info(f"清理用户 {username} 的连接")
            await manager.disconnect(username)

@app.get("/user/info")
async def get_user_info():
    """获取用户信息"""
    return {
        "id": 1,
        "name": "测试用户",
        "background": "这是一个测试用户",
        "avatar": None,
        "createdAt": datetime.now().isoformat()
    }

@app.post("/user/profile")
async def save_user_profile(data: UserProfileData):
    """保存用户资料"""
    return {"message": "资料保存成功"}

# 添加新的API端点
@app.get("/chats")
async def get_chats():
    """获取所有聊天列表"""
    logger.info("收到获取聊天列表请求")
    chats = [chat.dict() for chat in manager.chat_rooms.values()]
    logger.info(f"返回 {len(chats)} 个聊天室信息")
    return chats

@app.get("/chats/{chat_id}")
async def get_chat(chat_id: int):
    """获取特定聊天的详细信息"""
    chat = await manager.get_chat(chat_id)
    if chat:
        return chat.dict()
    return {"error": "聊天不存在"}

@app.post("/chats")
async def create_chat(chat_data: dict):
    """创建新的聊天"""
    logger.info(f"收到创建聊天请求: {chat_data}")
    new_chat = await manager.create_chat(chat_data)
    logger.info(f"聊天创建成功: {new_chat}")
    return new_chat.dict()

@app.put("/chats/{chat_id}")
async def update_chat(chat_id: int, chat_data: dict):
    """更新聊天信息"""
    await manager.update_chat(chat_id, chat_data)
    return {"message": "更新成功"}

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int):
    """删除聊天"""
    await manager.delete_chat(chat_id)
    return {"message": "删除成功"}

if __name__ == "__main__":
    logger.info("=== FastAPI服务器启动 ===")
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run(app, host="127.0.0.1", port=8082)
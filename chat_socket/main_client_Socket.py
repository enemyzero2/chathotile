from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from CLIENT.chat_client import ChatClient
from MODELS import Message, Chat, UserProfileData
from typing import Dict, Optional, List
from pydantic import BaseModel
import threading
import asyncio
from datetime import datetime
import json
import uvicorn
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, ChatMember, Chat, Message, User
from openai import OpenAI

from MODELS.models import UserProfileUpdateData

app = FastAPI()
client = OpenAI(base_url="https://xdaicn.top/v1",api_key="sk-JmFlLWM2smg4WVgXPMsZW38fHn6ai5HrNV0lXLH4gvOhxPZE")
class openai_message(BaseModel):
    role: str
    content: str

class openai_Request(BaseModel):
    chatId: int
    messages: List[openai_message]

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
        self.db = SessionLocal()
        self.loop = asyncio.get_event_loop()

    async def send_chat_list(self, username: str):
        """发送聊天列表"""
        if username in self.active_connections:
            try:
                # 直接从数据库查询用户的聊天列表
                chat_members = (self.db.query(ChatMember)
                              .join(User, ChatMember.user_id == User.id)
                              .filter(User.username == username)
                              .all())
                
                chats = [{
                    "id": member.chat.id,
                    "name": member.chat.name,
                    "type": member.chat.type,
                    "avatar": member.chat.avatar,
                    "last_message": member.chat.last_message,
                    "last_message_time": member.chat.last_message_time.isoformat() if member.chat.last_message_time else None
                } for member in chat_members]
                
                await self.active_connections[username].send_json({
                    'type': 'chat_list',
                    'chats': chats
                })
                logger.debug(f"已发送聊天列表给用户 {username}")
            except Exception as e:
                logger.error(f"发送聊天列表失败: {e}", exc_info=True)

    async def handle_websocket_message(self, websocket: WebSocket, username: str, id: str, client: ChatClient, data: dict):
        """统一处理 WebSocket 消息"""
        try:
            logger.debug(f"收到用户 {username} 的消息: {data}")
            
            # 处理特殊消息类型
            if data.get('type') == 'request_chat_list':
                logger.info(f"用户 {username} 请求聊天列表")
                await self.send_chat_list(username)
                return
            elif data.get('type') == 'request_chat_messages':
                logger.info(f"用户 {username} 请求聊天消息")
                messages = await self.get_chat_messages(data.get('chatId'), data.get('limit', 50))
                await websocket.send_json({
                    'type': 'chat_messages',
                    'messages': messages
                })
                return
            elif data.get('type') == 'create_chat':
                logger.info(f"用户 {username} 请求创建新聊天")
                new_chat = await self.create_chat(data.get('chatData', {}))
                await self.send_chat_list(username)
                return
            elif data.get('type') == 'claude_message':
                logger.debug(f"收到Claude消息: {data}")
                message = {
                    'content': data.get('content', ''),
                    'chatId': data.get('chatId', 1),
                    'sender': 'Claude',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'message',
                    'isSelf': False
                }
                await self.update_chat_message(message['chatId'], message['content'], "claude")
                logger.debug(f"消息已处理并更新数据库")
                await websocket.send_json(message)
                return
            # 处理普通聊天消息
            message = {
                'content': data.get('content', ''),
                'chatId': data.get('chatId', 1),
                'sender': data.get('sender', username),
                'timestamp': datetime.now().isoformat(),
                'type': 'message',
                'isSelf': data.get('isSelf', True)
            }
            
            # 更新聊天室最后消息
            chat_id = message['chatId']
            new_message = await self.update_chat_message(
                chat_id=chat_id,
                message=message['content'],
                sender_id=id
            )
            
            if new_message:
                message['timestamp'] = new_message.created_at.isoformat()
            
            # 发送消息到聊天服务器
            client.send_message(json.dumps(message))
            # 发送消息到WebSocket客户端
            await websocket.send_json(message)
            logger.debug(f"消息已发送到聊天服务器和WebSocket客户端")
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}", exc_info=True)

    async def connect(self, websocket: WebSocket, username: str, id: str):
        """处理新的WebSocket连接"""
        logger.info(f"用户 {username} 正在尝试连接")
        await websocket.accept()
        self.active_connections[username] = websocket
        logger.info(f"用户 {username} WebSocket连接成功")
        
        # 获取或创建用户
        user = self.db.query(User).filter(User.id == id).first()
        if not user:
            user = User(id=id, username=username)
            self.db.add(user)
            self.db.commit()
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        self.db.commit()
        
        # 获取用户的聊天列表并发送
        await self.send_chat_list(username)
        
        # 创建ChatClient实例并设置消息回调
        client = ChatClient(host="127.0.0.1", port=8888)
        
        # 使用同步回调函数
        def message_callback(msg):
            asyncio.run_coroutine_threadsafe(
                self.handle_server_message(websocket, msg),
                self.loop
            )
        
        client.set_message_callback(message_callback)
        logger.info(f"为用户 {username} 创建ChatClient实例")
        
        # 连接到聊天服务器
        if client.connect(username):
            self.chat_clients[username] = client
            logger.info(f"用户 {username} 成功连接到聊天服务器")
            return client
        logger.error(f"用户 {username} 连接到聊天服务器失败")
        return None

    async def handle_server_message(self, websocket: WebSocket, message_str: str):
        """处理从聊天服务器接收到的消息"""
        try:
            message = json.loads(message_str)
            logger.debug(f"从服务器接收到消息: {message}")
            await websocket.send_json(message)
            logger.debug(f"消息已转发到WebSocket客户端")
        except Exception as e:
            logger.error(f"处理服务器消息时出错: {e}", exc_info=True)

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
        try:
            new_chat = Chat(
                name=chat_data.get('name', '新的聊天'),
                type=chat_data.get('type', 'private'),
                avatar=chat_data.get('avatar'),
                last_message="",
                last_message_time=datetime.now()
            )
            self.db.add(new_chat)
            self.db.flush()  # 获取新生成的ID
            
            # 创建聊天成员关系
            if 'members' in chat_data:
                for user_id in chat_data['members']:
                    chat_member = ChatMember(
                        id=f"cm_{new_chat.id}_{user_id}",
                        chat_id=new_chat.id,
                        user_id=user_id
                    )
                    self.db.add(chat_member)
            
            self.db.commit()
            logger.info(f"新聊天创建成功: {new_chat.id}")
            return new_chat
        except Exception as e:
            logger.error(f"创建聊天失败: {e}")
            self.db.rollback()
            raise

    async def get_chat(self, chat_id: int) -> Optional[Chat]:
        """获取特定聊天的信息"""
        try:
            return self.db.query(Chat).filter(Chat.id == chat_id).first()
        except Exception as e:
            logger.error(f"获取聊天信息失败: {e}")
            return None

    async def update_chat(self, chat_id: int, data: dict):
        """更新聊天信息"""
        try:
            chat = await self.get_chat(chat_id)
            if chat:
                for key, value in data.items():
                    if hasattr(chat, key):
                        setattr(chat, key, value)
                self.db.commit()
                logger.info(f"聊天 {chat_id} 更新成功")
            else:
                logger.warning(f"未找到聊天 {chat_id}")
        except Exception as e:
            logger.error(f"更新聊天失败: {e}")
            self.db.rollback()

    async def delete_chat(self, chat_id: int):
        """删除聊天"""
        try:
            chat = await self.get_chat(chat_id)
            if chat:
                # 首先删除相关的聊天成员关系
                self.db.query(ChatMember).filter(ChatMember.chat_id == chat_id).delete()
                # 删除聊天消息
                self.db.query(Message).filter(Message.chat_id == chat_id).delete()
                # 删除聊天
                self.db.delete(chat)
                self.db.commit()
                logger.info(f"聊天 {chat_id} 删除成功")
            else:
                logger.warning(f"未找到聊天 {chat_id}")
        except Exception as e:
            logger.error(f"删除聊天失败: {e}")
            self.db.rollback()

    async def update_chat_message(self, chat_id: int, message: str, sender_id: str):
        """添加新消息到数据库并更新聊天的最后消息"""
        try:
            # 创建新的消息记录
            new_message = Message(
                chat_id=chat_id,
                sender_id=sender_id,
                content=message,
                type="text",
                created_at=datetime.now()
            )
            self.db.add(new_message)
            
            # 更新聊天的最后消息
            chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.last_message = message
                chat.last_message_time = new_message.created_at
            
            self.db.commit()
            logger.debug(f"已添加新消息并更新聊天 {chat_id} 的最后消息")
            
            return new_message
            
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            self.db.rollback()
            return None

    async def get_chat_messages(self, chat_id: int, limit: int = 50) -> list:
        """获取聊天消息历史"""
        try:
            messages = (self.db.query(Message)
                       .filter(Message.chat_id == chat_id)
                       .order_by(Message.created_at.desc())
                       .limit(limit)
                       .all())
            logger.debug(f"获取聊天消息历史: {messages}")
            
            return [{
                'id': msg.id,
                'content': msg.content,
                'sender': {
                    'id': msg.sender.id,
                    'username': msg.sender.username,
                    'avatar': msg.sender.avatar
                },
                'timestamp': msg.created_at.isoformat(),
                'type': msg.type,
                'chatId': msg.chat_id,
            } for msg in messages]
        
        except Exception as e:
            logger.error(f"获取聊天消息失败: {e}", exc_info=True)
            return []

manager = ConnectionManager()

@app.websocket("/ws/{id}/{username}")
async def websocket_endpoint(websocket: WebSocket, id: str):
    username = manager.db.query(User).filter(User.id == id).first().username
    logger.info(f"收到来自用户 {username} 的WebSocket连接请求")
    client = None
    
    try:
        client = await manager.connect(websocket, username, id)
        if not client:
            logger.error(f"用户 {username} 连接失败")
            await websocket.close()
            return
        
        while True:
            try:
                data = await websocket.receive_json()
                await manager.handle_websocket_message(websocket, username, id, client, data)
                
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

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/user/info")
async def get_user_info(id: str, db: Session = Depends(get_db)):
    """获取用户信息"""
    logger.info(f"获取用户信息请求: {id}")
    
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": user.id,
            "username": user.username or "",    
            "background": user.background or "",
            "avatar": user.avatar or "",
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }

@app.post("/user/profile")
async def update_user_info(user_data: UserProfileUpdateData, db: Session = Depends(get_db)):
    """更新用户信息"""
    logger.info(f"更新用户信息请求: {user_data}")
    
    user = db.query(User).filter(User.id == user_data.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.username = user_data.username
    user.background = user_data.background
    db.commit()
    
    return {
        "code": 200,
        "message": "success",
    }

@app.get("/chats")
async def get_chats(user_id: str, db: Session = Depends(get_db)):
    """获取用户的聊天列表"""
    chat_members = db.query(ChatMember).filter(ChatMember.user_id == user_id).all()
    chats = []
    
    for member in chat_members:
        chat = member.chat
        chats.append({
            "id": chat.id,
            "name": chat.name,
            "type": chat.type,
            "avatar": chat.avatar,
            "last_message": chat.last_message,
            "last_message_time": chat.last_message_time.isoformat() if chat.last_message_time else None
        })
    
    return chats

@app.post("/messages")
async def save_message(chat_id: int, sender_id: str, content: str, db: Session = Depends(get_db)):
    """保存聊天消息"""
    message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        type="text"
    )
    
    db.add(message)
    
    # 更新聊天室最后消息
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        chat.last_message = content
        chat.last_message_time = datetime.now()
    
    db.commit()
    
    return {
        "code": 200,
        "message": "消息保存成功",
        "data": {
            "id": message.id,
            "content": message.content,
            "created_at": message.created_at.isoformat()
        }
    }

@app.get("/messages/{chat_id}")
async def get_messages(chat_id: int, limit: int = 50, before_id: int = None, db: Session = Depends(get_db)):
    """获取聊天记录"""
    query = db.query(Message).filter(Message.chat_id == chat_id)
    
    if before_id:
        query = query.filter(Message.id < before_id)
    
    messages = query.order_by(Message.id.desc()).limit(limit).all()
    
    return [
        {
            "id": msg.id,
            "sender": {
                "id": msg.sender.id,
                "username": msg.sender.username,
                "avatar": msg.sender.avatar
            },
            "content": msg.content,
            "type": msg.type,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]

@app.post("/api/claude")
async def claude_api(request: openai_Request):
    try:
        message_history = []
        for message in request.messages[-10:]:
            message_history.append(openai_message(role=message.role, content=message.content))
            
        response = client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=message_history,
            stream=False,
            max_tokens=1024
        )
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "content": response.choices[0].message.content
            }
        }
    except Exception as e:
        logger.error(f"Claude API 请求失败: {e}", exc_info=True)
        return {
            "code": 500,
            "message": str(e),
        }
        
if __name__ == "__main__":
    logger.info("=== FastAPI服务器启动 ===")
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run(app, host="127.0.0.1", port=8082)
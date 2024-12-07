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

from MODELS.models import UserProfileUpdateData

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
        self.db = SessionLocal()

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
                        
                        chat_id = message.get('chatId') or msg_data.get('chatId')
                        
                        await self.update_chat_message(chat_id, msg_data.get('content', ''))
                        
                        ws_message = {
                            'type': 'message',
                            'content': message.get('content', ''),
                            'sender': message.get('sender', username),
                            'timestamp': datetime.now().isoformat(),
                            'chatId': chat_id,
                            'isSelf': message.get('isSelf', False)
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

    async def update_chat_message(self, chat_id: int, message: str):
        """更新聊天的最后消息"""
        try:
            chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
            if chat:
                chat.last_message = message
                chat.last_message_time = datetime.now()
                self.db.commit()
                logger.debug(f"已更新聊天 {chat_id} 的最后消息")
        except Exception as e:
            logger.error(f"更新聊天消息失败: {e}")
            self.db.rollback()

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
    # 获取username by database
    username = manager.db.query(User).filter(User.id == id).first().username
    logger.info(f"收到来自用户 {username} 的WebSocket连接请求")
    client = None
    try:
        client = await manager.connect(websocket, username, id)
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
                elif data.get('type') == 'request_chat_messages':
                    logger.info(f"用户 {username} 请求聊天消息")
                    messages = await manager.get_chat_messages(data.get('chatId'), data.get('limit', 50))
                    await websocket.send_json({
                        'type': 'chat_messages',
                        'messages': messages
                    })
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
                # 直接更新数据库中的最后消息
                await manager.update_chat_message(chat_id, message['content'])
                
                # 发送消息到聊天服务器
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

if __name__ == "__main__":
    logger.info("=== FastAPI服务器启动 ===")
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run(app, host="127.0.0.1", port=8082)
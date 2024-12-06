from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 定义数据模型
class Chat(BaseModel):
    id: int
    name: str
    lastMessage: str
    time: str
    members: Optional[str] = None

class Message(BaseModel):
    content: str
    sender: str
    timestamp: str
    type: str  # 'message' | 'system'
    chatId: int
    isSelf: Optional[bool] = None

class UserProfileData(BaseModel):
    name: str
    background: str
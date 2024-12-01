from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    id:int
    content:str
    isSelf:bool
    createdAt:str

class Chat(BaseModel):
    id:int
    name:str
    lastMessage:str
    time:str
    members:str | None = None

class SendMessageData(BaseModel):
    chatId:int
    content:str
    isSelf:bool
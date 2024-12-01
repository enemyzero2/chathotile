from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from SERVER.chat_server import ChatServer
import threading
import time
from datetime import datetime
from MODELS.models import Message,Chat,SendMessageData

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

chat_server = ChatServer(host="127.0.0.1",port=8888)

threading.Thread(target=chat_server.start,daemon=True).start()

chat_history = {}

chat_rooms = {}

@app.get("/chats",response_model = List[Chat])
async def get_chats():
    return list(chat_rooms.values())

@app.get("/chats/{chat_id}/messages",response_model = List[Message])
async def get_messages(chat_id:int):
    return chat_history.get(chat_id,[])

@app.post("/messages",response_model = Message)
async def send_message(message_data:SendMessageData):
    new_message = Message(
        id = len(chat_history.get(message_data.chatId)) + 1,
        content = message_data.content,
        isSelf = message_data.isSelf,
        createdAt=datetime.now().isoformat()
    )

    if message_data.chatId not in chat_history:
        chat_history[message_data.chatId] = []
    chat_history[message_data.chatId].append(new_message)

    if message_data.chatId in chat_rooms:
        chat_rooms[message_data.chatId].lastMessage = message_data.content
        chat_rooms[message_data.chatId].time = datetime.now().isoformat()
    

    chat_server._broadcast({
        'type':'chat',
        'content': message_data.content,
        'chatId':message_data.chatId,
        'isSelf': message_data.isSelf
        
    })

    return new_message

if __name__ == "__main__":
    uvicorn.run(app,host="127.0.0.1",port=8081)
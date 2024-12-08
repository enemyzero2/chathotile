from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# 数据库连接配置
#DATABASE_URL = "postgresql://username:password@localhost:5432/chatdb"
# 或者使用 MySQL
DATABASE_URL = "mysql+pymysql://root:wdmzj67294381@10.129.169.123:3307/chatdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    background = Column(String(200))
    avatar = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    chats = relationship("ChatMember", back_populates="user")
    messages = relationship("Message", back_populates="sender")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    type = Column(String(20))  # group/private
    avatar = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    last_message = Column(Text)
    last_message_time = Column(DateTime)
    
    # 关系
    members = relationship("ChatMember", back_populates="chat")
    messages = relationship("Message", back_populates="chat")

class ChatMember(Base):
    __tablename__ = "chat_members"
    
    id = Column(String(50), primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    user_id = Column(String(50), ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.now)

    # 关系
    chat = relationship("Chat", back_populates="members")
    user = relationship("User", back_populates="chats")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(String(50), ForeignKey("users.id"))
    content = Column(Text)
    type = Column(String(20))  # text/image/system
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")

# 创建数据库表
Base.metadata.create_all(bind=engine) 
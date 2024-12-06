from SOCKET_API.MySocket import *
import json
import threading
import asyncio
from typing import Callable
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ChatClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        logger.info(f"初始化ChatClient - 主机: {host}, 端口: {port}")
        self.host = host
        self.port = port
        self.sock = None
        self.username = None
        self.running = False
        self.message_callback: Callable[[dict], None] = None
        self.send_lock = threading.Lock()
        self.loop = asyncio.get_event_loop()
        
    def connect(self, username: str):
        """连接到聊天服务器"""
        logger.info(f"尝试连接到聊天服务器 - 用户: {username}")
        try:
            logger.debug("初始化Winsock")
            initialize_winsock()
            
            logger.debug("创建socket")
            self.sock = create_socket(2, 1, 0)
            
            logger.debug(f"连接到服务器 {self.host}:{self.port}")
            connect_socket(self.sock, (self.host, self.port), 16)
            
            self.username = username
            self.running = True
            
            logger.debug("创建新的事件循环")
            self.loop = asyncio.new_event_loop()
            
            # 发送登录消息
            login_message = {
                'type': 'login',
                'content': username
            }
            logger.info(f"发送登录消息: {login_message}")
            self._send_message(login_message)
            
            # 启动接收消息的线程
            logger.debug("启动消息接收线程")
            receive_thread = threading.Thread(
                target=self._run_async_loop,
                args=(self.loop,),
                daemon=True
            )
            receive_thread.start()
            
            logger.info(f"用户 {username} 成功连接到服务器")
            return True
            
        except Exception as e:
            logger.error(f"连接服务器失败: {e}", exc_info=True)
            self.disconnect()
            return False
            
    def send_message(self, content: str):
        """发送聊天消息"""
        logger.debug(f"准备发送消息: {content}")
        message = {
            'type': 'message',  # 改为 'message' 以匹配服务器端
            'content': content
        }
        self._send_message(message)
        
    def _send_message(self, message: dict):
        """发送消息到服务器"""
        try:
            with self.send_lock:
                logger.debug(f"序列化消息: {message}")
                message_bytes = json.dumps(message).encode('utf-8')
                length = len(message_bytes)
                length_bytes = length.to_bytes(4, byteorder='big')
                
                logger.debug(f"发送消息长度: {length} 字节")
                send_socket(self.sock, length_bytes, 4, 0)
                
                logger.debug("发送消息内容")
                send_socket(self.sock, message_bytes, length, 0)
                
                logger.debug("消息发送完成")
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            
    def _run_async_loop(self, loop):
        """在独立线程中运行事件循环"""
        logger.debug("设置事件循环")
        asyncio.set_event_loop(loop)
        logger.debug("启动事件循环")
        loop.run_until_complete(self._receive_messages())
            
    async def _receive_messages(self):
        """异步接收服务器消息"""
        logger.info("开始接收消息循环")
        while self.running:
            try:
                logger.debug("等待接收数据...")
                data = recv_socket(self.sock, 1024, 0)
                if not data:
                    logger.warning("接收到空数据，连接可能已断开")
                    break
                    
                logger.debug(f"接收到原始数据: {data}")
                message = json.loads(data.decode('utf-8'))
                logger.debug(f"解析后的消息: {message}")
                
                if self.message_callback:
                    logger.debug("执行消息回调")
                    if asyncio.iscoroutinefunction(self.message_callback):
                        await self.message_callback(message)
                    else:
                        await self.loop.run_in_executor(None, self.message_callback, message)
                    
            except Exception as e:
                logger.error(f"接收消息失败: {e}", exc_info=True)
                break
                
        logger.info("消息接收循环结束，准备断开连接")
        self.disconnect()
        
    def set_message_callback(self, callback: Callable[[dict], None]):
        """设置消息处理回调函数"""
        logger.info("设置消息回调函数")
        self.message_callback = callback
        
    def disconnect(self):
        """断开与服务器的连接"""
        if not self.running:
            logger.debug("客户端已经断开，跳过断开操作")
            return
            
        logger.info(f"开始断开用户 {self.username} 的连接")
        try:
            if self.sock:
                logout_message = {
                    'type': 'logout',
                    'content': self.username
                }
                logger.info(f"发送登出消息: {logout_message}")
                self._send_message(logout_message)
        except Exception as e:
            logger.error(f"发送登出消息失败: {e}", exc_info=True)
        
        self.running = False
        
        if self.loop:
            logger.debug("关闭事件循环")
            try:
                self.loop.stop()
                self.loop.close()
            except Exception as e:
                logger.error(f"关闭事件循环失败: {e}", exc_info=True)
            self.loop = None
            
        if self.sock:
            logger.debug("关闭socket连接")
            try:
                close_socket(self.sock)
            except Exception as e:
                logger.error(f"关闭socket失败: {e}", exc_info=True)
            self.sock = None
            
        logger.debug("清理Winsock")
        cleanup_winsock()
        logger.info("连接断开完成")
        
from SOCKET_API.MySocket import *
import json
import threading
from typing import Callable

class ChatClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.sock = None
        self.username = None
        self.running = False
        self.message_callback: Callable[[dict], None] = None
        self.send_lock = threading.Lock()
        
    def connect(self, username: str):
        """连接到聊天服务器"""
        try:
            initialize_winsock()
            self.sock = create_socket(2, 1, 0)
            connect_socket(self.sock, (self.host, self.port), 16)
            self.username = username
            self.running = True
            
            # 发送登录消息
            self._send_message({
                'type': 'login',
                'content': username
            })
            
            # 启动接收消息的线程
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"连接服务器失败: {e}")
            self.disconnect()
            return False
            
    def send_message(self, content: str):
        """发送聊天消息"""
        self._send_message({
            'type': 'chat',
            'content': content
        })
        
    def _send_message(self, message: dict):
        """发送消息到服务器"""
        try:
            with self.send_lock:
                message_bytes = json.dumps(message).encode('utf-8')
                length = len(message_bytes)
                length_bytes = length.to_bytes(4, byteorder='big')
                
                send_socket(self.sock, length_bytes, 4, 0)
                send_socket(self.sock, message_bytes, length, 0)
                
        except Exception as e:
            print(f"发送消息失败: {e}")
            
    def _receive_messages(self):
        """接收服务器消息"""
        while self.running:
            try:
                data = recv_socket(self.sock, 1024, 0)
                if not data:
                    break
                    
                message = json.loads(data.decode('utf-8'))
                if self.message_callback:
                    self.message_callback(message)
                    
            except Exception as e:
                print(f"接收消息失败: {e}")
                break
                
        self.disconnect()
        
    def set_message_callback(self, callback: Callable[[dict], None]):
        """设置消息处理回调函数"""
        self.message_callback = callback
        
    def disconnect(self):
        """断开与服务器的连接"""
        if not self.running:  # 避免重复断开连接
            return
            
        try:
            # 首先发送登出消息
            if self.sock:
                self._send_message({
                    'type': 'logout',
                    'content': self.username
                })
        except Exception as e:
            print(f"发送登出消息失败: {e}")
        
        # 然后设置运行状态为False
        self.running = False
        
        # 最后关闭socket
        if self.sock:
            try:
                close_socket(self.sock)
            except Exception as e:
                print(f"关闭socket失败: {e}")
            self.sock = None
            
        cleanup_winsock() 
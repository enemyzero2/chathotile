from MySocket import *
from typing import Dict, Set
import json
import threading

class ChatServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.server_sock = None
        self.clients: Dict[int, tuple[str, int]] = {}  # socket_fd -> (ip, port)
        self.usernames: Dict[int, str] = {}  # socket_fd -> username
        self.running = False
        
    def start(self):
        """启动聊天服务器"""
        try:
            initialize_winsock()
            self.server_sock = create_socket(2, 1, 0)
            server_addr = SockAddr_in(self.port, self.host)
            bind_socket(self.server_sock, server_addr, 16)
            listen_socket(self.server_sock, 5)
            self.running = True
            
            print(f"聊天服务器启动在 {self.host}:{self.port}")
            
            # 启动接受连接的线程
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.start()
            
        except Exception as e:
            print(f"服务器启动失败: {e}")
            self.stop()
            
    def _accept_connections(self):
        """处理新的客户端连接"""
        while self.running:
            try:
                client_sock, client_addr = accept_socket(self.server_sock, (self.host, self.port), 16)
                self.clients[client_sock] = client_addr
                
                # 为每个客户端启动一个处理线程
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock,))
                client_thread.start()
                
            except Exception as e:
                print(f"接受连接失败: {e}")
                
    def _handle_client(self, client_sock: int):
        """处理客户端消息"""
        client_addr = self.clients.get(client_sock, ('未知', 0))
        username = self.usernames.get(client_sock, '未知用户')
        
        try:
            while self.running:
                try:
                    # 先读取消息长度（4字节）
                    length_bytes = recv_socket(client_sock, 4, 0)
                    if not length_bytes:
                        print(f"客户端 {username}({client_addr[0]}:{client_addr[1]}) 断开连接")
                        break
                    
                    message_length = int.from_bytes(length_bytes, byteorder='big')
                    
                    # 根据长度读取完整消息
                    data = recv_socket(client_sock, message_length, 0)
                    if not data:
                        print(f"客户端 {username}({client_addr[0]}:{client_addr[1]}) 断开连接")
                        break
                    
                    try:
                        decoded_data = data.decode('utf-8')
                        message = json.loads(decoded_data)
                        self._process_message(client_sock, message)
                    except UnicodeDecodeError as e:
                        print(f"解码消息失败 - 客户端 {username}: {e}")
                        print(f"原始数据: {data}")
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败 - 客户端 {username}: {e}")
                        print(f"收到的数据: {decoded_data}")
                        
                except Exception as e:
                    print(f"接收消息失败 - 客户端 {username}({client_addr[0]}:{client_addr[1]}): {e}")
                
        except Exception as e:
            print(f"处理客户端 {username}({client_addr[0]}:{client_addr[1]}) 时发生错误: {e}")
            
        finally:
            print(f"清理客户端 {username}({client_addr[0]}:{client_addr[1]}) 的连接")
            self._remove_client(client_sock)
            
    def _process_message(self, client_sock: int, message: dict):
        """处理不同类型的消息"""
        msg_type = message.get('type')
        content = message.get('content')
        
        if msg_type == 'login':
            self.usernames[client_sock] = content
            self._broadcast({
                'type': 'system',
                'content': f"{content} 加入了聊天室"
            }, exclude=None)
            
        elif msg_type == 'chat':
            username = self.usernames.get(client_sock, '未知用户')
            self._broadcast({
                'type': 'chat',
                'sender': username,
                'content': content
            }, exclude=None)
            
    def _broadcast(self, message: dict, exclude: int = None):
        """广播消息给所有客户端"""
        message_bytes = json.dumps(message).encode('utf-8')
        for client_fd in self.clients:
            if client_fd != exclude:
                try:
                    send_socket(client_fd, message_bytes, len(message_bytes), 0)
                except Exception as e:
                    print(f"发送消息到客户端失败: {e}")
                    
    def _remove_client(self, client_sock: int):
        """移除断开连接的客户端"""
        username = self.usernames.get(client_sock)
        if username:
            self._broadcast({
                'type': 'system',
                'content': f"{username} 离开了聊天室"
            }, exclude=client_sock)
            
        if client_sock in self.clients:
            del self.clients[client_sock]
        if client_sock in self.usernames:
            del self.usernames[client_sock]
        close_socket(client_sock)
        
    def stop(self):
        """停止聊天服务器"""
        self.running = False
        if self.server_sock:
            close_socket(self.server_sock)
        cleanup_winsock() 
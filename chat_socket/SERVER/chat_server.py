from SOCKET_API.MySocket import *
from typing import Dict, Set, List
import json
import threading
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        logger.info(f"初始化聊天服务器 - 主机: {host}, 端口: {port}")
        self.host = host
        self.port = port
        self.server_sock = None
        self.clients: Dict[int, tuple[str, int]] = {}  # socket_fd -> (ip, port)
        self.usernames: Dict[int, str] = {}  # socket_fd -> username
        self.running = False
        self.current_client_sock_num = None
        self.current_client_count = 0
        logger.debug("聊天服务器初始化完成")
        
    def start(self):
        """启动聊天服务器"""
        try:
            logger.info("正在启动聊天服务器...")
            logger.debug("初始化Winsock")
            initialize_winsock()
            
            logger.debug("创建服务器socket")
            self.server_sock = create_socket(2, 1, 0)
            
            logger.debug(f"绑定地址 {self.host}:{self.port}")
            server_addr = SockAddr_in(self.port, self.host)
            bind_socket(self.server_sock, server_addr, 16)
            
            logger.debug("开始监听连接")
            listen_socket(self.server_sock, 5)
            self.running = True
            
            logger.info(f"聊天服务器启动成功 - 监听地址: {self.host}:{self.port}")
            
            # 启动接受连接的线程
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.start()
            logger.debug("连接接收线程已启动")
            
        except Exception as e:
            logger.error(f"服务器启动失败: {e}", exc_info=True)
            self.stop()
            
    def _accept_connections(self):
        """处理新的客户端连接"""
        logger.info("开始接受客户端连接")
        while self.running:
            try:
                logger.debug("等待新的客户端连接...")
                client_sock, client_addr = accept_socket(self.server_sock, (self.host, self.port), 16)
                self.clients[client_sock] = client_addr
                self.current_client_count += 1
                
                logger.info(f"新客户端连接: {client_addr[0]}:{client_addr[1]} (总连接数: {self.current_client_count})")
                
                # 为每个客户端启动一个处理线程
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock,))
                client_thread.start()
                logger.debug(f"已为客户端 {client_addr[0]}:{client_addr[1]} 创建处理线程")
                
            except Exception as e:
                logger.error(f"接受连接失败: {e}", exc_info=True)
                
    def _handle_client(self, client_sock: int):
        """处理客户端消息"""
        if self.current_client_count <= 0:
            logger.warning("没有活动的客户端连接")
            return
            
        client_addr = self.clients.get(client_sock, ('未知', 0))
        username = self.usernames.get(client_sock, '未知用户')
        logger.info(f"开始处理客户端 {username}({client_addr[0]}:{client_addr[1]}) 的消息")
        
        try:
            while self.running:
                try:
                    logger.debug(f"等待客户端 {username} 的消息...")
                    # 先读取消息长度（4字节）
                    length_bytes = recv_socket(client_sock, 4, 0)
                    if not length_bytes:
                        logger.info(f"客户端 {username}({client_addr[0]}:{client_addr[1]}) 断开连接")
                        break
                    
                    message_length = int.from_bytes(length_bytes, byteorder='big')
                    logger.debug(f"收到消息长度: {message_length} 字节")
                    
                    # 根据长度读取完整消息
                    data = recv_socket(client_sock, message_length, 0)
                    if not data:
                        logger.info(f"客户端 {username}({client_addr[0]}:{client_addr[1]}) 断开连接")
                        break
                    
                    try:
                        decoded_data = data.decode('utf-8')
                        logger.debug(f"收到原始消息: {decoded_data}")
                        message = json.loads(decoded_data)
                        logger.debug(f"解析后的消息: {message}")
                        self._process_message(client_sock, message)
                    except UnicodeDecodeError as e:
                        logger.error(f"解码消息失败 - 客户端 {username}: {e}")
                        logger.error(f"原始数据: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败 - 客户端 {username}: {e}")
                        logger.error(f"收到的数据: {decoded_data}")
                        
                except Exception as e:
                    logger.error(f"接收消息失败 - 客户端 {username}({client_addr[0]}:{client_addr[1]}): {e}", exc_info=True)
                    break
                
        except Exception as e:
            logger.error(f"处理客户端 {username}({client_addr[0]}:{client_addr[1]}) 时发生错误: {e}", exc_info=True)
            
        finally:
            logger.info(f"清理客户端 {username}({client_addr[0]}:{client_addr[1]}) 的连接")
            self._remove_client(client_sock)
            
    def _process_message(self, client_sock: int, message: dict):
        """处理不同类型的消息"""
        msg_type = message.get('type')
        content = message.get('content')
        username = self.usernames.get(client_sock, '未知用户')
        
        logger.debug(f"处理消息 - 类型: {msg_type}, 发送者: {username}")
        
        if msg_type == 'login':
            self.usernames[client_sock] = content
            logger.info(f"用户 {content} 登录成功")
            self._broadcast({
                'type': 'system',
                'content': f"{content} 加入了聊天室"
            }, exclude=None)
            
        elif msg_type == 'message':
            try:
                # 解析content中的JSON字符串
                if isinstance(content, str):
                    msg_data = json.loads(content)
                else:
                    msg_data = content
                    
                logger.debug(f"收到聊天消息 - 发送者: {username}, 内容: {msg_data}")
                
                # 构建消息对象
                broadcast_message = {
                    'type': 'message',
                    'content': msg_data.get('content'),
                    'sender': username,
                    'chatId': msg_data.get('chatId', 1),
                    'timestamp': datetime.now().isoformat(),
                    'isSelf': False
                }
                
                # 给其他用户发送 isSelf=False 的消息
                self._broadcast(broadcast_message, exclude=client_sock)
                
                # 给发送者的消息设置 isSelf=True
                broadcast_message['isSelf'] = True
                self._broadcast(broadcast_message, include=[client_sock])
                
            except json.JSONDecodeError as e:
                logger.error(f"解析消息内容失败: {e}")
                logger.error(f"原始内容: {content}")
                
        elif msg_type == 'logout':
            logger.info(f"用户 {username} 请求登出")
            self._broadcast({
                'type': 'system',
                'content': f"{username} 离开了聊天室"
            }, exclude=None)
            self._remove_client(client_sock)
            
    def _broadcast(self, message: dict, exclude: int = None, include: List[int] = None):
        """广播消息给指定的客户端"""
        logger.debug(f"广播消息: {message}")
        message_bytes = json.dumps(message).encode('utf-8')
        
        if include:
            # 只发送给指定的客户端
            clients = include
        else:
            # 发送给所有客户端，除了exclude
            clients = [fd for fd in self.clients if fd != exclude]
        
        for client_fd in clients:
            try:
                logger.debug(f"发送消息到客户端 {self.usernames.get(client_fd, '未知用户')}")
                send_socket(client_fd, message_bytes, len(message_bytes), 0)
            except Exception as e:
                logger.error(f"发送消息到客户端失败: {e}", exc_info=True)
                    
    def _remove_client(self, client_sock: int):
        """移除断开连接的客户端"""
        if client_sock not in self.clients:
            logger.debug(f"客户端 {client_sock} 已经被移除")
            return
            
        try:
            username = self.usernames.get(client_sock, str(client_sock))
            logger.info(f"移除客户端 {username}")
            
            # 广播用户离开消息
            self._broadcast({
                'type': 'system',
                'content': f"{username} 离开了聊天室"
            }, exclude=client_sock)
            
            # 移除客户端信息
            if client_sock in self.clients:
                del self.clients[client_sock]
            if client_sock in self.usernames:
                del self.usernames[client_sock]
                
            self.current_client_count = max(0, len(self.clients))  # 确保不会小于0
            logger.debug(f"当前连接数: {self.current_client_count}")
            
            # 尝试关闭socket
            try:
                close_socket(client_sock)
            except OSError as e:
                if "10038" in str(e):  # socket已关闭
                    logger.debug(f"socket {client_sock} 已经关闭")
                else:
                    logger.warning(f"关闭socket {client_sock} 失败: {e}")
                    
        except Exception as e:
            logger.error(f"移除客户端时出错: {e}", exc_info=True)
        
    def stop(self):
        """停止聊天服务器"""
        logger.info("正在停止聊天服务器...")
        self.running = False
        if self.server_sock:
            close_socket(self.server_sock)
        cleanup_winsock()
        logger.info("聊天服务器已停止") 
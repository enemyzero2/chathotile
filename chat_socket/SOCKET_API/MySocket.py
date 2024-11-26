#实现socket的六大基本API，基于windows内核
import ctypes
import struct
from typing import Tuple

# Windows socket库
ws2_32 = ctypes.windll.ws2_32

def initialize_winsock():
    """初始化Winsock"""
    # 创建WSADATA结构体
    WSADATA = ctypes.create_string_buffer(408)
    # 初始化Winsock (版本2.2)
    ret = ws2_32.WSAStartup(0x202, WSADATA)
    if ret != 0:
        raise OSError(f"WSAStartup失败: {ret}")

def cleanup_winsock():
    """清理Winsock"""
    ws2_32.WSACleanup()

def create_socket(domain: int, type: int, protocol: int) -> int:
    """创建一个新的socket对象
    
    Args:
        domain (int): 协议族
            - PF_INET(2): IPv4网络协议
        type (int): Socket类型
            - SOCK_STREAM(1): TCP流式套接字
            - SOCK_DGRAM(2): UDP数据报套接字
        protocol (int): 传输协议
            - 0: 使用默认协议
    
    Returns:
        socket.socket: 返回创建的socket对象
        
    Raises:
        socket.error: 创建socket失败时抛出异常
    """
    sockfd = ws2_32.socket(domain, type, protocol)
    if sockfd == -1:
        raise OSError("创建socket失败")
    return sockfd

def connect_socket(sockfd: int, server_addr: tuple[str,int], sockaddr_len: int):
    """连接到服务器

    Args:
        sockfd (int): socket描述符
        server_addr (tuple[str,int]): 服务器地址(ip,port)
        sockaddr_len (int): 地址长度
    """
    addr = _pack_sockaddr_in(server_addr[0], server_addr[1])
    result = ws2_32.connect(sockfd, addr, sockaddr_len)
    if result == -1:
        error_code = ws2_32.WSAGetLastError()
        error_msg = {
            10061: "连接被拒绝。目标服务器可能未启动或端口未开放"
        }.get(error_code, f"未知错误")
        
        raise OSError(f"连接失败 - 错误码 {error_code}: {error_msg}")
    return result

def send_socket(sockfd: int, data: bytes, data_len: int, flags: int):
    """发送数据
    Args:
        sockfd (int): socket描述符
        data (bytes): 发送的数据
        data_len (int): 数据长度
        flags (int): 标志位
    """
    bytes_sent = ws2_32.send(sockfd, data, data_len, flags)
    if bytes_sent == -1:
        raise OSError("发送数据失败")
    return bytes_sent

def send_to_socket(sockfd: int, data: bytes, data_len: int, flags: int, server_addr: tuple[str,int], sockaddr_len: int):
    """发送数据到指定地址
    Args:
        sockfd (int): socket描述符
        data (bytes): 发送的数据
        data_len (int): 数据长度
        flags (int): 标志位
        server_addr (tuple[str,int]): 服务器地址(ip,port)
        sockaddr_len (int): 地址长度
    """
    addr = _pack_sockaddr_in(server_addr[0], server_addr[1])
    bytes_sent = ws2_32.sendto(sockfd, data, data_len, flags, addr, sockaddr_len)
    if bytes_sent == -1:
        raise OSError("发送数据失败")
    return bytes_sent

def recv_socket(sockfd: int, bufsize: int, flags: int):
    """接收数据
    Args:
        sockfd (int): socket描述符
        bufsize (int): 缓冲区大小
        flags (int): 标志位
    """
    buffer = ctypes.create_string_buffer(bufsize)
    bytes_received = ws2_32.recv(sockfd, buffer, bufsize, flags)
    if bytes_received == -1:
        raise OSError("接收数据失败")
    return buffer.raw[:bytes_received]

def recvfrom_socket(sockfd: int, bufsize: int, flags: int, server_addr: tuple[str,int], sockaddr_len: int):
    """接收数据并返回地址
    Args:
        sockfd (int): socket描述符
        bufsize (int): 缓冲区大小
        flags (int): 标志位
        server_addr (tuple[str,int]): 服务器地址(ip,port)
        sockaddr_len (int): 地址长度
    """
    buffer = ctypes.create_string_buffer(bufsize)
    addr = _pack_sockaddr_in("0.0.0.0", 0)
    addr_len = ctypes.c_int(sockaddr_len)
    bytes_received = ws2_32.recvfrom(sockfd, buffer, bufsize, flags, addr, ctypes.byref(addr_len))
    if bytes_received == -1:
        raise OSError("接收数据失败")
    client_addr = _unpack_sockaddr_in(addr)
    return buffer.raw[:bytes_received], client_addr

#定义sockaddr_in结构体
class SockAddr_in:
    """Socket地址结构体
    
    Attributes:
        地址族默认IPv4
        sin_port (int): 端口号(网络字节序)
        sin_addr (str): IP地址
    """
    def __init__(self, port: int, addr: str):
        self.sin_port = port
        self.sin_addr = addr

def bind_socket(sockfd: int, server_addr: SockAddr_in, sockaddr_len: int):
    """将socket绑定到指定地址和端口

    Args:
        sockfd (int): socket描述符
        server_addr (SockAddr_in): 服务器地址(ip,port)
        sockaddr_len (int): 地址结构长度
        IPV4地址结构长度是16
        
    Raises:
        socket.error: 绑定失败时抛出异常，包含具体的错误码和描述
    """
    addr = _pack_sockaddr_in(server_addr.sin_addr, server_addr.sin_port)
    result = ws2_32.bind(sockfd, addr, sockaddr_len)
    if result == -1:
        error_code = ws2_32.WSAGetLastError()
        error_msg = {
            10013: "权限不足。尝试使用管理员权限运行或使用大于1024的端口",
            10048: "地址已被使用。该端口可能已经被其他程序占用",
            10049: "请求的地址无法分配给该主机",
            10022: "参数无效。请检查地址格式是否正确",
            10047: "地址族不支持。请检查地址族是否正确"
        }.get(error_code, f"未知错误")
        
        raise OSError(f"绑定失败 - 错误码 {error_code}: {error_msg}")
    return result

def listen_socket(sockfd: int, input_queue_size: int):
    """
    for server
    面向连接的套接字使用它将一个套接字置为被动模式，并准备接收传入连接。用于服务器，指明某个套接字连接是被动的

    Args:
        sockfd (int): socket描述符
        input_queue_size (int): 指定输入队列大小
    """
    result = ws2_32.listen(sockfd, input_queue_size)
    if result == -1:
        raise OSError("监听失败")
    return result

def accept_socket(sockfd: int, server_addr: tuple[str,int], sockaddr_len: int):
    """
    接受传入连接

    Args:
        sockfd (int): socket描述符
        server_addr (tuple[str,int]): 服务器地址(ip,port)
        sockaddr_len (int): 地址长度
    """
    addr = _pack_sockaddr_in("0.0.0.0", 0)
    addr_len = ctypes.c_int(sockaddr_len)
    new_fd = ws2_32.accept(sockfd, addr, ctypes.byref(addr_len))
    if new_fd == -1:
        raise OSError("接受连接失败")
    client_addr = _unpack_sockaddr_in(addr)
    return new_fd, client_addr

def close_socket(sockfd: int):
    """关闭socket
    如果只有一个进程使用，立即终止连接并撤销该套接字，如果多个进程共享该套接字，将引用数减一，如果引用数降到零，则撤销它。

    Args:
        sockfd (int): socket描述符
    """
    result = ws2_32.closesocket(sockfd)
    if result == -1:
        raise OSError("关闭socket失败")
    return result

def _pack_sockaddr_in(ip: str, port: int) -> bytes:
    """将IP地址和端口打包成sockaddr_in结构体"""
    ip_bytes = bytes(map(int, ip.split('.')))
    port_bytes = struct.pack('!H', port)
    family = struct.pack('<H', 2)  # AF_INET = 2, 使用小端序 '<H'
    return family + port_bytes + ip_bytes + b'\x00' * 8

def _unpack_sockaddr_in(addr: bytes) -> tuple[str, int]:
    """从sockaddr_in结构体解析出IP地址和端口
    
    Args:
        addr (bytes): sockaddr_in结构体的字节数据
        
    Returns:
        tuple[str, int]: 返回(ip地址, 端口号)的元组
    """
    family = struct.unpack('<H', addr[:2])[0]  # 地址族使用小端序
    port = struct.unpack('!H', addr[2:4])[0]   # 端口仍然使用网络字节序
    ip = '.'.join(str(b) for b in addr[4:8])
    return (ip, port)





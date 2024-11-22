from MySocket import *

def main():
    server_sock = None
    client_sock = None
    try:
        # 初始化Winsock
        initialize_winsock()
        
        # 创建TCP socket
        server_sock = create_socket(2, 1, 0)  # PF_INET=2, SOCK_STREAM=1
        
        # 绑定地址和端口
        server_addr = SockAddr_in(8888, "127.0.0.1")
        bind_socket(server_sock, server_addr, 16)  # 16是sockaddr_in结构体的大小
        
        # 监听连接
        listen_socket(server_sock, 5)
        print("服务器启动，等待连接...")
        
        # 接受客户端连接
        client_sock, client_addr = accept_socket(server_sock, ("127.0.0.1", 8888), 16)
        print(f"客户端{client_addr}已连接")
        
        while True:
            # 接收数据
            data = recv_socket(client_sock, 1024, 0)
            if not data:
                break
                
            try:
                message = data.decode('utf-8')
                print(f"收到消息: {message}")
                
                # 发送响应
                response = f"服务器已收到消息: {message}"
                send_socket(client_sock, response.encode('utf-8'), len(response), 0)
            except UnicodeDecodeError:
                print(f"收到无效的数据格式: {data!r}")
                response = "错误：收到的数据不是有效的UTF-8编码"
                send_socket(client_sock, response.encode('utf-8'), len(response), 0)
                
    finally:
        # 关闭连接
        if client_sock:
            close_socket(client_sock)
        if server_sock:
            close_socket(server_sock)
        # 清理Winsock
        cleanup_winsock()

if __name__ == "__main__":
    main() 
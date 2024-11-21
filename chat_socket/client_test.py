from MySocket import *
import time

def main():
    # 创建TCP socket
    initialize_winsock()
    client_sock = create_socket(2, 1, 0)  # PF_INET=2, SOCK_STREAM=1
    
    # 连接服务器
    connect_socket(client_sock, ("127.0.0.1", 8888), 16)
    print("已连接到服务器")
    
    try:
        # 发送消息
        message = "你好，服务器！"
        send_socket(client_sock, message.encode('utf-8'), len(message), 0)
        
        # 接收响应
        response = recv_socket(client_sock, 1024, 0)
        print(f"服务器响应: {response.decode('utf-8')}")
        
    finally:
        # 关闭连接
        close_socket(client_sock)
        cleanup_winsock()

if __name__ == "__main__":
    main() 
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
        message_bytes = message.encode('utf-8')
        total_sent = 0
        while total_sent < len(message_bytes):
            sent = send_socket(client_sock, message_bytes[total_sent:], 
                             len(message_bytes) - total_sent, 0)
            total_sent += sent
        
        # 接收响应
        response = recv_socket(client_sock, 1024, 0)
        try:
            decoded_response = response.decode('utf-8')
            print(f"服务器响应: {decoded_response}")
        except UnicodeDecodeError:
            print(f"服务器响应(原始字节): {response}")
        
    finally:
        # 关闭连接
        close_socket(client_sock)
        cleanup_winsock()

if __name__ == "__main__":
    main() 
import chat_client
import time

def message_handler(message):
    """处理接收到的消息"""
    if message['type'] == 'chat':
        print(f"收到消息: {message['content']}")
    elif message['type'] == 'system':
        print(f"系统消息: {message['content']}")

def main():
    # 创建客户端实例
    client = chat_client.ChatClient()
    
    # 设置消息处理回调
    client.set_message_callback(message_handler)
    
    # 连接到服务器
    if client.connect("测试用户"):
        print("成功连接到服务器！")
        
        try:
            # 使用命令行输入消息
            while True:
                message = input("输入消息: ")
                client.send_message(message)
            
            # 保持程序运行一段时间以接收消息
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n正在断开连接...")
            client.disconnect()
    else:
        print("连接服务器失败！")

if __name__ == "__main__":
    main()
    

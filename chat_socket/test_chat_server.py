import chat_server
import time 
def main():
    server = chat_server.ChatServer()
    try:
        server.start()
        print("服务器启动成功")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("服务器已停止")

if __name__ == "__main__":
    main()

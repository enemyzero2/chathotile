from SERVER.chat_server import ChatServer
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("正在初始化聊天服务器...")
    chat_server = ChatServer(host="127.0.0.1", port=8888)
    
    try:
        logger.info("正在启动聊天服务器...")
        chat_server.start()
        logger.info("聊天服务器启动成功")
    except KeyboardInterrupt:
        logger.warning("\n检测到键盘中断，正在关闭服务器...")
        chat_server.stop()
        logger.info("服务器已安全关闭")
    except Exception as e:
        logger.error(f"服务器运行出错: {e}", exc_info=True)
        chat_server.stop()
        logger.info("服务器已关闭")

if __name__ == "__main__":
    logger.info("=== 聊天服务器程序启动 ===")
    main()

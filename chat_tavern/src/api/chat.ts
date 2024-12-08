export interface Chat {
  id: number
  name: string
  lastMessage: string
  time: string
  members?: string
}

export interface Message {
  content: string
  sender: string
  timestamp: string
  type: 'message' | 'system'
  chatId: number
  isSelf?: boolean
}

export interface SendMessageData {
  chatId: number
  content: string
  isSelf: boolean
}


// 添加 WebSocket 客户端
export class WebSocketClient {
  private ws: WebSocket | null = null
  
  connect(id: string, username: string) {
    this.ws = new WebSocket(`ws://127.0.0.1:8082/ws/${id}/${username}`)
    
    this.ws.onopen = () => {
      console.log('WebSocket连接成功')
      this.requestChatList()
    }
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      // 处理不同类型的消息
      switch(data.type) {
        case 'chat_list':
          // 触发聊天室列表更新事件
          window.dispatchEvent(new CustomEvent('chat-list', { 
            detail: data.chats as Chat[]
          }))
          break
          
        case 'message':
          const message: Message = {
            content: data.content,
            sender: data.sender,
            timestamp: new Date(data.timestamp).toLocaleTimeString(),
            type: data.type,
            chatId: data.chatId,
            isSelf: data.isSelf
          }
          window.dispatchEvent(new CustomEvent('chat-message', { detail: message }))
          break

        case 'chat_messages':
          const messages: Message[] = data.messages.map((msg: any) => ({
            content: msg.content,
            sender: msg.sender.username,
            timestamp: new Date(msg.timestamp).toLocaleTimeString(),
            type: msg.type,
            chatId: msg.chatId,
            isSelf: msg.sender.id === localStorage.getItem('userId')
          }))
          window.dispatchEvent(new CustomEvent('chat-messages', { 
            detail: messages 
          }))
          break
      }
    }

    this.ws.onerror = () => {
      window.dispatchEvent(new CustomEvent('ws-error'))
    }
  }
  
  // 请求聊天室列表
  requestChatList() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'request_chat_list'
      }))
    }
  }

  requestChatMessages(chatId: number) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'request_chat_messages',
        chatId
      }))
    }
  }
  
  sendMessage(content: string, chatId: number) {
    if (this.ws?.readyState === WebSocket.OPEN && content.trim() !== '') {
      const message = {
        type: 'message',
        content,
        chatId,
      }
      this.ws.send(JSON.stringify(message))
    }
  }
  sendClaudeMessage(content: string, chatId: number) {
    if (this.ws?.readyState === WebSocket.OPEN && content.trim() !== '') {
      const message = {
        type: 'claude_message',
        content,
        chatId,
      }
      this.ws.send(JSON.stringify(message))
    }
  }
  
  close() {
    this.ws?.close()
  }
} 
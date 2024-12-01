import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8081'
})

export interface Chat {
  id: number
  name: string
  lastMessage: string
  time: string
  members?: string
}

export interface Message {
  id: number
  content: string
  isSelf: boolean
  createdAt: string
}

export interface SendMessageData {
  chatId: number
  content: string
  isSelf: boolean
}

export const chatApi = {
  // 获取聊天列表
  getChats() {
    return api.get<Chat[]>('/chats')
  },

  // 获取指定聊天的消息记录
  getChatMessages(chatId: number) {
    return api.get<Message[]>(`/chats/${chatId}/messages`)
  },

  // 发送消息
  sendMessage(data: SendMessageData) {
    return api.post<Message>('/messages', data)
  }
} 
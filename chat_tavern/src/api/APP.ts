import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8082'
})

export interface InitClientResponse {
  status: string
  message: string
}

export const appApi = {
  // 初始化聊天客户端
  initChatClient() {
    return api.post<InitClientResponse>('/init-client')
  },

  // 关闭聊天客户端连接
  closeChatClient() {
    return api.post<InitClientResponse>('/close-client')
  }
}



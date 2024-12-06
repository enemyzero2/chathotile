import { defineStore } from 'pinia'
import { WebSocketClient } from '../api/chat'

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    wsClient: new WebSocketClient(),
    isConnected: false
  }),

  actions: {
    connect(deviceId: string) {
      console.log('WebSocket Store: 尝试连接', { deviceId })
      
      if (!this.isConnected) {
        console.log('WebSocket Store: 建立新连接')
        this.wsClient.connect(deviceId)
        this.isConnected = true
      } else {
        console.log('WebSocket Store: 已存在连接，跳过')
      }
    },

    disconnect() {
      console.log('WebSocket Store: 尝试断开连接')
      
      if (this.isConnected) {
        console.log('WebSocket Store: 关闭连接')
        this.wsClient.close()
        this.isConnected = false
      } else {
        console.log('WebSocket Store: 连接已关闭，跳过')
      }
    }
  }
}) 
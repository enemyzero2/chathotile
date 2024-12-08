<template>
  <div v-if="loading || showError" class="fixed inset-0 z-50 backdrop-blur-sm flex items-center justify-center bg-base-200/30">
    <div class="card bg-base-100 shadow-xl p-8 flex flex-col items-center">
      <div v-if="loading" class="card flex flex-col items-center">
        <span class="loading loading-spinner loading-lg text-primary"></span>
        <p class="mt-4 text-base-content/70">正在进入酒馆...</p>
      </div>
      
      <div v-if="showError" class="alert alert-error shadow-lg">
        <div class="flex flex-col items-center gap-2">
          <div class="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span class="ml-2">啊哦~ 进入酒馆失败了</span>
          </div>
          <button class="btn btn-sm btn-outline" @click="retryEnter">再试一次吧</button>
        </div>
      </div>
    </div>
  </div>
  <div class="flex-1 flex">
    <!-- 聊天列表 -->
    <div class="w-80 bg-base-200 border-r border-base-300">
      <!-- 搜索栏 -->
      <div class="p-4 border-b border-base-300">
        <div class="relative">
          <input
            type="text"
            placeholder="搜索聊天"
            class="input input-bordered w-full pl-10"
          >
          <SearchIcon class="absolute left-3 top-2.5 text-base-content/50" :size="20" />
        </div>
      </div>

      <!-- 聊天列表 -->
      <div class="overflow-y-auto h-[calc(100vh-5rem)] bg-base-200">
        <div
          v-for="chat in chats"
          :key="chat.id"
          @click="selectChat(chat)"
          class="p-4 hover:bg-base-300 cursor-pointer"
          :class="{ 'bg-base-300': selectedChat?.id === chat.id }"
        >
          <div class="flex justify-between items-start mb-1">
            <h3 class="font-medium text-base-content">{{ chat.name }}</h3>
            <span class="text-sm text-base-content/70">{{ chat.time }}</span>
          </div>
          <p class="text-sm text-base-content/60 truncate">{{ chat.lastMessage }}</p>
        </div>
      </div>
    </div>

    <!-- 聊天界面 -->
    <div class="flex-1 flex flex-col bg-base-100 h-screen overflow-hidden">
      <!-- 聊天头部 -->
      <div class="navbar bg-base-200">
        <div v-if="selectedChat">
          <h2 class="font-medium text-base-content">{{ selectedChat.name }}</h2>
          <p class="text-sm text-base-content/70">{{ selectedChat.members }}</p>
        </div>
        <button class="btn btn-ghost btn-sm">
          <MoreVerticalIcon :size="20" class="text-base-content/70" />
        </button>
      </div>

      <!-- 消息列表 -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <div
          v-for="message in messages"
          :key="message.timestamp"
          class="chat"
          :class="message.isSelf ? 'chat-end' : 'chat-start'"
        >
          <div
            class="chat-bubble"
            :class="message.isSelf ? 'chat-bubble-primary' : 'chat-bubble-secondary'"
          >
            {{ message.content }}
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="h-32 border-t border-base-300 p-4 bg-base-200">
        <div class="flex items-center space-x-4 mb-2">
          <button class="btn btn-ghost btn-sm">
            <SmileIcon :size="20" class="text-base-content" />
          </button>
          <button class="btn btn-ghost btn-sm">
            <ImageIcon :size="20" class="text-base-content" />
          </button>
          <button class="btn btn-ghost btn-sm">
            <FileIcon :size="20" class="text-base-content" />
          </button>
          <button 
            class="btn btn-ghost btn-sm" 
            @click="askClaude"
            :disabled="!selectedChat"
          >
            <BrainIcon :size="20" class="text-primary" />
          </button>
        </div>
        
        <div class="join w-full">
          <input
            v-model="newMessage"
            type="text"
            placeholder="输入消息..."
            class="input input-bordered join-item w-full"
            @keyup.enter="sendMessage"
          >
          <button
            @click="sendMessage"
            class="btn btn-primary join-item"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { WebSocketClient, type Chat, type Message } from '../api/chat'
import { userApi, type UserInfo } from '../api/user'
import {
  SearchIcon,
  MoreVerticalIcon,
  SmileIcon,
  ImageIcon,
  FileIcon,
  BrainIcon
} from 'lucide-vue-next'
import { getDeviceId } from '../utils/deviceId'
import { useWebSocketStore } from '../stores/websocket'

const chats = ref<Chat[]>([])
const messages = ref<Message[]>([])
const selectedChat = ref<Chat | null>(null)
const newMessage = ref('')
const username = ref('')
const wsClient = new WebSocketClient()
const router = useRouter()
const loading = ref(true)
const showError = ref(false)
const deviceId = ref('')
const wsStore = useWebSocketStore()
const userId = ref('')


const handleNewMessage = (event: CustomEvent) => {
  console.log('Chat: 收到新消息', event.detail)
  const message = event.detail
  if(message.chatId === selectedChat.value?.id) {
    messages.value.push(message)
  }
}

const handleWsError = () => {
  console.log('Chat: WebSocket连接错误')
  showError.value = true
  loading.value = false
}

const handleChatList = (event: CustomEvent<Chat[]>) => {
  chats.value = event.detail
}

const handleChatMessages = (event: CustomEvent<Message[]>) => {
  messages.value = event.detail
}

onMounted(async () => {
  console.log('Chat: 组件挂载')
  try {
    deviceId.value = getDeviceId()
    userId.value = deviceId.value
    console.log('Chat: 生成设备ID', deviceId.value)
    localStorage.setItem('deviceId', deviceId.value)
    localStorage.setItem('userId', userId.value)
    console.log('Chat: 开始获取用户信息')
    const response = await userApi.getUserInfo(userId.value)
    console.log('Chat: 获取到用户信息', response.data.data)
    
    if(!response.data.data?.username || response.data.data?.username === 'undefined') {
      console.log('Chat: 未找到用户名，跳转到设置页面')
      router.push('/settings')
      return
    }
    
    username.value = response.data.data.username
    console.log('Chat: 设置用户名', username.value)
    
    // 使用 store 中的 WebSocket
    if (!wsStore.isConnected) {
      console.log('Chat: WebSocket未连接，开始连接')
      wsStore.connect(deviceId.value, username.value)
    } else {
      console.log('Chat: WebSocket已连接')
    }
    wsStore.wsClient.requestChatList()
    console.log('Chat: 添加事件监听器')
    window.addEventListener('chat-message', handleNewMessage as EventListener)
    window.addEventListener('chat-list', handleChatList as EventListener)
    window.addEventListener('ws-error', handleWsError as EventListener)
    wsStore.wsClient.requestChatList()
    window.addEventListener('chat-messages', handleChatMessages as EventListener)
    loading.value = false
    console.log('Chat: 初始化完成')
  } catch (error) {
    console.error('Chat: 获取用户信息失败', error)
    showError.value = true
    loading.value = false
  }
})

onUnmounted(() => {
  console.log('Chat: 组件卸载')
  console.log('Chat: 移除事件监听器')
  window.removeEventListener('chat-message', handleNewMessage as EventListener)
  window.removeEventListener('chat-list', handleChatList as EventListener)
  window.removeEventListener('ws-error', handleWsError as EventListener)
  window.removeEventListener('chat-messages', handleChatMessages as EventListener)
})

const sendMessage = () => {
  if (!newMessage.value.trim() || !selectedChat.value?.id || newMessage.value.trim() === '') {
    console.log('消息为空或未选择聊天室, 发送失败')
    return
  }
  
  // 使用 store 中的 WebSocket 客户端发送消息
  wsStore.wsClient.sendMessage(newMessage.value, selectedChat.value.id)
  newMessage.value = ''
}

const retryEnter = async () => {
  showError.value = false
  loading.value = true
  
  try {
    const response = await userApi.getUserInfo(userId.value)
    

    username.value = response.data.data.username
    wsStore.connect(deviceId.value, username.value)
    window.addEventListener('chat-message', handleNewMessage as EventListener)
    loading.value = false
  } catch (error) {
    console.error('获取用户信息失败:', error)
    showError.value = true
    loading.value = false
  }
}

const selectChat = (chat: Chat) => {
  selectedChat.value = chat
  messages.value = []
  wsStore.wsClient.requestChatMessages(chat.id)
  
}

const askClaude = async () => {
  if (!selectedChat.value?.id) return
  
  try {
    const messageHistory = messages.value.map(msg => ({
      content: msg.content,
      role: 'user'
    }))
    
    const response = await fetch('http://127.0.0.1:8082/api/claude', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        chatId: selectedChat.value.id,
        messages: messageHistory
      })
    })
    
    const result = await response.json()
    
    if (result.code !== 200) {
      throw new Error(result.message || '调用 Claude API 失败')
    }
    
    // 让后端通过 WebSocket 广播消息
    wsStore.wsClient.sendClaudeMessage(result.data.content, selectedChat.value.id)
    
  } catch (error) {
    console.error('请求 Claude 失败:', error)
  }
}
</script>   
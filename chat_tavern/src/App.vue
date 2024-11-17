<template>
  <container class="flex  min-h-screen max-w-[1920px] mx-auto bg-gray-100">
    <!-- 左侧导航栏 -->
    <div class="min-w-20 bg-gray-900 flex flex-col items-center py-4">
      <!-- 用户头像 -->
      <div class="w-12 h-12 rounded-full bg-gray-700 mb-8 flex items-center justify-center">
        <UserIcon class="text-gray-300" :size="24" />
      </div>
      
      <!-- 导航按钮 -->
      <nav class="space-y-10 flex flex-col items-center">
        <button class="p-3 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white">
          <MessageSquareIcon :size="20" />
        </button>
        <button class="p-3 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white">
          <UsersIcon :size="20" />
        </button>
        <button class="p-3 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white">
          <FolderIcon :size="20" />
        </button>
      </nav>
    </div>

    <!-- 聊天列表 -->
    <div class=" bg-white border-r ">
      <!-- 搜索框 -->
      <div class="p-4 border-b">
        <div class="relative">
          <input
            type="text"
            placeholder="search"
            class="w-full pl-10 pr-4 py-2 bg-gray-100 rounded-full text-sm focus:outline-none"
          >
          <SearchIcon class="absolute left-3 top-2.5 text-gray-400" :size="16" />
        </div>
      </div>

      <!-- 聊天列表 -->
      <div class="overflow-y-auto h-[calc(100vh-73px)]">
        <div
          v-for="chat in chats"
          :key="chat.id"
          @click="selectChat(chat)"
          :class="[
            'flex items-center p-4 hover:bg-gray-100 cursor-pointer',
            selectedChat?.id === chat.id ? 'bg-gray-100' : ''
          ]"
        >
          <div class="w-12 h-12 rounded-full bg-blue-500 flex-shrink-0 flex items-center justify-center text-white">
            {{ chat.name[0] }}
          </div>
          <div class="ml-4 flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-medium">{{ chat.name }}</span>
              <span class="text-xs text-gray-500">{{ chat.time }}</span>
            </div>
            <p class="text-sm text-gray-500 truncate">{{ chat.lastMessage }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="flex flex-col flex-grow ">
      <!-- 聊天头部 -->
      <div class="h-16 border-b flex items-center justify-between px-6">
        <div class="flex items-center">
          <h2 class="font-medium">{{ selectedChat?.name || '请选择聊天' }}</h2>
          <span class="ml-2 text-sm text-gray-500">{{ selectedChat?.members || '' }}</span>
        </div>
        <div class="flex items-center space-x-4 text-gray-500">
          <button class="hover:text-gray-700">
            <SearchIcon :size="18" />
          </button>
          <button class="hover:text-gray-700">
            <MoreVerticalIcon :size="18" />
          </button>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4 ">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="[
            'flex',
            message.isSelf ? 'justify-end' : 'justify-start'
          ]"
        >
          <div
            :class="[
              'max-w-[70%] rounded-lg p-3',
              message.isSelf ? 'bg-blue-500 text-white' : 'bg-gray-300'
            ]"
          >
            {{ message.content }}
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="h-1/4 border-t p-4">
        <div class="flex items-center space-x-4 mb-2">
          <button class="text-gray-500 hover:text-gray-700">
            <SmileIcon :size="20" />
          </button>
          <button class="text-gray-500 hover:text-gray-700">
            <ImageIcon :size="20" />
          </button>
          <button class="text-gray-500 hover:text-gray-700">
            <FileIcon :size="20" />
          </button>
        </div>
        <div class="flex items-end space-x-4">
          <textarea
            v-model="newMessage"
            rows="2"
            class="flex-1 resize-none rounded-lg border p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入消息..."
            @keydown.enter.prevent="sendMessage"
          ></textarea>
          <button
            @click="sendMessage"
            class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:3000/api'

import {
  UserIcon,
  MessageSquareIcon,
  UsersIcon,
  FolderIcon,
  SearchIcon,
  MoreVerticalIcon,
  SmileIcon,
  ImageIcon,
  FileIcon
} from 'lucide-vue-next'

interface Chat {
  id: number
  name: string
  lastMessage: string
  time: string
  members?: string
}

interface Message {
  id: number
  content: string
  isSelf: boolean
}

const chats = ref<Chat[]>([])
const messages = ref<Message[]>([])
const selectedChat = ref<Chat | null>(null)
const newMessage = ref('')

const fetchChats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/chats`)
    chats.value = response.data
  } catch (error) {
    console.error('获取聊天列表失败:', error)
  }
}

const fetchMessages = async (chatId: number) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/chats/${chatId}/messages`)
    messages.value = response.data
  } catch (error) {
    console.error('获取消息记录失败:', error)
  }
}

const selectChat = async (chat: Chat) => {
  selectedChat.value = chat
  await fetchMessages(chat.id)
}

const sendMessage = async () => {
  if (!newMessage.value.trim() || !selectedChat.value) return
  
  try {
    const messageData = {
      chatId: selectedChat.value.id,
      content: newMessage.value,
      isSelf: true
    }
    
    const response = await axios.post(`${API_BASE_URL}/messages`, messageData)
    messages.value.push(response.data)
    newMessage.value = ''
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

onMounted(() => {
  fetchChats()
})
</script>
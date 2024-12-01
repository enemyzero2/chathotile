<template>
  <div class="flex-1 flex">
    <!-- 聊天列表 -->
    <div class="w-80 bg-gray-100 border-r border-gray-200">
      <!-- 搜索栏 -->
      <div class="p-4 border-b border-gray-200">
        <div class="relative">
          <input
            type="text"
            placeholder="搜索聊天"
            class="w-full pl-10 pr-4 py-2 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-gray-500 font-song"
          >
          <SearchIcon class="absolute left-3 top-2.5 text-gray-400" :size="20" />
        </div>
      </div>

      <!-- 聊天列表 -->
      <div class="overflow-y-auto h-[calc(100vh-5rem)] bg-gray-100">
        <div
          v-for="chat in chats"
          :key="chat.id"
          @click="selectChat(chat)"
          class="p-4 hover:bg-gray-200 cursor-pointer"
          :class="{ 'bg-gray-200': selectedChat?.id === chat.id }"
        >
          <div class="flex justify-between items-start mb-1">
            <h3 class="font-medium font-song text-gray-900">{{ chat.name }}</h3>
            <span class="text-sm text-gray-700">{{ chat.time }}</span>
          </div>
          <p class="text-sm text-gray-600 truncate">{{ chat.lastMessage }}</p>
        </div>
      </div>
    </div>

    <!-- 聊天界面 -->
    <div class="flex-1 flex flex-col bg-white">
      <!-- 聊天头部 -->
      <div class="h-16 border-b bg-gray-100 border-gray-200 px-6 flex justify-between items-center">
        <div v-if="selectedChat">
          <h2 class="font-medium text-gray-900">{{ selectedChat.name }}</h2>
          <p class="text-sm text-gray-700">{{ selectedChat.members }}</p>
        </div>
        <button class="p-2 hover:bg-gray-200 rounded-lg">
          <MoreVerticalIcon :size="20" class="text-gray-700" />
        </button>
      </div>

      <!-- 消息列表 -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <div
          v-for="message in messages"
          :key="message.id"
          class="flex"
          :class="message.isSelf ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-[70%] rounded-lg px-4 py-2"
            :class="message.isSelf ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-900'"
          >
            {{ message.content }}
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="h-32 border-t border-gray-200 p-4 bg-gray-100">
        <div class="flex items-center space-x-4 mb-2">
          <button class="p-2 hover:bg-gray-200 rounded-lg">
            <SmileIcon :size="20" class="text-gray-600" />
          </button>
          <button class="p-2 hover:bg-gray-200 rounded-lg">
            <ImageIcon :size="20" class="text-gray-600" />
          </button>
          <button class="p-2 hover:bg-gray-200 rounded-lg">
            <FileIcon :size="20" class="text-gray-600" />
          </button>
        </div>
        <div class="flex space-x-4">
          <input
            v-model="newMessage"
            type="text"
            placeholder="输入消息..."
            class="flex-1 px-4 py-2 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-gray-500 text-gray-900 placeholder-gray-400"
            @keyup.enter="sendMessage"
          >
          <button
            @click="sendMessage"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { chatApi, type Chat, type Message } from '../api/chat'
import {
  SearchIcon,
  MoreVerticalIcon,
  SmileIcon,
  ImageIcon,
  FileIcon
} from 'lucide-vue-next'

const chats = ref<Chat[]>([])
const messages = ref<Message[]>([])
const selectedChat = ref<Chat | null>(null)
const newMessage = ref('')

const fetchChats = async () => {
  try {
    const { data } = await chatApi.getChats()
    chats.value = data
  } catch (error) {
    console.error('获取聊天列表失败:', error)
  }
}

const fetchMessages = async (chatId: number) => {
  try {
    const { data } = await chatApi.getChatMessages(chatId)
    messages.value = data
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
    
    const { data } = await chatApi.sendMessage(messageData)
    messages.value.push(data)
    newMessage.value = ''
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

onMounted(() => {
  fetchChats()
})
</script> 
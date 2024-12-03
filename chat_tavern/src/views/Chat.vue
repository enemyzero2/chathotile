<template>
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
    <div class="flex-1 flex flex-col bg-base-100">
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
      <div class="card-body flex-1 overflow-y-auto p-6 space-y-4">
        <div
          v-for="message in messages"
          :key="message.id"
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
import { ref, onMounted } from 'vue'
import { themeChange } from 'theme-change'
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
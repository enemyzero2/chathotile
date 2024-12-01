<template>
  <container class="flex min-h-screen max-w-[1920px] mx-auto bg-gray-100">
    <!-- 左侧导航栏 -->
    <div class="min-w-20 bg-gray-900 flex flex-col items-center py-4">
      <!-- 用户头像 -->
      <router-link to="/settings" class="w-12 h-12 rounded-full bg-gray-700 mb-8 flex items-center justify-center">
        <UserIcon class="text-gray-300" :size="24" />
      </router-link>
      
      <!-- 导航按钮 -->
      <nav class="space-y-10 flex flex-col items-center">
        <router-link to="/" class="p-3 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white">
          <MessageSquareIcon :size="20" />
        </router-link>
        <button class="p-3 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white">
          <UsersIcon :size="20" />
        </button>
        <button class="p-3 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white">
          <FolderIcon :size="20" />
        </button>
      </nav>
    </div>

    <!-- 路由出口 -->
    <router-view></router-view>
  </container>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { appApi } from './api/APP'
import {
  UserIcon,
  MessageSquareIcon,
  UsersIcon,
  FolderIcon,
} from 'lucide-vue-next'

onMounted(async () => {
  try {
    await appApi.initChatClient()
    console.log('聊天客户端初始化成功')
  } catch (error) {
    console.error('聊天客户端初始化失败:', error)
  }
})

onBeforeUnmount(async () => {
  try {
    await appApi.closeChatClient()
    console.log('聊天客户端关闭成功')
  } catch (error) {
    console.error('聊天客户端关闭失败:', error)
  }
})
</script>

<style>
body {
  font-family: 'SimSun', 'STSong', '宋体', serif;
}
</style>
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


onMounted(() => {
})
</script>

<style>
</style>
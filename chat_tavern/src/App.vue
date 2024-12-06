<template>
  <div class="container flex min-h-screen max-w-[1920px] mx-auto bg-base-100">
    <!-- 左侧导航栏 -->
    <div class="min-w-20 bg-base-300 flex flex-col items-center py-4">
      <!-- 用户头像 -->
      <router-link to="/settings" class="avatar placeholder mb-8">
        <div class="w-12 rounded-full bg-neutral text-neutral-content">
          <UserIcon :size="24" />
        </div>
      </router-link>
      
      <!-- 导航按钮 -->
      <nav class="space-y-10 flex flex-col items-center">
        <router-link 
          to="/" 
          class="btn btn-ghost btn-circle"
          :class="{ 'btn-active': $route.path === '/' }"
        >
          <MessageSquareIcon :size="20" />
        </router-link>
        <button class="btn btn-ghost btn-circle">
          <UsersIcon :size="20" />
        </button>
        <button class="btn btn-ghost btn-circle">
          <FolderIcon :size="20" />
        </button>
      </nav>

      <!-- 主题切换按钮，放在底部 -->
      <select 
        class="select select-bordered select-sm mt-auto"
        data-choose-theme
      >
        <option value="retro">复古</option>
        <option value="light">明亮</option>
        <option value="dark">深色</option>
        <option value="cupcake">粉彩</option>
        <option value="bumblebee">蜜蜂</option>
        <option value="emerald">翠绿</option>
        <option value="corporate">商务</option>
        <option value="synthwave">赛博</option>
        <option value="cyberpunk">朋克</option>
      </select>
    </div>

    <!-- 路由出口 -->
    <router-view></router-view>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { appApi } from './api/APP'
import { themeChange } from 'theme-change'
import {
  UserIcon,
  MessageSquareIcon,
  UsersIcon,
  FolderIcon,
} from 'lucide-vue-next'

onMounted(async () => {
  themeChange(false)
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
<template>
    <div :class="{ 'dark': darkMode }">
      <div class="max-w-md mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
        <header class="bg-gray-200 dark:bg-gray-800 p-4">
          <h1 class="text-xl font-semibold text-gray-800 dark:text-gray-200">个人资料</h1>
        </header>
        
        <main class="p-4 space-y-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-4">
              <div class="w-16 h-16 bg-gray-300 dark:bg-gray-700 rounded-full overflow-hidden">
                <UserIcon alt="头像" class="w-full h-full object-cover" />
              </div>
              <div>
                <h2 class="text-lg font-medium text-gray-800 dark:text-gray-200">更改头像</h2>
                <p class="text-sm text-gray-600 dark:text-gray-400">点击更新您的头像</p>
              </div>
            </div>
            <ChevronRight class="text-gray-400" />
          </div>
  
          <div class="space-y-2">
            <label for="nickname" class="text-gray-700 dark:text-gray-300">昵称</label>
            <input id="nickname" v-model="nickname" placeholder="输入您的昵称" 
                   class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400" />
          </div>
  
          <div class="flex items-center justify-between py-2 border-t border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-2">
              <User class="text-gray-600 dark:text-gray-400" />
              <span class="text-gray-800 dark:text-gray-200">微信号</span>
            </div>
            <span class="text-gray-600 dark:text-gray-400">wxid_abc123</span>
          </div>
  
          <div class="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-2">
              <QrCode class="text-gray-600 dark:text-gray-400" />
              <span class="text-gray-800 dark:text-gray-200">我的二维码</span>
            </div>
            <ChevronRight class="text-gray-400" />
          </div>
  
          <div class="flex items-center justify-between">
            <span class="text-gray-800 dark:text-gray-200">深色模式</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="darkMode" class="sr-only peer">
              <div class="w-11 h-6 bg-gray-400 peer-focus:outline-none rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-500"></div>
            </label>
          </div>
  
          <button @click="saveChanges" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">
            保存更改
          </button>
        </main>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { ChevronRight, QrCode, User, UserIcon } from 'lucide-vue-next'
  import { userApi } from '../api/user'
  
  // 用户数据
  const darkMode = ref(false)
  const nickname = ref('')
  const isEditing = ref(false)
  const avatarFile = ref<File | null>(null)
  
  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const { data } = await userApi.getUserInfo()
      nickname.value = data.nickname
      darkMode.value = data.darkMode
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
  
  // 处理头像上传
  const handleAvatarChange = async (event: Event) => {
    const input = event.target as HTMLInputElement
    if (input.files && input.files[0]) {
      const file = input.files[0]
      const formData = new FormData()
      formData.append('avatar', file)
      
      try {
        await userApi.updateAvatar(formData)
        // 刷新用户信息
        await fetchUserInfo()
      } catch (error) {
        console.error('上传头像失败:', error)
      }
    }
  }
  
  // 保存更改
  const saveChanges = async () => {
    try {
      await userApi.updateUserInfo({
        nickname: nickname.value,
        darkMode: darkMode.value
      })
      isEditing.value = false
    } catch (error) {
      console.error('保存更改失败:', error)
    }
  }
  
  // 组件加载时获取用户信息
  onMounted(fetchUserInfo)
  </script>
  <script lang="ts">
  export default {
    name: 'Usersettings'
  }
  </script>
  
  <style scoped>
  /* 可以在这里添加任何额外的组件特定样式 */
  </style>
<template>
  <div class="min-h-screen w-full bg-amber-100 flex items-center justify-center p-4">
    <div class="w-full max-w-xl bg-amber-200 border-2 border-amber-900 rounded-lg shadow-lg overflow-hidden">
      <div class="bg-amber-300 p-6">
        <h1 class="text-3xl font-bold text-amber-900 text-center font-song">酒馆旅客登记簿</h1>
      </div>
      <form @submit.prevent="saveProfile" class="p-6 space-y-6">
        <div class="space-y-2">
          <label for="name" class="block text-sm font-medium text-amber-900">来者可曾报上大名</label>
          <input
            id="name"
            v-model="name"
            type="text"
            class="w-full px-4 py-3 bg-amber-50 border border-amber-900 rounded-md text-amber-900 placeholder-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-700 transition duration-300"
            placeholder="请输入您的名字"
          />
        </div>
        <div class="space-y-2">
          <label for="background" class="block text-sm font-medium text-amber-900">还请坐下小酌一杯，叙述你的传奇</label>
          <textarea
            id="background"
            v-model="background"
            rows="5"
            class="w-full px-4 py-3 bg-amber-50 border border-amber-900 rounded-md text-amber-900 placeholder-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-700 transition duration-300"
            placeholder="讲述您的传奇故事"
          ></textarea>
        </div>
        <button
          type="submit"
          class="w-full bg-amber-900 hover:bg-amber-800 text-amber-100 font-bold py-3 px-6 rounded-md transition duration-300 ease-in-out transform hover:scale-105"
        >
          记入酒馆史册
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { userApi } from '../api/user'

const name = ref('')
const background = ref('')

const saveProfile = async () => {
  try {
    await userApi.saveProfile({
      name: name.value,
      background: background.value
    })
    // 可以添加成功提示
    alert('保存成功！')
  } catch (error) {
    console.error('保存失败:', error)
    // 可以添加错误提示
    alert('保存失败，请稍后重试')
  }
}
</script>
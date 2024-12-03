<template>
  <div class="min-h-screen w-full bg-base-200 flex items-center justify-center p-4">
    <div class="card w-full max-w-xl bg-base-100 shadow-xl">
      <div class="card-body">
        <h1 class="card-title text-3xl font-bold text-base-content text-center font-song">酒馆旅客登记簿</h1>
        <form @submit.prevent="saveProfile" class="space-y-6">
          <div class="form-control">
            <label class="label">
              <span class="label-text">来者可曾报上大名</span>
            </label>
            <input
              id="name"
              v-model="name"
              type="text"
              class="input input-bordered w-full"
              placeholder="请输入您的名字"
            />
          </div>
          <div class="form-control">
            <label class="label">
              <span class="label-text">还请坐下小酌一杯，叙述你的传奇</span>
            </label>
            <textarea
              id="background"
              v-model="background"
              rows="5"
              class="textarea textarea-bordered w-full"
              placeholder="讲述您的传奇故事"
            ></textarea>
          </div>
          <button
            type="submit"
            class="btn btn-primary w-full"
          >
            记入酒馆史册
          </button>
        </form>
      </div>
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
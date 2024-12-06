import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8082'
})

// 用户信息接口
export interface UserInfo {
  id?: number
  name: string
  background?: string
  avatar?: string
  createdAt?: string
}

// 用户资料更新接口
export interface UserProfileUpdateData {
  name: string
  background: string
}

export const userApi = {
  // 获取用户信息
  getUserInfo() {
    return api.get<{ data: UserInfo }>('/user/info')
  },

  // 保存用户资料
  saveProfile(data: UserProfileUpdateData) {
    return api.post<{ message: string }>('/user/profile', data)
  }
}


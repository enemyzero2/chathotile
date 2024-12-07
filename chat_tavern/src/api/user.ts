import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8082'
})

// 用户信息接口
export interface UserInfo {
  id: string
  username: string
  background: string | null
  avatar: string | null
  created_at: string
}

// 用户资料更新接口
export interface UserProfileUpdateData {
  id: string
  username: string
  background: string
}

export const userApi = {
  // 获取用户信息
  getUserInfo(id: string) {
    return api.get<{ data: UserInfo }>(`/user/info?id=${id}`)
  },

  // 更新用户资料
  updateProfile(data: UserProfileUpdateData) {
    return api.post<{ message: string }>('/user/profile', data)
  }
}


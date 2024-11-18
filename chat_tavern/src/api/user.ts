import axios from 'axios'

const API_BASE_URL = 'http://your-api-base-url'

export const userApi = {
  // 获取用户信息
  getUserInfo: () => axios.get(`${API_BASE_URL}/user/info`),
  
  // 更新用户信息
  updateUserInfo: (data: {
    nickname: string,
    darkMode: boolean
  }) => axios.put(`${API_BASE_URL}/user/update`, data),
  
  // 更新头像
  updateAvatar: (formData: FormData) => axios.post(
    `${API_BASE_URL}/user/avatar`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  )
} 
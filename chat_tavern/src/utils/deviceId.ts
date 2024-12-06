function generateDeviceId(): string {
  // 获取时间戳后6位
  const timestamp = new Date().getTime().toString().slice(-6)
  // 生成4位随机数
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  // 组合成10位ID
  return `${timestamp}${random}`
}

export function getDeviceId(): string {
  const storageKey = 'device_id'
  let deviceId = localStorage.getItem(storageKey)
  
  if (!deviceId) {
    deviceId = generateDeviceId()
    localStorage.setItem(storageKey, deviceId)
  }
  
  return deviceId
} 
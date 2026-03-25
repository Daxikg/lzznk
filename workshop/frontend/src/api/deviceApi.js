// API基础地址 - 通过Vite代理访问Django后端
const API_BASE_URL = '/workshop'

// 模拟网络延迟
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * 获取所有数据（设备和区域）
 */
export async function getAllData() {
  const response = await fetch(`${API_BASE_URL}/api/all/`)
  if (!response.ok) {
    throw new Error('获取数据失败')
  }
  return response.json()
}

/**
 * 获取所有设备状态
 */
export async function getDeviceStatus() {
  const response = await fetch(`${API_BASE_URL}/api/devices/`)
  if (!response.ok) {
    throw new Error('获取设备数据失败')
  }
  return response.json()
}

/**
 * 获取单个设备详情
 */
export async function getDeviceDetail(deviceId) {
  const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/`)
  if (!response.ok) {
    throw new Error('设备不存在')
  }
  return response.json()
}

/**
 * 获取统计数据
 */
export async function getStatistics() {
  const response = await fetch(`${API_BASE_URL}/api/statistics/`)
  if (!response.ok) {
    throw new Error('获取统计数据失败')
  }
  return response.json()
}

/**
 * 获取区域配置
 */
export async function getAreas() {
  const response = await fetch(`${API_BASE_URL}/api/areas/`)
  if (!response.ok) {
    throw new Error('获取区域数据失败')
  }
  return response.json()
}

/**
 * 更新设备状态
 */
export async function updateDeviceStatus(deviceId, status) {
  const response = await fetch(`${API_BASE_URL}/api/devices/${deviceId}/status/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  })
  if (!response.ok) {
    throw new Error('更新状态失败')
  }
  return response.json()
}

/**
 * 格式化故障时长
 */
export function formatFaultDuration(faultTime) {
  if (!faultTime) return '-'

  const duration = Date.now() - faultTime
  const hours = Math.floor(duration / (1000 * 60 * 60))
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60))

  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  return `${minutes}分钟`
}
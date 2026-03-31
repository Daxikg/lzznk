import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAllData, getDeviceStatus, getStatistics, getAreas } from '../api/deviceApi'

export const useDeviceStore = defineStore('device', () => {
  // 设备列表
  const devices = ref([])

  // 区域列表
  const areas = ref([])

  // 统计数据
  const statistics = ref({
    total: 0,
    running: 0,
    fault: 0,
    longFault: 0,
    offline: 0,
    runningRate: 0
  })

  // 加载状态
  const loading = ref(false)

  // 最后更新时间
  const lastUpdate = ref(null)

  // 是否自动刷新
  const autoRefresh = ref(true)

  // 刷新间隔（毫秒）- 1分钟刷新页面数据
  const refreshInterval = ref(60000)

  // 计算属性
  const runningRate = computed(() => {
    return statistics.value.runningRate || 0
  })

  // 按区域分组
  const devicesByArea = computed(() => {
    const grouped = {}
    devices.value.forEach(device => {
      if (!grouped[device.area]) {
        grouped[device.area] = []
      }
      grouped[device.area].push(device)
    })
    return grouped
  })

  // 获取所有数据（初始化）
  async function fetchAllData() {
    loading.value = true
    try {
      const data = await getAllData()
      devices.value = data.devices
      areas.value = data.areas
      statistics.value = data.statistics
      lastUpdate.value = new Date()
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 仅获取设备数据
  async function fetchDevices() {
    loading.value = true
    try {
      const data = await getDeviceStatus()
      devices.value = data
      lastUpdate.value = new Date()
    } catch (error) {
      console.error('获取设备数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取统计数据
  async function fetchStatistics() {
    try {
      const data = await getStatistics()
      statistics.value = data
    } catch (error) {
      console.error('获取统计数据失败:', error)
    }
  }

  // 获取区域数据
  async function fetchAreas() {
    try {
      const data = await getAreas()
      areas.value = data
    } catch (error) {
      console.error('获取区域数据失败:', error)
    }
  }

  // 刷新所有数据
  async function refreshAll() {
    await fetchAllData()
  }

  // 更新单个设备状态（用于WebSocket实时更新）
  function updateDevice(deviceId, status) {
    const index = devices.value.findIndex(d => d.id === deviceId)
    if (index !== -1) {
      devices.value[index] = {
        ...devices.value[index],
        status,
        faultTime: status === 'fault' ? Date.now() : null
      }
    }
  }

  return {
    devices,
    areas,
    statistics,
    loading,
    lastUpdate,
    autoRefresh,
    refreshInterval,
    runningRate,
    devicesByArea,
    fetchAllData,
    fetchDevices,
    fetchStatistics,
    fetchAreas,
    refreshAll,
    updateDevice
  }
})
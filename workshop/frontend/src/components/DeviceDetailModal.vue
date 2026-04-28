<template>
  <Teleport to="body">
    <div class="modal-overlay" v-if="visible" @click.self="$emit('close')">
      <div class="modal-content">
        <div class="modal-header">
          <div class="header-left">
            <span class="device-type-icon">{{ typeIcon }}</span>
            <h3>{{ device?.name }}</h3>
          </div>
          <button class="close-btn" @click="$emit('close')">&times;</button>
        </div>
        <div class="modal-body" v-if="device">
          <!-- 状态卡片 -->
          <div class="status-card" :class="`status-${device.computedStatus}`">
            <span class="status-dot" :style="{ backgroundColor: statusColor }"></span>
            <span class="status-text">{{ statusLabel }}</span>
            <span class="status-desc">{{ statusDesc }}</span>
          </div>

          <!-- 设备二维码 -->
          <div class="qrcode-section" v-if="device.qrcodeUrl">
            <h4>设备二维码</h4>
            <div class="qrcode-container">
              <img :src="device.qrcodeUrl" alt="设备二维码" class="qrcode-image" />
            </div>
          </div>

          <!-- 设备其他信息 -->
          <div class="info-section">
            <h4>设备其他信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">设备编号</span>
                <span class="value">{{ device.id }}</span>
              </div>
              <div class="info-item">
                <span class="label">所属区域</span>
                <span class="value">{{ device.area }}</span>
              </div>
              <div class="info-item">
                <span class="label">设备类型</span>
                <span class="value">{{ typeLabel }}</span>
              </div>
              <div class="info-item">
                <span class="label">设备描述</span>
                <span class="value">{{ device.description || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 故障信息 -->
          <div class="fault-section" v-if="device.faultTime && (device.computedStatus === 'fault' || device.computedStatus === 'longFault')">
            <h4>故障信息</h4>
            <div class="fault-info">
              <div class="fault-row">
                <span class="label">故障发生时间</span>
                <span class="value">{{ faultStartTime }}</span>
              </div>
              <div class="fault-row">
                <span class="label">已持续时间</span>
                <span class="value highlight">{{ faultDuration }}</span>
              </div>
              <!-- 当前故障详情 -->
              <div class="fault-row" v-if="currentFault">
                <span class="label">发现人</span>
                <span class="value">{{ currentFault.reporter || '-' }}</span>
              </div>
              <div class="fault-row" v-if="currentFault">
                <span class="label">故障情况描述</span>
                <span class="value">{{ currentFault.phenomenon || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 最近半年统计 -->
          <div class="stats-section" v-if="device.halfYearStats">
            <h4>最近半年统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-label">点检次数</span>
                <span class="stat-value">{{ device.halfYearStats.inspectionCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">故障次数</span>
                <span class="stat-value fault">{{ device.halfYearStats.faultCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">故障率</span>
                <span class="stat-value" :class="{ 'fault': device.halfYearStats.faultRate > 5 }">{{ device.halfYearStats.faultRate }}%</span>
              </div>
            </div>
          </div>

          <!-- 故障记录列表 -->
          <div class="repair-section" v-if="device.repairRecords && device.repairRecords.length > 0">
            <h4>最近半年故障记录 <span class="record-count">(共{{ device.repairRecords.length }}条)</span></h4>
            <div class="repair-list">
              <div
                class="repair-item"
                v-for="(record, index) in device.repairRecords"
                :key="record.id"
                :class="{ 'expanded': expandedRecordId === record.id }"
                @click="toggleRecord(record.id)"
              >
                <div class="repair-header">
                  <div class="repair-summary">
                    <span class="repair-date">{{ record.faultDate }}</span>
                    <span class="repair-reporter">{{ record.reporter || '-' }}</span>
                    <span class="repair-status" :class="{ 'resolved': record.isResolved }">
                      {{ record.isResolved ? '已修复' : '未修复' }}
                    </span>
                  </div>
                  <span class="expand-icon">{{ expandedRecordId === record.id ? '▼' : '▶' }}</span>
                </div>
                <!-- 展开详情 -->
                <div class="repair-detail" v-if="expandedRecordId === record.id">
                  <div class="detail-row">
                    <span class="label">故障日期</span>
                    <span class="value">{{ record.faultDate }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">发现人</span>
                    <span class="value">{{ record.reporter || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">故障情况描述</span>
                    <span class="value">{{ record.phenomenon || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">故障分析</span>
                    <span class="value">{{ record.analysis || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">维修日期</span>
                    <span class="value">{{ record.repairDate || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">维修班组</span>
                    <span class="value">{{ record.repairTeam || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">修理人员</span>
                    <span class="value">{{ record.worker || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">故障处理情况</span>
                    <span class="value">{{ record.result || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">材料消耗</span>
                    <span class="value">{{ record.materials || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">是否已修复</span>
                    <span class="value" :class="{ 'resolved': record.isResolved }">{{ record.isResolved ? '已修复' : '未修复' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref } from 'vue'
import { statusConfig, deviceTypeConfig } from '../api/mockData'
import { formatFaultDuration } from '../api/deviceApi'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  device: {
    type: Object,
    default: null
  }
})

defineEmits(['close'])

// 展开的故障记录ID
const expandedRecordId = ref(null)

// 切换展开状态
const toggleRecord = (id) => {
  if (expandedRecordId.value === id) {
    expandedRecordId.value = null
  } else {
    expandedRecordId.value = id
  }
}

const statusColor = computed(() => {
  return statusConfig[props.device?.computedStatus]?.color || '#95a5a6'
})

const statusLabel = computed(() => {
  return statusConfig[props.device?.computedStatus]?.label || '未知'
})

const statusDesc = computed(() => {
  return statusConfig[props.device?.computedStatus]?.description || ''
})

const typeLabel = computed(() => {
  return deviceTypeConfig[props.device?.type]?.label || props.device?.type || '-'
})

const typeIcon = computed(() => {
  return deviceTypeConfig[props.device?.type]?.icon || '⚙️'
})

const faultDuration = computed(() => {
  if (!props.device?.faultTime) return '-'
  return formatFaultDuration(props.device.faultTime)
})

const faultStartTime = computed(() => {
  if (!props.device?.faultTime) return ''
  const date = new Date(props.device.faultTime)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
})

// 当前故障（最近的未修复故障记录）
const currentFault = computed(() => {
  if (!props.device?.repairRecords) return null
  // 找最近的未修复故障
  const unresolved = props.device.repairRecords.filter(r => !r.isResolved)
  if (unresolved.length > 0) {
    return unresolved[0]
  }
  // 如果都已修复，返回最近一条
  if (props.device.repairRecords.length > 0) {
    return props.device.repairRecords[0]
  }
  return null
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: linear-gradient(135deg, #1a2a3a, #2c3e50);
  border-radius: 12px;
  border: 1px solid rgba(79, 195, 247, 0.3);
  min-width: 450px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.device-type-icon {
  font-size: 24px;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 1;
}

.modal-body {
  padding: 20px;
}

/* 状态卡片 */
.status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.05);
}

.status-card.status-running {
  border-left: 4px solid #2ecc71;
}

.status-card.status-fault {
  border-left: 4px solid #f1c40f;
}

.status-card.status-longFault {
  border-left: 4px solid #e74c3c;
}

.status-card.status-offline {
  border-left: 4px solid #95a5a6;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-text {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.status-desc {
  margin-left: auto;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* 信息区块 */
.info-section, .fault-section, .warehouse-section, .qrcode-section, .stats-section, .repair-section {
  margin-bottom: 20px;
}

.info-section h4, .fault-section h4, .warehouse-section h4, .qrcode-section h4, .stats-section h4, .repair-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #4fc3f7;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 8px;
}

.record-count {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

/* 二维码区域 */
.qrcode-container {
  display: flex;
  justify-content: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(79, 195, 247, 0.15);
}

.qrcode-image {
  max-width: calc(100% - 10px);
  width: calc(100% - 10px);
  height: auto;
  border-radius: 4px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.info-item .value {
  font-size: 13px;
  color: #fff;
}

/* 故障信息 */
.fault-info {
  background: rgba(231, 76, 60, 0.1);
  border-radius: 8px;
  padding: 12px;
}

.fault-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.fault-row:last-child {
  border-bottom: none;
}

.fault-row .label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.fault-row .value {
  color: #fff;
  font-size: 12px;
  max-width: 60%;
  word-break: break-all;
}

.fault-row .value.highlight {
  color: #e74c3c;
  font-weight: 600;
}

/* 统计数据 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #4fc3f7;
}

.stat-value.fault {
  color: #e74c3c;
}

/* 故障记录列表 */
.repair-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.repair-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.repair-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.repair-item.expanded {
  background: rgba(79, 195, 247, 0.1);
}

.repair-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
}

.repair-summary {
  display: flex;
  gap: 12px;
  align-items: center;
}

.repair-date {
  font-size: 12px;
  color: #fff;
}

.repair-reporter {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.repair-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.repair-status.resolved {
  background: rgba(46, 204, 113, 0.2);
  color: #2ecc71;
}

.expand-icon {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

/* 展开详情 */
.repair-detail {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-row {
  display: flex;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  width: 100px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
}

.detail-row .value {
  flex: 1;
  color: #fff;
  font-size: 11px;
}

.detail-row .value.resolved {
  color: #2ecc71;
}

/* 仓储信息 */
.warehouse-info {
  background: rgba(155, 89, 182, 0.1);
  border-radius: 8px;
  padding: 12px;
}
</style>
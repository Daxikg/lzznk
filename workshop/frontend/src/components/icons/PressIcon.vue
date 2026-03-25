<template>
  <!-- 压装设备图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 底座 -->
    <rect x="2" y="20" width="20" height="3" rx="1" :fill="iconColor" opacity="0.7"/>
    <!-- 支柱 -->
    <rect x="4" y="8" width="3" height="12" :fill="iconColor"/>
    <rect x="17" y="8" width="3" height="12" :fill="iconColor"/>
    <!-- 横梁 -->
    <rect x="3" y="6" width="18" height="4" rx="1" :fill="iconColor"/>
    <!-- 压头 -->
    <rect x="9" y="10" width="6" height="8" rx="1" :fill="iconColor" opacity="0.9">
      <animate v-if="status === 'running'" attributeName="y" values="10;12;10" dur="1s" repeatCount="indefinite"/>
      <animate v-if="status === 'running'" attributeName="height" values="8;6;8" dur="1s" repeatCount="indefinite"/>
    </rect>
    <!-- 工作台 -->
    <rect x="7" y="18" width="10" height="2" rx="1" :fill="iconColor" opacity="0.8"/>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'running' },
  size: { type: Number, default: 24 }
})

const iconColor = computed(() => {
  const colors = { running: '#22c55e', fault: '#eab308', longFault: '#ef4444', offline: '#6b7280' }
  return colors[props.status] || '#6b7280'
})
</script>
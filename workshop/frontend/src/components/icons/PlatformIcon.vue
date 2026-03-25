<template>
  <!-- 平台设备图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 平台面 -->
    <rect x="2" y="14" width="20" height="3" rx="1" :fill="iconColor"/>
    <!-- 支撑腿 -->
    <rect x="4" y="17" width="2" height="5" :fill="iconColor" opacity="0.8"/>
    <rect x="10" y="17" width="2" height="5" :fill="iconColor" opacity="0.8"/>
    <rect x="18" y="17" width="2" height="5" :fill="iconColor" opacity="0.8"/>
    <!-- 温度标识 -->
    <circle cx="12" cy="10" r="4" :fill="iconColor" opacity="0.6"/>
    <text x="12" y="13" text-anchor="middle" fill="#fff" font-size="6" font-weight="bold">T</text>
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
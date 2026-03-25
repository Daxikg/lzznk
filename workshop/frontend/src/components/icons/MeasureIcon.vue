<template>
  <!-- 测量设备图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 底座 -->
    <rect x="4" y="18" width="16" height="4" rx="1" :fill="iconColor" opacity="0.8"/>
    <!-- 主体 -->
    <rect x="6" y="6" width="12" height="12" rx="2" :fill="iconColor"/>
    <!-- 显示屏 -->
    <rect x="8" y="8" width="8" height="6" rx="1" fill="rgba(0,0,0,0.3)"/>
    <!-- 测量线 -->
    <line x1="10" y1="11" x2="14" y2="11" stroke="rgba(255,255,255,0.8)" stroke-width="1.5"/>
    <line x1="12" y1="9" x2="12" y2="13" stroke="rgba(255,255,255,0.8)" stroke-width="1.5"/>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'running' },
  size: { type: Number, default: 24 }
})

const iconColor = computed(() => {
  const colors = {
    running: '#22c55e',
    fault: '#eab308',
    longFault: '#ef4444',
    offline: '#6b7280'
  }
  return colors[props.status] || '#6b7280'
})
</script>
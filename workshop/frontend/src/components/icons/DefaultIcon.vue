<template>
  <!-- 默认设备图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <rect x="4" y="4" width="16" height="16" rx="3" :fill="iconColor"/>
    <circle cx="12" cy="12" r="4" fill="rgba(255,255,255,0.3)"/>
    <circle cx="12" cy="12" r="2" :fill="iconColor" opacity="0.8"/>
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
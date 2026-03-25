<template>
  <!-- 电控柜图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 柜体 -->
    <rect x="4" y="2" width="16" height="20" rx="2" :fill="iconColor"/>
    <!-- 门缝 -->
    <line x1="12" y1="4" x2="12" y2="20" :stroke="iconColor" stroke-width="0.5" opacity="0.5"/>
    <!-- 指示灯组 -->
    <circle cx="8" cy="6" r="2" :fill="status === 'running' ? '#4ade80' : '#374151'">
      <animate v-if="status === 'running'" attributeName="opacity" values="1;0.5;1" dur="1s" repeatCount="indefinite"/>
    </circle>
    <circle cx="16" cy="6" r="2" :fill="status === 'running' ? '#4ade80' : '#374151'">
      <animate v-if="status === 'running'" attributeName="opacity" values="1;0.5;1" dur="1s" repeatCount="indefinite"/>
    </circle>
    <!-- 显示屏 -->
    <rect x="7" y="10" width="10" height="5" rx="1" fill="rgba(0,0,0,0.3)"/>
    <line x1="9" y1="12" x2="15" y2="12" stroke="rgba(255,255,255,0.6)" stroke-width="1"/>
    <!-- 按钮 -->
    <circle cx="12" cy="18" r="2" fill="rgba(255,255,255,0.3)"/>
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
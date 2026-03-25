<template>
  <!-- 玻璃房图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 房体 -->
    <rect x="2" y="6" width="20" height="16" rx="2" :fill="iconColor" opacity="0.3"/>
    <!-- 玻璃反光 -->
    <rect x="3" y="7" width="18" height="14" rx="1" fill="rgba(255,255,255,0.1)"/>
    <line x1="3" y1="7" x2="21" y2="21" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
    <!-- 顶部 -->
    <path d="M2 6 L12 1 L22 6" :fill="iconColor" opacity="0.5"/>
    <!-- 门 -->
    <rect x="10" y="14" width="4" height="8" rx="1" :fill="iconColor" opacity="0.6"/>
    <!-- 状态灯 -->
    <circle cx="12" cy="4" r="1.5" :fill="status === 'running' ? '#4ade80' : '#6b7280'">
      <animate v-if="status === 'running'" attributeName="opacity" values="1;0.5;1" dur="1.5s" repeatCount="indefinite"/>
    </circle>
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
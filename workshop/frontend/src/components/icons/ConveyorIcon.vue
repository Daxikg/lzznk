<template>
  <!-- 传输设备图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 滚轮 -->
    <circle cx="5" cy="12" r="4" :fill="iconColor" opacity="0.8">
      <animateTransform v-if="status === 'running'" attributeName="transform" type="rotate" from="0 5 12" to="360 5 12" dur="1s" repeatCount="indefinite"/>
    </circle>
    <circle cx="19" cy="12" r="4" :fill="iconColor" opacity="0.8">
      <animateTransform v-if="status === 'running'" attributeName="transform" type="rotate" from="0 19 12" to="360 19 12" dur="1s" repeatCount="indefinite"/>
    </circle>
    <!-- 传送带 -->
    <rect x="3" y="10" width="18" height="4" :fill="iconColor" opacity="0.3"/>
    <!-- 流动点 -->
    <circle r="2" cy="12" :fill="iconColor">
      <animate attributeName="cx" values="5;19;5" dur="2s" repeatCount="indefinite"/>
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
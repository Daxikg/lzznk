<template>
  <!-- 动力设备图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 外壳 -->
    <circle cx="12" cy="12" r="10" :fill="iconColor" opacity="0.3"/>
    <circle cx="12" cy="12" r="8" :fill="iconColor" opacity="0.5"/>
    <!-- 叶片/转子 -->
    <g v-if="status === 'running'">
      <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
      <rect x="11" y="4" width="2" height="8" rx="1" :fill="iconColor"/>
      <rect x="11" y="12" width="2" height="8" rx="1" :fill="iconColor"/>
      <rect x="4" y="11" width="8" height="2" rx="1" :fill="iconColor"/>
      <rect x="12" y="11" width="8" height="2" rx="1" :fill="iconColor"/>
    </g>
    <g v-else>
      <rect x="11" y="4" width="2" height="8" rx="1" :fill="iconColor" opacity="0.7"/>
      <rect x="11" y="12" width="2" height="8" rx="1" :fill="iconColor" opacity="0.7"/>
      <rect x="4" y="11" width="8" height="2" rx="1" :fill="iconColor" opacity="0.7"/>
      <rect x="12" y="11" width="8" height="2" rx="1" :fill="iconColor" opacity="0.7"/>
    </g>
    <!-- 中心 -->
    <circle cx="12" cy="12" r="3" :fill="iconColor"/>
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
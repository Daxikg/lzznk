<template>
  <!-- 立体库图标 -->
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
    <!-- 框架 -->
    <rect x="2" y="2" width="20" height="20" rx="2" :fill="iconColor" opacity="0.3"/>
    <!-- 货架列 -->
    <line x1="8" y1="2" x2="8" y2="22" :stroke="iconColor" stroke-width="1.5"/>
    <line x1="16" y1="2" x2="16" y2="22" :stroke="iconColor" stroke-width="1.5"/>
    <!-- 货架行 -->
    <line x1="2" y1="8" x2="22" y2="8" :stroke="iconColor" stroke-width="1.5"/>
    <line x1="2" y1="14" x2="22" y2="14" :stroke="iconColor" stroke-width="1.5"/>
    <!-- 货位点 -->
    <rect x="3" y="3" width="4" height="4" rx="1" :fill="iconColor" opacity="0.8"/>
    <rect x="9" y="3" width="6" height="4" rx="1" :fill="iconColor" opacity="0.6"/>
    <rect x="17" y="3" width="4" height="4" rx="1" :fill="iconColor" opacity="0.8"/>
    <rect x="3" y="9" width="4" height="4" rx="1" :fill="iconColor" opacity="0.7"/>
    <rect x="9" y="9" width="6" height="4" rx="1" :fill="iconColor" opacity="0.9"/>
    <rect x="17" y="9" width="4" height="4" rx="1" :fill="iconColor" opacity="0.5"/>
    <rect x="3" y="15" width="4" height="4" rx="1" :fill="iconColor" opacity="0.6"/>
    <rect x="9" y="15" width="6" height="4" rx="1" :fill="iconColor" opacity="0.8"/>
    <rect x="17" y="15" width="4" height="4" rx="1" :fill="iconColor" opacity="0.7"/>
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
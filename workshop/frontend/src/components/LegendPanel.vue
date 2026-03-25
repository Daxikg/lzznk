<template>
  <div class="legend-panel">
    <div class="legend-title">状态说明</div>
    <div class="legend-items">
      <div class="legend-item" v-for="(config, key) in statusConfig" :key="key">
        <span class="legend-dot" :style="{ backgroundColor: config.color }">
          <span class="legend-dot-glow" :style="{ backgroundColor: config.color }"></span>
        </span>
        <span class="legend-label">{{ config.label }}</span>
        <span class="legend-desc">{{ config.description }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { statusConfig } from '../api/mockData'
</script>

<style scoped>
.legend-panel {
  background: linear-gradient(135deg, rgba(20, 30, 48, 0.95), rgba(36, 59, 85, 0.95));
  border-radius: 10px;
  border: 1px solid rgba(79, 195, 247, 0.2);
  padding: 12px;
}

.legend-title {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #4fc3f7;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  transition: background 0.2s;
}

.legend-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
  box-shadow: 0 0 10px currentColor;
}

.legend-dot-glow {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  opacity: 0.3;
  filter: blur(3px);
}

.legend-label {
  color: #fff;
  font-weight: 600;
  min-width: 70px;
  font-size: 11px;
}

.legend-desc {
  color: rgba(255, 255, 255, 0.5);
  font-size: 10px;
}
</style>
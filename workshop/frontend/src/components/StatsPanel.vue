<template>
  <div class="stats-panel">
    <div class="stat-item total">
      <div class="stat-icon">📊</div>
      <div class="stat-content">
        <div class="stat-value">{{ statistics.total }}</div>
        <div class="stat-label">设备总数</div>
      </div>
    </div>

    <div class="stat-item running">
      <div class="stat-icon">✅</div>
      <div class="stat-content">
        <div class="stat-value">{{ statistics.running }}</div>
        <div class="stat-label">运行中</div>
      </div>
    </div>

    <div class="stat-item offline">
      <div class="stat-icon">⚫</div>
      <div class="stat-content">
        <div class="stat-value">{{ statistics.offline }}</div>
        <div class="stat-label">离线</div>
      </div>
    </div>

    <div class="stat-item fault">
      <div class="stat-icon">⚠️</div>
      <div class="stat-content">
        <div class="stat-value">{{ statistics.fault }}</div>
        <div class="stat-label">故障</div>
      </div>
    </div>

    <div class="stat-item long-fault">
      <div class="stat-icon">🔴</div>
      <div class="stat-content">
        <div class="stat-value">{{ statistics.longFault }}</div>
        <div class="stat-label">长时间故障</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  statistics: {
    type: Object,
    required: true
  },
  runningRate: {
    type: [String, Number],
    default: 0
  }
})
</script>

<style scoped>
.stats-panel {
  display: flex;
  gap: 10px;
  padding: 8px 14px;
  background: linear-gradient(135deg, rgba(20, 30, 48, 0.9), rgba(36, 59, 85, 0.9));
  border-radius: 10px;
  border: 1px solid rgba(79, 195, 247, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  min-width: 80px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 18px;
}

.stat-content {
  text-align: left;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 10px;
  opacity: 0.8;
}

.total .stat-value {
  color: #fff;
}

.running .stat-value {
  color: #22c55e;
  text-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
}

.fault .stat-value {
  color: #eab308;
  text-shadow: 0 0 20px rgba(234, 179, 8, 0.5);
}

.long-fault .stat-value {
  color: #ef4444;
  text-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
}

.offline .stat-value {
  color: #9ca3af;
}
</style>
<template>
  <g
    class="device-item"
    :class="{ 'compact-device': isCompact, 'lathe-device': device.type === 'lathe', 'turntable-device': device.type === 'turntable' }"
    :transform="`translate(${device.x}, ${device.y})`"
    @click="$emit('click', device)"
    style="cursor: pointer"
  >
    <!-- 设备阴影和渐变定义 -->
    <defs>
      <filter :id="`shadow-${device.id}`" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" :flood-color="statusColor" flood-opacity="0.4"/>
      </filter>
      <linearGradient :id="`grad-${device.id}`" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="statusLightColor"/>
        <stop offset="100%" :stop-color="statusColor"/>
      </linearGradient>
      <!-- 发光滤镜 -->
      <filter :id="`glow-${device.id}`" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur stdDeviation="2" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <!-- 转盘径向渐变 -->
      <radialGradient :id="`radial-${device.id}`" cx="50%" cy="30%" r="60%">
        <stop offset="0%" :stop-color="statusLightColor"/>
        <stop offset="100%" :stop-color="statusColor"/>
      </radialGradient>
    </defs>

    <!-- 转盘设备（圆形） -->
    <template v-if="device.type === 'turntable'">
      <!-- 外圈光晕 -->
      <circle
        :r="device.width / 2 + 5"
        :cx="device.width / 2"
        :cy="device.height / 2"
        :fill="statusColor"
        opacity="0.15"
      >
        <animate v-if="!isFault" attributeName="r" :values="`${device.width / 2 + 3};${device.width / 2 + 8};${device.width / 2 + 3}`" dur="2s" repeatCount="indefinite"/>
        <animate v-if="!isFault" attributeName="opacity" values="0.15;0.25;0.15" dur="2s" repeatCount="indefinite"/>
      </circle>
      <!-- 主体圆 -->
      <circle
        :r="device.width / 2"
        :cx="device.width / 2"
        :cy="device.height / 2"
        :fill="`url(#radial-${device.id})`"
        :filter="`url(#shadow-${device.id})`"
        class="device-body"
      />
      <!-- 内圈 -->
      <circle
        :r="device.width / 2 - 8"
        :cx="device.width / 2"
        :cy="device.height / 2"
        fill="none"
        stroke="rgba(255,255,255,0.2)"
        stroke-width="2"
      />
      <!-- 中心点 -->
      <circle
        r="4"
        :cx="device.width / 2"
        :cy="device.height / 2"
        :fill="statusColor"
        :filter="`url(#glow-${device.id})`"
      />
      <!-- 旋转指示线 -->
      <g :transform="`translate(${device.width / 2}, ${device.height / 2})`">
        <line x1="0" y1="-15" x2="0" y2="-25" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="!isFault" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
        <line x1="0" y1="15" x2="0" y2="25" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="!isFault" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
        <line x1="-15" y1="0" x2="-25" y2="0" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="!isFault" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
        <line x1="15" y1="0" x2="25" y2="0" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="!isFault" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
      </g>
    </template>

    <!-- 车轮车床特殊显示 -->
    <template v-else-if="device.type === 'lathe'">
      <!-- 车床主体 -->
      <rect
        :width="device.width"
        :height="device.height"
        rx="8"
        ry="8"
        :fill="`url(#grad-${device.id})`"
        :filter="`url(#shadow-${device.id})`"
        class="device-body"
      />
      <!-- 车床内部区域 -->
      <rect :x="device.width / 5" y="8" :width="device.width * 4 / 5 - 10" :height="device.height - 16" fill="rgba(0,0,0,0.15)" rx="4"/>

      <!-- 设备图标 -->
      <g class="device-icon-group" :transform="`translate(${device.width / 2 + 10}, 12)`">
        <component :is="LatheIcon" :status="device.computedStatus" :size="28" />
      </g>

      <!-- 设备名称 -->
      <text
        :x="device.width / 2"
        :y="device.height - 8"
        text-anchor="middle"
        fill="#fff"
        font-size="13"
        font-weight="600"
      >
        {{ device.name }}
      </text>

      <!-- 状态指示灯 -->
      <g class="status-indicator" :transform="`translate(${device.width - 16}, 10)`">
        <circle r="7" :fill="statusColor" opacity="0.15"/>
        <circle r="4" :fill="statusColor">
          <animate v-if="isFault" attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite"/>
        </circle>
      </g>
    </template>

    <!-- 天车设备特殊显示 -->
    <template v-else-if="device.type === 'crane'">
      <!-- 天车主体 -->
      <rect
        :width="device.width"
        :height="device.height"
        rx="6"
        ry="6"
        :fill="`url(#grad-${device.id})`"
        :filter="`url(#shadow-${device.id})`"
        class="device-body"
      />
      <!-- 天车图标 -->
      <g class="device-icon-group" :transform="`translate(${device.width / 2 - 12}, 5)`">
        <component :is="CraneIcon" :status="device.computedStatus" :size="24" />
      </g>
      <text
        :x="device.width / 2"
        :y="device.height - 6"
        text-anchor="middle"
        fill="#fff"
        font-size="8"
        font-weight="500"
      >
        {{ device.name }}
      </text>
    </template>

    <!-- 普通设备 -->
    <template v-else>
      <!-- 设备主体背景 -->
      <rect
        :width="device.width"
        :height="device.height"
        :rx="isCompact ? 4 : 8"
        ry="8"
        :fill="`url(#grad-${device.id})`"
        :filter="`url(#shadow-${device.id})`"
        class="device-body"
      />

      <!-- 顶部装饰线 -->
      <rect x="3" y="3" :width="device.width - 6" :height="isCompact ? 1 : 2" rx="1" fill="rgba(255,255,255,0.15)"/>

      <!-- 非紧凑设备显示 -->
      <template v-if="!isCompact">
        <!-- 设备图标区域 -->
        <g class="device-icon-group" :transform="`translate(${device.width / 2 - 15}, 8)`">
          <component :is="currentIcon" :status="device.computedStatus" :size="30" />
        </g>

        <!-- 设备名称 -->
        <text
          :x="device.width / 2"
          :y="device.height - 16"
          text-anchor="middle"
          fill="#fff"
          font-size="10"
          font-weight="600"
          class="device-name"
        >
          {{ shortName }}
        </text>

        <!-- 状态指示灯组件 -->
        <g class="status-indicator" :transform="`translate(${device.width - 14}, 10)`">
          <circle r="8" :fill="statusColor" opacity="0.15" class="glow-ring">
            <animate v-if="isFault" attributeName="r" values="8;12;8" dur="1.5s" repeatCount="indefinite"/>
            <animate v-if="isFault" attributeName="opacity" values="0.15;0.3;0.15" dur="1.5s" repeatCount="indefinite"/>
          </circle>
          <circle r="4" :fill="statusColor" class="status-light" :filter="`url(#glow-${device.id})`">
            <animate v-if="isFault" attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite"/>
          </circle>
          <circle r="1.5" cy="-1" cx="0" fill="rgba(255,255,255,0.6)"/>
        </g>

        <!-- 状态文字 -->
        <text
          :x="device.width / 2"
          :y="device.height - 4"
          text-anchor="middle"
          fill="rgba(255,255,255,0.8)"
          font-size="8"
        >
          {{ statusLabel }}
        </text>

        <!-- 立体库/堆垛系统容量条 -->
        <g v-if="(device.type === 'warehouse' || device.type === 'stacker') && device.capacity" class="capacity-bar">
          <rect x="8" :y="device.height - 32" :width="device.width - 16" height="6" rx="3" fill="rgba(0,0,0,0.3)"/>
          <rect x="8" :y="device.height - 32" :width="(device.width - 16) * (device.used / device.capacity)" height="6" rx="3" fill="rgba(74, 222, 128, 0.9)">
            <animate attributeName="opacity" values="0.9;0.6;0.9" dur="3s" repeatCount="indefinite"/>
          </rect>
          <text :x="device.width / 2" :y="device.height - 26" text-anchor="middle" fill="#fff" font-size="7" font-weight="500">
            {{ device.used }}/{{ device.capacity }}
          </text>
        </g>
      </template>

      <!-- 紧凑设备显示（集成装置） -->
      <template v-else>
        <!-- 紧凑设备的简短名称 -->
        <text
          :x="device.width / 2"
          :y="device.height / 2 + 3"
          text-anchor="middle"
          fill="#fff"
          font-size="7"
          font-weight="500"
          class="device-name"
        >
          {{ compactLabel }}
        </text>

        <!-- 小状态灯 -->
        <circle
          :cx="device.width - 6"
          :cy="6"
          r="3"
          :fill="statusColor"
          class="status-light"
        >
          <animate v-if="isFault" attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite"/>
        </circle>
      </template>
    </template>
  </g>
</template>

<script setup>
import { computed } from 'vue'
import { statusConfig } from '../api/mockData'

// 导入所有图标组件
import MeasureIcon from './icons/MeasureIcon.vue'
import PressIcon from './icons/PressIcon.vue'
import PlatformIcon from './icons/PlatformIcon.vue'
import ConveyorIcon from './icons/ConveyorIcon.vue'
import WarehouseIcon from './icons/WarehouseIcon.vue'
import CabinetIcon from './icons/CabinetIcon.vue'
import RoomIcon from './icons/RoomIcon.vue'
import PowerIcon from './icons/PowerIcon.vue'
import DefaultIcon from './icons/DefaultIcon.vue'

// 创建简单的图标组件
const LatheIcon = {
  props: ['status', 'size'],
  template: `
    <svg :width="size" :height="size" viewBox="0 0 40 40">
      <rect x="5" y="10" width="30" height="20" rx="3" fill="currentColor" opacity="0.8"/>
      <rect x="8" y="13" width="12" height="14" rx="2" fill="rgba(0,0,0,0.3)"/>
      <circle cx="32" cy="20" r="5" fill="rgba(255,255,255,0.3)"/>
      <rect x="10" y="16" width="6" height="8" rx="1" fill="rgba(255,255,255,0.2)"/>
    </svg>
  `
}

const CraneIcon = {
  props: ['status', 'size'],
  template: `
    <svg :width="size" :height="size" viewBox="0 0 40 40">
      <rect x="5" y="5" width="30" height="4" rx="1" fill="currentColor" opacity="0.9"/>
      <rect x="18" y="9" width="4" height="20" fill="currentColor" opacity="0.7"/>
      <rect x="10" y="29" width="20" height="6" rx="2" fill="currentColor" opacity="0.8"/>
      <circle cx="20" cy="32" r="2" fill="rgba(255,255,255,0.5)"/>
    </svg>
  `
}

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

// 是否为紧凑设备（集成装置）
const isCompact = computed(() => {
  return props.device.width <= 70 || props.device.height <= 25 ||
         props.device.type === 'protect' || props.device.type === 'forklift'
})

// 状态颜色
const statusColor = computed(() => {
  const colors = {
    running: '#22c55e',
    fault: '#eab308',
    longFault: '#ef4444',
    offline: '#6b7280'
  }
  return colors[props.device.computedStatus] || '#6b7280'
})

const statusLightColor = computed(() => {
  const colors = {
    running: '#4ade80',
    fault: '#fcd34d',
    longFault: '#fca5a5',
    offline: '#9ca3af'
  }
  return colors[props.device.computedStatus] || '#9ca3af'
})

const statusLabel = computed(() => {
  return statusConfig[props.device.computedStatus]?.label || '未知'
})

const isFault = computed(() => {
  return props.device.computedStatus === 'fault' || props.device.computedStatus === 'longFault'
})

// 简短名称（用于显示）
const shortName = computed(() => {
  const name = props.device.name
  if (name.length > 10) {
    return name.substring(0, 8) + '...'
  }
  return name
})

// 紧凑设备标签
const compactLabel = computed(() => {
  const name = props.device.name
  if (props.device.type === 'protect') {
    return '防护套'
  }
  if (props.device.type === 'forklift') {
    return '货叉'
  }
  return name.substring(0, 4)
})

// 根据设备类型返回对应图标组件
const currentIcon = computed(() => {
  const iconMap = {
    grind: PressIcon,        // 磨合设备 → 压装图标
    detect: MeasureIcon,     // 检测设备 → 测量图标
    unload: ConveyorIcon,    // 退卸设备 → 传输图标
    rust: PlatformIcon,      // 除锈设备 → 平台图标
    flaw: CabinetIcon,       // 探伤设备 → 电控柜图标
    oil: ConveyorIcon,       // 涂油设备 → 传输图标
    bolt: PressIcon,         // 紧固设备 → 压装图标
    press: PressIcon,        // 压装设备
    measure: MeasureIcon,    // 测量设备
    crane: CraneIcon,        // 天车设备
    lathe: LatheIcon,        // 车轮车床
    protect: RoomIcon,       // 防护装置
    forklift: WarehouseIcon, // 货叉装置
    stacker: WarehouseIcon,  // 堆垛系统
    warehouse: WarehouseIcon,// 立体库
    // 保留旧类型兼容
    platform: PlatformIcon,
    conveyor: ConveyorIcon,
    cabinet: CabinetIcon,
    room: RoomIcon,
    power: PowerIcon
  }
  return iconMap[props.device.type] || DefaultIcon
})
</script>

<style scoped>
.device-item {
  /* 移除悬浮效果，只保留点击交互 */
}

.device-body {
  transition: all 0.3s ease;
}

.device-name {
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
  pointer-events: none;
}

.status-light {
  transition: fill 0.3s ease;
}

.device-icon-group {
  pointer-events: none;
}

.compact-device .device-body {
  stroke-width: 1;
}

.lathe-device .device-body {
  stroke: rgba(255,255,255,0.1);
  stroke-width: 1;
}
</style>
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
        <animate v-if="shouldRotate" attributeName="r" :values="`${device.width / 2 + 3};${device.width / 2 + 8};${device.width / 2 + 3}`" dur="2s" repeatCount="indefinite"/>
        <animate v-if="shouldRotate" attributeName="opacity" values="0.15;0.25;0.15" dur="2s" repeatCount="indefinite"/>
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
          <animateTransform v-if="shouldRotate" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
        <line x1="0" y1="15" x2="0" y2="25" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="shouldRotate" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
        <line x1="-15" y1="0" x2="-25" y2="0" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="shouldRotate" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
        </line>
        <line x1="15" y1="0" x2="25" y2="0" stroke="rgba(255,255,255,0.6)" stroke-width="2" stroke-linecap="round">
          <animateTransform v-if="shouldRotate" attributeName="transform" type="rotate" from="0" to="360" dur="4s" repeatCount="indefinite"/>
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

      <!-- 设备名称 -->
      <text
        :x="device.width / 2"
        :y="device.height / 2 + 5"
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
      <!-- 悬臂吊特殊显示 -->
      <template v-if="device.name.includes('悬臂吊')">
        <!-- 中心立柱 -->
        <rect
          :x="device.width / 2 - 3"
          y="0"
          width="6"
          :height="device.height - 2"
          rx="3"
          :fill="statusColor"
          :filter="`url(#shadow-${device.id})`"
        />
        <!-- 立柱顶部装饰 -->
        <circle
          :cx="device.width / 2"
          cy="3"
          r="4"
          :fill="statusLightColor"
          :filter="`url(#glow-${device.id})`"
        />

        <!-- 旋转臂（运行时旋转动画） -->
        <g :transform="`translate(${device.width / 2}, 4)`">
          <line
            x1="0"
            y1="0"
            :x2="device.width / 2 - 8"
            y2="0"
            :stroke="statusColor"
            stroke-width="4"
            stroke-linecap="round"
          >
            <animateTransform
              v-if="shouldRotate"
              attributeName="transform"
              type="rotate"
              values="0;360"
              dur="8s"
              repeatCount="indefinite"
            />
          </line>
          <!-- 臂端吊绳 -->
          <g :transform="`translate(${device.width / 2 - 8}, 0)`">
            <line
              x1="0"
              y1="0"
              x2="0"
              :y2="device.height - 8"
              stroke="rgba(255,255,255,0.5)"
              stroke-width="1.5"
            >
              <animateTransform
                v-if="shouldRotate"
                attributeName="transform"
                type="rotate"
                values="0;360"
                dur="8s"
                repeatCount="indefinite"
              />
            </line>
            <!-- 吊钩 -->
            <circle
              cx="0"
              :cy="device.height - 6"
              r="3"
              :fill="statusColor"
            >
              <animateTransform
                v-if="shouldRotate"
                attributeName="transform"
                type="rotate"
                values="0;360"
                dur="8s"
                repeatCount="indefinite"
              />
            </circle>
          </g>
        </g>

        <!-- 设备名称 -->
        <text
          :x="device.width / 2"
          :y="-3"
          text-anchor="middle"
          fill="rgba(255,255,255,0.9)"
          font-size="9"
          font-weight="500"
        >
          {{ device.name }}
        </text>

        <!-- 状态指示灯 -->
        <circle
          :cx="4"
          :cy="4"
          r="2"
          :fill="statusColor"
        >
          <animate v-if="isFault" attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite"/>
        </circle>
      </template>

      <!-- 普通天车（航架天车等） -->
      <template v-else>
        <!-- 天车桥架（顶部横梁） -->
        <rect
          x="0"
          y="0"
          :width="device.width"
          height="6"
          rx="2"
          :fill="statusColor"
          :filter="`url(#shadow-${device.id})`"
        />
        <!-- 横梁底部装饰线 -->
        <rect
          x="2"
          y="4"
          :width="device.width - 4"
          height="1.5"
          rx="1"
          fill="rgba(255,255,255,0.2)"
        />

        <!-- 小车+吊钩整体（运行时一起左右移动） -->
        <g :transform="`translate(${device.width / 2 - 10}, 1)`">
          <animateTransform
            v-if="shouldRotate"
            attributeName="transform"
            type="translate"
            values="0,0; 10,0; 0,0; -10,0; 0,0"
            dur="4s"
            repeatCount="indefinite"
            additive="sum"
          />
          <!-- 小车 -->
          <rect
            width="20"
            height="4"
            rx="1"
            :fill="statusLightColor"
          />
          <!-- 吊钩钢丝绳 -->
          <line
            x1="10"
            y1="4"
            x2="10"
            :y2="device.height - 12"
            stroke="rgba(255,255,255,0.5)"
            stroke-width="1.5"
          />
          <!-- 吊钩 -->
          <g :transform="`translate(10, ${device.height - 10})`">
            <!-- 吊钩主体（钩形） -->
            <path
              d="M 0 -2 L 0 3 Q 4 5 5 3 Q 5 0 3 -2"
              fill="none"
              :stroke="statusColor"
              stroke-width="2"
              stroke-linecap="round"
              :filter="`url(#glow-${device.id})`"
            />
            <!-- 吊钩顶部固定点 -->
            <circle r="2" :fill="statusLightColor"/>
          </g>
        </g>

        <!-- 设备名称（显示在横梁上方） -->
        <text
          :x="device.width / 2"
          :y="-3"
          text-anchor="middle"
          fill="rgba(255,255,255,0.9)"
          font-size="9"
          font-weight="500"
        >
          {{ device.name }}
        </text>

        <!-- 状态指示灯 -->
        <circle
          :cx="device.width - 4"
          :cy="3"
          r="2"
          :fill="statusColor"
        >
          <animate v-if="isFault" attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite"/>
        </circle>
      </template>
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

      <!-- 非紧凑非集成设备显示 -->
      <template v-if="!isCompact && !isIntegrated">
        <!-- 设备名称 -->
        <text
          :x="device.width / 2"
          :y="device.height / 2 + 4"
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
      </template>

      <!-- 紧凑设备显示（字号9，支持换行） -->
      <template v-else-if="isCompact">
        <!-- 紧凑设备名称（支持两行） -->
        <text
          v-if="compactNameLines.length === 1"
          :x="device.width / 2"
          :y="device.height / 2 + 3"
          text-anchor="middle"
          fill="#fff"
          font-size="9"
          font-weight="500"
          class="device-name"
        >
          {{ compactNameLines[0] }}
        </text>
        <template v-else>
          <text
            :x="device.width / 2"
            :y="device.height / 2 - 5"
            text-anchor="middle"
            fill="#fff"
            font-size="9"
            font-weight="500"
            class="device-name"
          >
            {{ compactNameLines[0] }}
          </text>
          <text
            :x="device.width / 2"
            :y="device.height / 2 + 8"
            text-anchor="middle"
            fill="#fff"
            font-size="9"
            font-weight="500"
            class="device-name"
          >
            {{ compactNameLines[1] }}
          </text>
        </template>

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

      <!-- 集成设备显示（防护套、货叉，字号7，简称） -->
      <template v-else-if="isIntegrated">
        <text
          :x="device.width / 2"
          :y="device.height / 2 + 3"
          text-anchor="middle"
          fill="#fff"
          font-size="7"
          font-weight="500"
          class="device-name"
        >
          {{ integratedLabel }}
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

const props = defineProps({
  device: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

// 是否为集成设备（防护套、货叉）
const isIntegrated = computed(() => {
  return props.device.type === 'protect' || props.device.type === 'forklift'
})

// 是否为紧凑设备（宽度<=70或高度<=25，但不是集成设备）
const isCompact = computed(() => {
  return (props.device.width <= 70 || props.device.height <= 25) && !isIntegrated.value
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

const isFault = computed(() => {
  return props.device.computedStatus === 'fault' || props.device.computedStatus === 'longFault'
})

// 转盘是否需要旋转（只有运行中才旋转）
const shouldRotate = computed(() => {
  return props.device.computedStatus === 'running'
})

// 简短名称（用于显示）
const shortName = computed(() => {
  const name = props.device.name
  if (name.length > 10) {
    return name.substring(0, 8) + '...'
  }
  return name
})

// 集成设备标签（防护套、货叉用简称）
const integratedLabel = computed(() => {
  if (props.device.type === 'protect') {
    return '防护套'
  }
  if (props.device.type === 'forklift') {
    return '货叉'
  }
  return props.device.name.substring(0, 4)
})

// 紧凑设备名称换行（最多2行）
const compactNameLines = computed(() => {
  const name = props.device.name
  const fontSize = 9
  const charWidth = fontSize * 0.6 // 估算中文字符宽度
  const maxWidth = props.device.width - 8 // 留出边距

  const maxCharsPerLine = Math.floor(maxWidth / charWidth)
  if (maxCharsPerLine <= 0) return [name]

  if (name.length <= maxCharsPerLine) {
    return [name]
  }

  // 分成两行，尽量平均分配
  const mid = Math.ceil(name.length / 2)
  return [name.substring(0, mid), name.substring(mid)]
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
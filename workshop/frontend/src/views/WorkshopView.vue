<template>
  <div class="workshop-screen" ref="screenRef">
    <!-- 科技感背景 -->
    <div class="bg-decoration">
      <!-- 六边形网格 -->
      <div class="hex-grid"></div>
      <!-- 动态网格 -->
      <div class="grid-lines"></div>
      <!-- 扫描线 -->
      <div class="scan-line"></div>
      <!-- 数据流动线 -->
      <div class="data-flow">
        <div class="flow-line" v-for="i in 5" :key="i" :style="{ '--delay': i * 2 + 's', '--y': 15 + i * 18 + '%' }"></div>
      </div>
      <!-- 科技粒子 -->
      <div class="particles">
        <div class="particle" v-for="i in 30" :key="i" :style="{ '--delay': i * 0.3 + 's', '--x': Math.random() * 100 + '%', '--y': Math.random() * 100 + '%' }"></div>
      </div>
      <!-- 角落装饰 -->
      <div class="corner-decoration top-left"></div>
      <div class="corner-decoration top-right"></div>
      <div class="corner-decoration bottom-left"></div>
      <div class="corner-decoration bottom-right"></div>
      <!-- 边框呼吸灯 -->
      <div class="border-glow"></div>
      <!-- 渐变遮罩 -->
      <div class="gradient-overlay"></div>
    </div>

    <!-- 顶部标题栏 -->
    <header class="screen-header">
      <!-- 标题装饰线 -->
      <div class="header-deco-line left"></div>
      <div class="header-deco-line right"></div>

      <div class="header-left">
        <!-- 左侧留空 -->
      </div>

      <div class="header-center">
        <div class="logo-area">
          <div class="logo-icon-wrapper">
            <div class="logo-icon">🚨</div>
            <div class="logo-ring"></div>
            <div class="logo-ring inner"></div>
          </div>
          <div class="title-wrapper">
            <div class="title-deco">
              <span></span><span></span><span></span>
            </div>
            <h1 class="title">
              <span class="title-text">轮轴库设备运行状态监控</span>
              <span class="title-glow"></span>
            </h1>
            <div class="title-deco right">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="header-right">
        <div class="time-wrapper">
          <div class="time-frame"></div>
          <div class="time-label">系统时间</div>
          <div class="time-display">
            <span class="current-date">{{ currentDate }}</span>
            <span class="current-time">
              <span class="time-segment" v-for="(char, idx) in currentTime" :key="idx">{{ char }}</span>
            </span>
          </div>
          <div class="update-time">
            <span class="pulse-dot" :class="{ active: deviceStore.loading }"></span>
            数据更新: {{ formattedUpdateTime }}
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- SVG车间图 -->
      <div class="workshop-container">
        <svg
          class="workshop-svg"
          viewBox="-90 0 1490 700"
          preserveAspectRatio="xMidYMid meet"
        >
          <!-- 全局滤镜定义 -->
          <defs>
            <!-- 发光效果 -->
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            <!-- 网格图案 -->
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(79, 195, 247, 0.05)" stroke-width="0.5"/>
            </pattern>
            <!-- 钢轨渐变 -->
            <linearGradient id="railGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#4a5a6a"/>
              <stop offset="50%" stop-color="#6a7a8a"/>
              <stop offset="100%" stop-color="#4a5a6a"/>
            </linearGradient>
          </defs>

          <!-- 背景网格 -->
          <rect width="100%" height="100%" fill="url(#grid)"/>

          <!-- 外部实体墙体 -->
          <rect x="0" y="15" width="1400" height="600" fill="#1a2a3a" stroke="none" rx="8"/>
          <!-- 墙体边框装饰 -->
          <rect x="0" y="15" width="1400" height="600" fill="none" stroke="rgba(79, 195, 247, 0.6)" stroke-width="10" rx="8"/>
          <!-- 内部区域分隔线 -->
          <!-- 轮轴前库与轮轴后库分隔线：实线，中间开50像素缺口代表门（位于第3、4条钢轨中间） -->
          <line :x1="LAYOUT.leftWidth" y1="20" :x2="LAYOUT.leftWidth" y2="175" stroke="rgba(79, 195, 247, 0.6)" stroke-width="5"/>
          <line :x1="LAYOUT.leftWidth" y1="225" :x2="LAYOUT.leftWidth" y2="335" stroke="rgba(79, 195, 247, 0.6)" stroke-width="5"/>
          <line :x1="LAYOUT.leftWidth" y1="385" :x2="LAYOUT.leftWidth" y2="550" stroke="rgba(79, 195, 247, 0.6)" stroke-width="5"/>
          <line :x1="LAYOUT.leftWidth" y1="570" :x2="LAYOUT.leftWidth" y2="610" stroke="rgba(79, 195, 247, 0.6)" stroke-width="5"/>
          <!-- 轮轴后库与旋轮间分隔线：实线 -->
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth" y1="20" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth" y2="610" stroke="rgba(79, 195, 247, 0.6)" stroke-width="5"/>
          <!-- 旋轮间中间纵向双虚线，每根宽度3，间隔1 -->
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 - 2" y1="60" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 - 2" y2="580" stroke="rgba(155, 89, 182, 0.5)" stroke-width="3" stroke-dasharray="8,4"/>
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 + 3" y1="60" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 + 3" y2="580" stroke="rgba(155, 89, 182, 0.5)" stroke-width="3" stroke-dasharray="8,4"/>
          <!-- 旋轮间右边纵向双虚线，每根宽度3，间隔1 -->
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth - 20" y1="60" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth - 20" y2="580" stroke="rgba(155, 89, 182, 0.5)" stroke-width="3" stroke-dasharray="8,4"/>
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth - 15" y1="60" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth - 15" y2="580" stroke="rgba(155, 89, 182, 0.5)" stroke-width="3" stroke-dasharray="8,4"/>
          <!-- 旋轮间左边纵向双虚线，每根宽度3，间隔1 -->
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth + 15 " y1="60" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth + 15 " y2="580" stroke="rgba(155, 89, 182, 0.5)" stroke-width="3" stroke-dasharray="8,4"/>
          <line :x1="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 " y1="60" :x2="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 " y2="580" stroke="rgba(155, 89, 182, 0.5)" stroke-width="3" stroke-dasharray="8,4"/>

          <!-- 区域背景 -->
          <g class="areas">
            <g v-for="area in deviceStore.areas" :key="area.name">
              <!-- 区域背景 -->
              <rect
                :x="area.x"
                :y="area.y"
                :width="area.width"
                :height="area.height"
                :fill="area.color"
                :stroke="area.borderColor"
                stroke-width="1"
                stroke-dasharray="6,3"
                rx="8"
                class="area-bg"
              />
              <!-- 区域标签背景 -->
              <rect
                :x="area.x + area.width / 2 - 40"
                :y="area.y - 25"
                width="80"
                height="25"
                rx="8"
                :fill="area.borderColor"
                opacity="0.9"
              />
              <!-- 区域标签文字 -->
              <text
                :x="area.x + area.width / 2"
                :y="area.y - 7"
                text-anchor="middle"
                fill="#fff"
                font-size="15"
                font-weight="600"
              >
                {{ area.name }}
              </text>
            </g>
          </g>

          <!-- 钢轨 - 6条贯穿全屏（简洁双轨样式） -->
          <g class="rails">
            <defs>
              <!-- 钢轨渐变（垂直方向） -->
              <!-- 钢铁灰 - 真实钢轨质感 -->
              <linearGradient id="steelGray" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#5a5a5a"/>
                <stop offset="50%" stop-color="#3a3a3a"/>
                <stop offset="100%" stop-color="#4a4a4a"/>
              </linearGradient>
              <!-- 金属银 - 金属光泽感 -->
              <linearGradient id="metalSilver" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#b8b8b8"/>
                <stop offset="50%" stop-color="#8a8a8a"/>
                <stop offset="100%" stop-color="#a0a0a0"/>
              </linearGradient>
              <!-- 科技蓝灰 - 科技感强 -->
              <linearGradient id="techBlueGray" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#5a6a7a"/>
                <stop offset="50%" stop-color="#3a4a5a"/>
                <stop offset="100%" stop-color="#4a5a6a"/>
              </linearGradient>
              <!-- 锈铁棕 - 老旧钢轨真实感 -->
              <linearGradient id="rustBrown" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#8a6a5a"/>
                <stop offset="50%" stop-color="#6a4a3a"/>
                <stop offset="100%" stop-color="#7a5a4a"/>
              </linearGradient>
              <!-- 纵向钢轨渐变（水平方向） - 科技蓝灰 -->
              <linearGradient id="railHeadGradientV" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#5a6a7a"/>
                <stop offset="50%" stop-color="#3a4a5a"/>
                <stop offset="100%" stop-color="#4a5a6a"/>
              </linearGradient>
              <!-- 输送带流动渐变 -->
              <linearGradient id="conveyorFlow" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#5a6a7a">
                  <animate attributeName="offset" values="0;1" dur="1s" repeatCount="indefinite"/>
                </stop>
                <stop offset="25%" stop-color="#7a8a9a">
                  <animate attributeName="offset" values="0.25;1.25" dur="1s" repeatCount="indefinite"/>
                </stop>
                <stop offset="50%" stop-color="#5a6a7a">
                  <animate attributeName="offset" values="0.5;1.5" dur="1s" repeatCount="indefinite"/>
                </stop>
                <stop offset="75%" stop-color="#7a8a9a">
                  <animate attributeName="offset" values="0.75;1.75" dur="1s" repeatCount="indefinite"/>
                </stop>
              </linearGradient>
              <!-- 输送带条纹图案（从上往下） -->
              <pattern id="conveyorPattern" x="0" y="0" width="15" height="20" patternUnits="userSpaceOnUse">
                <rect width="15" height="20" fill="#5a6a7a"/>
                <line x1="0" y1="5" x2="15" y2="5" stroke="#7a8a9a" stroke-width="3"/>
                <line x1="0" y1="15" x2="15" y2="15" stroke="#7a8a9a" stroke-width="3"/>
                <animateTransform attributeName="patternTransform" type="translate" values="0 0;0 20" dur="1.5s" repeatCount="indefinite"/>
              </pattern>
              <!-- 输送带条纹图案（从下往上） -->
              <pattern id="conveyorPatternReverse" x="0" y="0" width="15" height="20" patternUnits="userSpaceOnUse">
                <rect width="15" height="20" fill="#5a6a7a"/>
                <line x1="0" y1="5" x2="15" y2="5" stroke="#7a8a9a" stroke-width="3"/>
                <line x1="0" y1="15" x2="15" y2="15" stroke="#7a8a9a" stroke-width="3"/>
                <animateTransform attributeName="patternTransform" type="translate" values="0 20;0 0" dur="1.5s" repeatCount="indefinite"/>
              </pattern>
            </defs>

            <!-- 1号钢轨：从轮轴前库左边开始，一直延伸到旋轮间离外墙30像素处 - 科技蓝灰 -->
            <g v-for="(rail, index) in rails" :key="rail.id">
              <template v-if="index === 0">
                <!-- 上轨 -->
                <rect x="15" :y="rail.y - 4" :width="1400 - 30 - 15" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 下轨 -->
                <rect x="15" :y="rail.y + 16" :width="1400 - 30 - 15" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 钢轨编号 -->
                <g :transform="`translate(5, ${rail.y + 10})`">
                  <circle r="12" fill="rgba(60, 70, 80, 0.9)" stroke="rgba(150, 160, 170, 0.5)" stroke-width="1"/>
                  <text y="4" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="11" font-weight="bold">{{ rail.id.split('-')[1] }}</text>
                </g>
              </template>
            </g>

            <!-- 2号钢轨：科技蓝灰 -->
            <g v-for="(rail, index) in rails" :key="rail.id">
              <template v-if="index === 1">
                <!-- 上轨 -->
                <rect x="-80" :y="rail.y - 4" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 下轨 -->
                <rect x="-80" :y="rail.y + 16" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 钢轨编号 -->
                <g :transform="`translate(-65, ${rail.y + 10})`">
                  <circle r="12" fill="rgba(60, 70, 80, 0.9)" stroke="rgba(150, 160, 170, 0.5)" stroke-width="1"/>
                  <text y="4" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="11" font-weight="bold">{{ rail.id.split('-')[1] }}</text>
                </g>
              </template>
            </g>

            <!-- 3号钢轨：科技蓝灰 -->
            <g v-for="(rail, index) in rails" :key="rail.id">
              <template v-if="index === 2">
                <!-- 上轨 -->
                <rect x="-80" :y="rail.y - 4" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 下轨 -->
                <rect x="-80" :y="rail.y + 16" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 钢轨编号 -->
                <g :transform="`translate(-65, ${rail.y + 10})`">
                  <circle r="12" fill="rgba(60, 70, 80, 0.9)" stroke="rgba(150, 160, 170, 0.5)" stroke-width="1"/>
                  <text y="4" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="11" font-weight="bold">{{ rail.id.split('-')[1] }}</text>
                </g>
              </template>
            </g>

            <!-- 4号钢轨：科技蓝灰 -->
            <g v-for="(rail, index) in rails" :key="rail.id">
              <template v-if="index === 3">
                <!-- 上轨 -->
                <rect x="-80" :y="rail.y - 4" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 下轨 -->
                <rect x="-80" :y="rail.y + 16" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 钢轨编号 -->
                <g :transform="`translate(-65, ${rail.y + 10})`">
                  <circle r="12" fill="rgba(60, 70, 80, 0.9)" stroke="rgba(150, 160, 170, 0.5)" stroke-width="1"/>
                  <text y="4" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="11" font-weight="bold">{{ rail.id.split('-')[1] }}</text>
                </g>
              </template>
            </g>

            <!-- 5号钢轨：科技蓝灰 -->
            <g v-for="(rail, index) in rails" :key="rail.id">
              <template v-if="index === 4">
                <!-- 上轨 -->
                <rect x="-80" :y="rail.y - 4" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 下轨 -->
                <rect x="-80" :y="rail.y + 16" :width="LAYOUT.leftWidth + LAYOUT.middleWidth + 20 + 80" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 钢轨编号 -->
                <g :transform="`translate(-65, ${rail.y + 10})`">
                  <circle r="12" fill="rgba(60, 70, 80, 0.9)" stroke="rgba(150, 160, 170, 0.5)" stroke-width="1"/>
                  <text y="4" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="11" font-weight="bold">{{ rail.id.split('-')[1] }}</text>
                </g>
              </template>
            </g>

            <!-- 6号钢轨：科技蓝灰 -->
            <g v-for="(rail, index) in rails" :key="rail.id">
              <template v-if="index === 5">
                <!-- 上轨 -->
                <rect x="-80" :y="rail.y - 4" :width="1450" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 下轨 -->
                <rect x="-80" :y="rail.y + 16" :width="1450" height="8" fill="url(#techBlueGray)" rx="2"/>
                <!-- 钢轨编号 -->
                <g :transform="`translate(-65, ${rail.y + 10})`">
                  <circle r="12" fill="rgba(60, 70, 80, 0.9)" stroke="rgba(150, 160, 170, 0.5)" stroke-width="1"/>
                  <text y="4" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="11" font-weight="bold">{{ rail.id.split('-')[1] }}</text>
                </g>
              </template>
            </g>

            <!-- 纵向钢轨1：轮轴前库左侧墙体右边30像素处，从钢轨1到钢轨3 -->
            <!-- 左轨（从墙左边算30像素，墙在x=0，所以是x=30） -->
            <rect x="30" :y="LAYOUT.railY[0] - 4" width="8" :height="LAYOUT.railY[2] - LAYOUT.railY[0] + 28" fill="url(#railHeadGradientV)" rx="2"/>
            <!-- 右轨 -->
            <rect x="50" :y="LAYOUT.railY[0] - 4" width="8" :height="LAYOUT.railY[2] - LAYOUT.railY[0] + 28" fill="url(#railHeadGradientV)" rx="2"/>

            <!-- 纵向钢轨2：轮对自动检测机与轴承退卸机中间，从钢轨1上轨到钢轨6下轨 -->
            <!-- 左轨 x=250 -->
            <rect x="250" :y="LAYOUT.railY[0] - 4" width="8" :height="LAYOUT.railY[5] - LAYOUT.railY[0] + 28" fill="url(#railHeadGradientV)" rx="2"/>
            <!-- 右轨 x=270 -->
            <rect x="270" :y="LAYOUT.railY[0] - 4" width="8" :height="LAYOUT.railY[5] - LAYOUT.railY[0] + 28" fill="url(#railHeadGradientV)" rx="2"/>

            <!-- 纵向钢轨3：轮轴后库右边墙体往左40像素处，从钢轨1上轨到钢轨6下轨 -->
            <!-- 左轨 x=940 -->
            <rect x="940" :y="LAYOUT.railY[0] - 4" width="8" :height="LAYOUT.railY[5] - LAYOUT.railY[0] + 28" fill="url(#railHeadGradientV)" rx="2"/>
            <!-- 右轨 x=960 -->
            <rect x="960" :y="LAYOUT.railY[0] - 4" width="8" :height="LAYOUT.railY[5] - LAYOUT.railY[0] + 28" fill="url(#railHeadGradientV)" rx="2"/>

            <!-- 纵向运输线1：第二条钢轨末端位置，中间打断间距20 -->
            <!-- 上段：从上往下流动 -->
            <rect x="1012" :y="LAYOUT.railY[0] - 4" width="15" :height="(LAYOUT.railY[5] - LAYOUT.railY[0] + 28) / 2 - 10" fill="url(#conveyorPattern)" rx="2"/>
            <!-- 下段：从下往上流动 -->
            <rect x="1012" :y="LAYOUT.railY[0] - 4 + (LAYOUT.railY[5] - LAYOUT.railY[0] + 28) / 2 + 10" width="15" :height="(LAYOUT.railY[5] - LAYOUT.railY[0] + 28) / 2 - 10" fill="url(#conveyorPatternReverse)" rx="2"/>

            <!-- 纵向运输线2：旋轮间钢轨末端，中间打断间距20，从上往下流动 -->
            <!-- 上段 -->
            <rect x="1363" :y="LAYOUT.railY[0] - 4" width="15" :height="(LAYOUT.railY[5] - LAYOUT.railY[0] + 28) / 2 - 10" fill="url(#conveyorPattern)" rx="2"/>
            <!-- 下段 -->
            <rect x="1363" :y="LAYOUT.railY[0] - 4 + (LAYOUT.railY[5] - LAYOUT.railY[0] + 28) / 2 + 10" width="15" :height="(LAYOUT.railY[5] - LAYOUT.railY[0] + 28) / 2 - 10" fill="url(#conveyorPattern)" rx="2"/>
          </g>

          <!-- 房间 -->
          <g class="rooms">
            <g v-for="room in rooms" :key="room.name">
              <rect
                :x="room.x"
                :y="room.y"
                :width="room.width"
                :height="room.height"
                :fill="room.color || 'rgba(100, 149, 237, 0.1)'"
                :stroke="room.textColor || 'rgba(100, 149, 237, 0.5)'"
                stroke-width="1"
                rx="4"
              />
              <text
                v-if="room.name"
                :x="room.x + room.width / 2"
                :y="room.labelBelow ? room.y + room.height + 15 : room.y + room.height / 2 + 4"
                text-anchor="middle"
                :fill="room.textColor || 'rgba(200, 220, 255, 0.9)'"
                font-size="14"
                font-weight="bold"
              >
                {{ room.name }}
              </text>
            </g>
          </g>

          <!-- 沙发（俯视图纵向：宽15高40，靠背在左，扶手上下，坐垫右侧纵向） -->
          <g class="sofas">
            <g v-for="(sofa, index) in sofas" :key="'sofa-' + index" :transform="`translate(${sofa.x}, ${sofa.y})`">
              <!-- 沙发外框 -->
              <rect
                x="0"
                y="0"
                :width="sofa.width"
                :height="sofa.height"
                rx="2"
                fill="none"
                stroke="rgba(255, 255, 255, 0.6)"
                stroke-width="1"
              />
              <!-- 靠背（右侧竖条） -->
              <rect
                :x="sofa.width - sofa.width * 0.25 - 1"
                y="3"
                :width="sofa.width * 0.25"
                :height="sofa.height - 6"
                rx="1"
                fill="none"
                stroke="rgba(255, 255, 255, 0.4)"
                stroke-width="0.5"
              />
              <!-- 上扶手 -->
              <line
                x1="1"
                y1="1"
                :x2="sofa.width - 1"
                y2="1"
                stroke="rgba(255, 255, 255, 0.5)"
                stroke-width="1"
                stroke-linecap="round"
              />
              <!-- 下扶手 -->
              <line
                x1="1"
                :y1="sofa.height - 1"
                :x2="sofa.width - 1"
                :y2="sofa.height - 1"
                stroke="rgba(255, 255, 255, 0.5)"
                stroke-width="1"
                stroke-linecap="round"
              />
              <!-- 四个坐垫（左侧纵向并排） -->
              <rect
                x="1"
                y="3"
                :width="sofa.width * 0.65"
                :height="sofa.height * 0.22"
                rx="1"
                fill="none"
                stroke="rgba(255, 255, 255, 0.5)"
                stroke-width="0.5"
              />
              <rect
                x="1"
                :y="sofa.height * 0.26"
                :width="sofa.width * 0.65"
                :height="sofa.height * 0.22"
                rx="1"
                fill="none"
                stroke="rgba(255, 255, 255, 0.5)"
                stroke-width="0.5"
              />
              <rect
                x="1"
                :y="sofa.height * 0.52"
                :width="sofa.width * 0.65"
                :height="sofa.height * 0.22"
                rx="1"
                fill="none"
                stroke="rgba(255, 255, 255, 0.5)"
                stroke-width="0.5"
              />
              <rect
                x="1"
                :y="sofa.height * 0.78"
                :width="sofa.width * 0.65"
                :height="sofa.height * 0.19"
                rx="1"
                fill="none"
                stroke="rgba(255, 255, 255, 0.5)"
                stroke-width="0.5"
              />
            </g>
          </g>

          <!-- 柜子（俯视图：宽30高25） -->
          <g class="cabinets">
            <g v-for="(cabinet, index) in cabinets" :key="'cabinet-' + index" :transform="`translate(${cabinet.x}, ${cabinet.y})`">
              <!-- 柜子外框 -->
              <rect
                x="0"
                y="0"
                :width="cabinet.width"
                :height="cabinet.height"
                rx="2"
                fill="none"
                stroke="rgba(255, 255, 255, 0.6)"
                stroke-width="1"
              />
              <!-- 柜门分隔线 -->
              <line
                :x1="cabinet.width / 2"
                y1="2"
                :x2="cabinet.width / 2"
                :y2="cabinet.height - 2"
                stroke="rgba(255, 255, 255, 0.4)"
                stroke-width="0.5"
              />
            </g>
          </g>

          <!-- StatsPanel嵌入SVG，定位在车间整体右下角，间距5px -->
          <foreignObject x="800" y="620" width="600" height="90">
            <body xmlns="http://www.w3.org/1999/xhtml" style="margin:0;padding:0;background:transparent;overflow:visible;">
              <div class="stats-wrapper-svg">
                <div class="stats-inner">
                  <div class="stats-corner tl"></div>
                  <div class="stats-corner tr"></div>
                  <div class="stats-corner bl"></div>
                  <div class="stats-corner br"></div>
                  <div class="stats-glow"></div>
                  <StatsPanel :statistics="deviceStore.statistics" :runningRate="deviceStore.runningRate" />
                </div>
              </div>
            </body>
          </foreignObject>

          <!-- 设备 -->
          <DeviceItem
            v-for="device in deviceStore.devices"
            :key="device.id"
            :device="device"
            @click="handleDeviceClick"
          />
        </svg>
      </div>

      <!-- 右侧图例面板 -->
      <div class="side-panel">
        <LegendPanel />
        <!-- 设备类型统计 -->
        <div class="type-stats">
          <h4>设备类型分布</h4>
          <div class="type-list">
            <div class="type-item" v-for="(config, type) in deviceTypeConfig" :key="type">
              <span class="type-icon">{{ config.icon }}</span>
              <span class="type-name">{{ config.label }}</span>
              <span class="type-count">{{ getTypeCount(type) }}台</span>
            </div>
          </div>
        </div>

        <!-- 区域设备统计 -->
        <div class="area-stats">
          <h4>区域设备统计</h4>
          <div class="area-list">
            <div class="area-item" v-for="area in ['轮轴前库', '轮轴后库', '旋轮间']" :key="area">
              <span class="area-name">{{ area }}</span>
              <span class="area-count">{{ getAreaCount(area) }}台</span>
            </div>
          </div>
        </div>

        <!-- 实时告警 -->
        <div class="alert-panel" v-if="deviceStore.statistics.fault > 0 || deviceStore.statistics.longFault > 0">
          <h4>⚠️ 实时告警</h4>
          <div class="alert-list">
            <div class="alert-item" v-for="device in faultDevices" :key="device.id">
              <span class="alert-dot" :class="device.computedStatus"></span>
              <span class="alert-name">{{ device.name }}</span>
              <span class="alert-time">{{ getFaultTime(device) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部信息栏 -->
    <footer class="screen-footer">
      <div class="footer-left">
        <span class="refresh-info">
          自动刷新间隔: 1分钟
        </span>
      </div>
      <div class="footer-center">
        <span class="alert-info" v-if="deviceStore.statistics.fault > 0 || deviceStore.statistics.longFault > 0">
          <span class="warning-icon">⚠️</span>
          当前有 {{ deviceStore.statistics.fault + deviceStore.statistics.longFault }} 台设备故障
        </span>
        <span v-else class="normal-info">✅ 所有设备运行正常</span>
      </div>
      <div class="footer-right">
        <span>设备总数: <strong>{{ deviceStore.statistics.total }}</strong></span>
        <span class="divider">|</span>
        <span>运行率: <strong class="highlight">{{ deviceStore.runningRate }}%</strong></span>
      </div>
    </footer>

    <!-- 设备详情弹窗 -->
    <DeviceDetailModal
      :visible="showDetail"
      :device="selectedDevice"
      @close="showDetail = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDeviceStore } from '../stores/deviceStore'
import { deviceTypeConfig, rails, rooms, LAYOUT, sofas, cabinets } from '../api/mockData'
import StatsPanel from '../components/StatsPanel.vue'
import LegendPanel from '../components/LegendPanel.vue'
import DeviceItem from '../components/DeviceItem.vue'
import DeviceDetailModal from '../components/DeviceDetailModal.vue'

const deviceStore = useDeviceStore()

// 时间显示
const currentTime = ref('')
const currentDate = ref('')
const updateTimeId = ref(null)

// 设备详情
const showDetail = ref(false)
const selectedDevice = ref(null)

// 格式化更新时间
const formattedUpdateTime = computed(() => {
  if (!deviceStore.lastSyncTime) return '-'
  const date = new Date(deviceStore.lastSyncTime)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
})

// 获取各类型设备数量
const getTypeCount = (type) => {
  return deviceStore.devices.filter(d => d.type === type).length
}

// 获取各区域设备数量
const getAreaCount = (area) => {
  return deviceStore.devices.filter(d => d.area === area).length
}

// 故障设备列表
const faultDevices = computed(() => {
  return deviceStore.devices.filter(d => d.computedStatus === 'fault' || d.computedStatus === 'longFault')
})

// 获取故障时间
const getFaultTime = (device) => {
  if (!device.faultTime) return ''
  const duration = Date.now() - device.faultTime
  const hours = Math.floor(duration / (1000 * 60 * 60))
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60))
  if (hours > 0) return `${hours}h${minutes}m`
  return `${minutes}min`
}

// 更新当前时间
const updateCurrentTime = () => {
  const now = new Date()
  currentDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  currentTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
}

// 点击设备
const handleDeviceClick = (device) => {
  selectedDevice.value = device
  showDetail.value = true
}

// 自动刷新定时器
let refreshTimer = null

// 刷新数据并更新设备状态
async function refreshData() {
  // 先更新设备状态
  try {
    await fetch('/workshop/api/sync/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'status' })
    })
  } catch (e) {
    console.error('更新设备状态失败:', e)
  }
  // 然后获取最新数据
  await deviceStore.fetchAllData()
}

onMounted(async () => {
  // 初始加载数据
  await refreshData()

  // 启动时间更新
  updateCurrentTime()
  updateTimeId.value = setInterval(updateCurrentTime, 1000)

  // 启动自动刷新（每1分钟）
  refreshTimer = setInterval(() => {
    if (deviceStore.autoRefresh) {
      refreshData()
    }
  }, deviceStore.refreshInterval)
})

onUnmounted(() => {
  if (updateTimeId.value) {
    clearInterval(updateTimeId.value)
  }
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.workshop-screen {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #0a0f1a 0%, #131c2e 50%, #0d1421 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif;
  position: relative;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

/* 六边形网格 */
.hex-grid {
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='52'%3E%3Cpath d='M30 0l30 15v22l-30 15L0 37V15z' fill='none' stroke='rgba(79,195,247,0.05)' stroke-width='0.5'/%3E%3C/svg%3E");
  opacity: 0.5;
  animation: hexPulse 10s ease-in-out infinite;
}

@keyframes hexPulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.grid-lines {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(79, 195, 247, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(79, 195, 247, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

/* 扫描线效果 */
.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.5), rgba(79, 195, 247, 0.9), rgba(79, 195, 247, 0.5), transparent);
  box-shadow: 0 0 30px rgba(79, 195, 247, 0.8), 0 0 60px rgba(79, 195, 247, 0.4);
  animation: scanMove 8s linear infinite;
}

@keyframes scanMove {
  0% { top: -2px; opacity: 0; }
  5% { opacity: 1; }
  95% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* 数据流动线 */
.data-flow {
  position: absolute;
  inset: 0;
}

.flow-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  top: var(--y);
  background: linear-gradient(90deg, transparent 0%, rgba(79, 195, 247, 0.3) 20%, rgba(79, 195, 247, 0.8) 50%, rgba(79, 195, 247, 0.3) 80%, transparent 100%);
  animation: flowMove 6s ease-in-out infinite;
  animation-delay: var(--delay);
}

@keyframes flowMove {
  0%, 100% { transform: translateX(-100%); opacity: 0; }
  50% { transform: translateX(100%); opacity: 1; }
}

/* 粒子效果 */
.particles {
  position: absolute;
  inset: 0;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(79, 195, 247, 0.8);
  border-radius: 50%;
  left: var(--x);
  top: var(--y);
  animation: particleFloat 12s ease-in-out infinite;
  animation-delay: var(--delay);
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.5), 0 0 20px rgba(79, 195, 247, 0.3);
}

@keyframes particleFloat {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.2; }
  25% { transform: translate(30px, -20px) scale(1.2); opacity: 0.6; }
  50% { transform: translate(10px, -40px) scale(1.5); opacity: 0.9; }
  75% { transform: translate(-20px, -20px) scale(1.2); opacity: 0.6; }
}

/* 角落装饰 */
.corner-decoration {
  position: absolute;
  width: 120px;
  height: 120px;
  border: 2px solid transparent;
  pointer-events: none;
}

.corner-decoration.top-left {
  top: 0;
  left: 0;
  border-top-color: rgba(79, 195, 247, 0.4);
  border-left-color: rgba(79, 195, 247, 0.4);
  animation: cornerPulse 3s ease-in-out infinite;
}

.corner-decoration.top-right {
  top: 0;
  right: 0;
  border-top-color: rgba(79, 195, 247, 0.4);
  border-right-color: rgba(79, 195, 247, 0.4);
  animation: cornerPulse 3s ease-in-out infinite 0.5s;
}

.corner-decoration.bottom-left {
  bottom: 0;
  left: 0;
  border-bottom-color: rgba(79, 195, 247, 0.4);
  border-left-color: rgba(79, 195, 247, 0.4);
  animation: cornerPulse 3s ease-in-out infinite 1s;
}

.corner-decoration.bottom-right {
  bottom: 0;
  right: 0;
  border-bottom-color: rgba(79, 195, 247, 0.4);
  border-right-color: rgba(79, 195, 247, 0.4);
  animation: cornerPulse 3s ease-in-out infinite 1.5s;
}

@keyframes cornerPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* 边框呼吸灯 */
.border-glow {
  position: absolute;
  inset: 0;
  border: 1px solid transparent;
  border-image: linear-gradient(135deg, rgba(79, 195, 247, 0.3), transparent 30%, transparent 70%, rgba(79, 195, 247, 0.3)) 1;
  animation: borderBreath 4s ease-in-out infinite;
}

@keyframes borderBreath {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 0%, rgba(79, 195, 247, 0.08) 0%, transparent 50%);
}

/* 顶部标题栏 */
.screen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 25px;
  background: linear-gradient(180deg, rgba(20, 30, 48, 0.95), rgba(10, 15, 26, 0.9));
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  position: relative;
  z-index: 10;
}

.screen-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.5), transparent);
}

/* 标题装饰线 */
.header-deco-line {
  position: absolute;
  bottom: 0;
  height: 3px;
  background: linear-gradient(90deg, rgba(79, 195, 247, 0.8), transparent);
  animation: decoPulse 2s ease-in-out infinite;
}

.header-deco-line.left {
  left: 0;
  width: 200px;
}

.header-deco-line.right {
  right: 0;
  width: 200px;
  background: linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.8));
}

@keyframes decoPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.header-left {
  flex: 1;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 15px;
  white-space: nowrap;
}

.logo-icon-wrapper {
  position: relative;
  width: 55px;
  height: 55px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon {
  font-size: 32px;
  filter: drop-shadow(0 0 15px rgba(79, 195, 247, 0.8));
  z-index: 2;
  position: relative;
  animation: iconGlow 2s ease-in-out infinite;
}

@keyframes iconGlow {
  0%, 100% { filter: drop-shadow(0 0 10px rgba(79, 195, 247, 0.5)); }
  50% { filter: drop-shadow(0 0 20px rgba(79, 195, 247, 0.9)); }
}

.logo-ring {
  position: absolute;
  inset: 0;
  border: 2px solid rgba(79, 195, 247, 0.4);
  border-radius: 50%;
  animation: ringRotate 10s linear infinite;
}

.logo-ring::before {
  content: '';
  position: absolute;
  top: -4px;
  left: 50%;
  width: 8px;
  height: 8px;
  background: #4fc3f7;
  border-radius: 50%;
  box-shadow: 0 0 15px #4fc3f7, 0 0 30px #4fc3f7;
}

.logo-ring.inner {
  inset: 8px;
  border-width: 1px;
  animation: ringRotate 15s linear infinite reverse;
}

.logo-ring.inner::before {
  width: 5px;
  height: 5px;
  top: -3px;
}

@keyframes ringRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-deco {
  display: flex;
  gap: 3px;
  align-items: center;
}

.title-deco span {
  display: block;
  width: 4px;
  height: 4px;
  background: #4fc3f7;
  border-radius: 50%;
  animation: dotPulse 1.5s ease-in-out infinite;
}

.title-deco span:nth-child(2) { animation-delay: 0.2s; }
.title-deco span:nth-child(3) { animation-delay: 0.4s; }

.title-deco.right span:nth-child(1) { animation-delay: 0.4s; }
.title-deco.right span:nth-child(2) { animation-delay: 0.2s; }
.title-deco.right span:nth-child(3) { animation-delay: 0s; }

@keyframes dotPulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.title {
  font-size: 50px;
  font-weight: bold;
  margin: 0;
  position: relative;
  white-space: nowrap;
}

.title-text {
  background: linear-gradient(90deg, #4fc3f7, #29b6f6, #4fc3f7);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
  animation: shimmer 3s ease-in-out infinite;
}

.title-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #4fc3f7, #29b6f6, #4fc3f7);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: blur(20px);
  opacity: 0.5;
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  align-items: center;
}

.stats-wrapper {
  position: relative;
  padding: 5px;
}

.stats-corner {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(79, 195, 247, 0.5);
  animation: cornerBlink 2s ease-in-out infinite;
}

.stats-corner.tl { top: 0; left: 0; border-right: none; border-bottom: none; }
.stats-corner.tr { top: 0; right: 0; border-left: none; border-bottom: none; animation-delay: 0.5s; }
.stats-corner.bl { bottom: 0; left: 0; border-right: none; border-top: none; animation-delay: 1s; }
.stats-corner.br { bottom: 0; right: 0; border-left: none; border-top: none; animation-delay: 1.5s; }

@keyframes cornerBlink {
  0%, 100% { border-color: rgba(79, 195, 247, 0.3); }
  50% { border-color: rgba(79, 195, 247, 0.8); }
}

.stats-glow {
  position: absolute;
  inset: -2px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(79, 195, 247, 0.1), transparent);
  animation: statsGlow 3s ease-in-out infinite;
}

@keyframes statsGlow {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

.header-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.time-wrapper {
  background: linear-gradient(135deg, rgba(79, 195, 247, 0.1), rgba(79, 195, 247, 0.05));
  border: 1px solid rgba(79, 195, 247, 0.25);
  border-radius: 10px;
  padding: 10px 18px;
  position: relative;
  overflow: hidden;
}

.time-frame {
  position: absolute;
  inset: 3px;
  border: 1px solid rgba(79, 195, 247, 0.15);
  border-radius: 7px;
  pointer-events: none;
}

.time-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.15), transparent);
  animation: timeShine 4s linear infinite;
}

@keyframes timeShine {
  0% { left: -100%; }
  100% { left: 100%; }
}

.time-label {
  font-size: 10px;
  color: rgba(79, 195, 247, 0.7);
  margin-bottom: 4px;
  letter-spacing: 3px;
  text-transform: uppercase;
}

.time-display {
  display: flex;
  gap: 12px;
  align-items: center;
}

.current-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  padding: 2px 8px;
  background: rgba(79, 195, 247, 0.1);
  border-radius: 4px;
}

.current-time {
  display: flex;
  gap: 1px;
  font-size: 24px;
  font-weight: 600;
  font-family: 'Consolas', 'Monaco', monospace;
  letter-spacing: 2px;
}

.time-segment {
  color: #4fc3f7;
  text-shadow: 0 0 15px rgba(79, 195, 247, 0.6);
  padding: 0 1px;
}

.time-segment:nth-child(3),
.time-segment:nth-child(6) {
  color: rgba(79, 195, 247, 0.5);
}

.update-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
}

.pulse-dot.active {
  animation: pulse 0.5s ease;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  padding: 15px;
  gap: 15px;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* SVG容器 */
.workshop-container {
  flex: 1;
  overflow: hidden;
  border-radius: 12px;
  background: rgba(0, 10, 20, 0.5);
  border: 1px solid rgba(79, 195, 247, 0.1);
  box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.3);
}

.workshop-svg {
  width: 100%;
  height: 100%;
}

.area-bg {
  transition: all 0.3s ease;
}

.area-bg:hover {
  stroke-width: 2;
  stroke-dasharray: none;
}

/* 右侧面板 */
.side-panel {
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.type-stats {
  background: linear-gradient(135deg, rgba(20, 30, 48, 0.95), rgba(36, 59, 85, 0.95));
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px;
}

.type-stats h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: #4fc3f7;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 8px;
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 180px;
  overflow-y: auto;
}

.type-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  transition: background 0.2s;
}

.type-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.type-icon {
  font-size: 12px;
}

.type-name {
  flex: 1;
  color: rgba(255, 255, 255, 0.8);
}

.type-count {
  color: #4fc3f7;
  font-weight: 600;
  font-size: 11px;
}

/* 区域统计 */
.area-stats {
  background: linear-gradient(135deg, rgba(20, 30, 48, 0.95), rgba(36, 59, 85, 0.95));
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px;
}

.area-stats h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: #4fc3f7;
  border-bottom: 1px solid rgba(79, 195, 247, 0.2);
  padding-bottom: 8px;
}

.area-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.area-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
}

.area-name {
  color: rgba(255, 255, 255, 0.8);
}

.area-count {
  color: #22c55e;
  font-weight: 600;
}

/* 告警面板 */
.alert-panel {
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.2), rgba(192, 57, 43, 0.2));
  border-radius: 10px;
  border: 1px solid rgba(231, 76, 60, 0.3);
  padding: 12px;
}

.alert-panel h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: #e74c3c;
  display: flex;
  align-items: center;
  gap: 6px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: blink 1s ease-in-out infinite;
}

.alert-dot.fault {
  background: #eab308;
}

.alert-dot.longFault {
  background: #e74c3c;
}

.alert-name {
  flex: 1;
  color: rgba(255, 255, 255, 0.9);
}

.alert-time {
  color: #e74c3c;
  font-size: 10px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 底部信息栏 */
.screen-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 25px;
  background: rgba(10, 15, 26, 0.9);
  border-top: 1px solid rgba(79, 195, 247, 0.2);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  position: relative;
  z-index: 10;
}

.footer-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.alert-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #eab308;
  font-weight: 500;
  padding: 4px 12px;
  background: rgba(234, 179, 8, 0.1);
  border-radius: 20px;
}

.warning-icon {
  animation: blink 1s ease-in-out infinite;
}

.normal-info {
  color: #22c55e;
  padding: 4px 12px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 20px;
}

.footer-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.divider {
  color: rgba(255, 255, 255, 0.3);
}

.highlight {
  color: #22c55e;
  font-size: 14px;
}

/* SVG内嵌StatsPanel样式 */
.stats-wrapper-svg {
  display: flex;
  justify-content: flex-end;
}

.stats-inner {
  position: relative;
  padding: 5px;
}

.stats-inner .stats-corner {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(79, 195, 247, 0.5);
  animation: cornerBlink 2s ease-in-out infinite;
}

.stats-inner .stats-corner.tl { top: 0; left: 0; border-right: none; border-bottom: none; }
.stats-inner .stats-corner.tr { top: 0; right: 0; border-left: none; border-bottom: none; animation-delay: 0.5s; }
.stats-inner .stats-corner.bl { bottom: 0; left: 0; border-right: none; border-top: none; animation-delay: 1s; }
.stats-inner .stats-corner.br { bottom: 0; right: 0; border-left: none; border-top: none; animation-delay: 1.5s; }

.stats-inner .stats-glow {
  position: absolute;
  inset: -2px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(79, 195, 247, 0.1), transparent);
  animation: statsGlow 3s ease-in-out infinite;
}
</style>
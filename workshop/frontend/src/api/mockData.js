// 车间设备数据 - 基于实际车间布局（2026-03-17更新）

// 设备类型配置
export const deviceTypeConfig = {
  grind: { label: '磨合设备', icon: '⚙️' },
  detect: { label: '检测设备', icon: '📏' },
  unload: { label: '退卸设备', icon: '🔄' },
  rust: { label: '除锈设备', icon: '🧹' },
  flaw: { label: '探伤设备', icon: '🔍' },
  oil: { label: '涂油设备', icon: '🛢️' },
  bolt: { label: '紧固设备', icon: '🔩' },
  press: { label: '压装设备', icon: '🔨' },
  measure: { label: '测量设备', icon: '📐' },
  crane: { label: '天车设备', icon: '🏗️' },
  lathe: { label: '车轮车床', icon: '🔧' },
  protect: { label: '防护装置', icon: '🛡️' },
  forklift: { label: '货叉装置', icon: '📦' },
  stacker: { label: '堆垛系统', icon: '🏭' },
  warehouse: { label: '立体库', icon: '🏛️' },
  turntable: { label: '转盘设备', icon: '🔄' },
}

// 状态配置
export const statusConfig = {
  running: {
    label: '运行中',
    color: '#2ecc71',
    lightColor: '#27ae60',
    description: '设备正常运行'
  },
  fault: {
    label: '故障',
    color: '#f1c40f',
    lightColor: '#f39c12',
    description: '设备出现故障'
  },
  longFault: {
    label: '长时间故障',
    color: '#e74c3c',
    lightColor: '#c0392b',
    description: '故障超过2小时未修复'
  },
  offline: {
    label: '离线',
    color: '#95a5a6',
    lightColor: '#7f8c8d',
    description: '设备离线或停机'
  }
}

// SVG布局参数
export const LAYOUT = {
  svgWidth: 1400,
  svgHeight: 700,
  // 区域宽度比例：左边3/7，中间2/7，右边2/7
  leftWidth: 600,      // 轮轴间宽度
  middleWidth: 400,    // 探伤间宽度
  rightWidth: 400,     // 旋轮间宽度
  // 钢轨Y坐标
  railY: [80, 150, 220, 320, 390, 460],
  // 设备尺寸
  deviceWidth: 100,
  deviceHeight: 45,
  smallDeviceWidth: 70,
  smallDeviceHeight: 35,
}

// 区域边界配置（钢轨贯穿全屏）
export const areas = [
  {
    name: '轮轴间',
    x: 10, y: 40,
    width: LAYOUT.leftWidth - 20,
    height: 540,
    color: 'rgba(52, 152, 219, 0.06)',
    borderColor: 'rgba(52, 152, 219, 0.5)'
  },
  {
    name: '探伤间',
    x: LAYOUT.leftWidth + 10, y: 40,
    width: LAYOUT.middleWidth - 20,
    height: 540,
    color: 'rgba(46, 204, 113, 0.06)',
    borderColor: 'rgba(46, 204, 113, 0.5)'
  },
  {
    name: '旋轮间',
    x: LAYOUT.leftWidth + LAYOUT.middleWidth + 10, y: 40,
    width: LAYOUT.rightWidth - 20,
    height: 540,
    color: 'rgba(155, 89, 182, 0.06)',
    borderColor: 'rgba(155, 89, 182, 0.5)'
  },
]

// 房间配置
export const rooms = [
  { name: '轴承端盖及配件清洗间', x: 50, y: 520, width: 160, height: 50, color: 'rgba(46, 204, 113, 0.15)', textColor: '#2ecc71' },
  { name: '探伤间休室', x: 220, y: 520, width: 170, height: 50, color: 'rgba(46, 204, 113, 0.15)', textColor: '#2ecc71' },
  { name: '轮轴间休室', x: 400, y: 520, width: 200, height: 50, color: 'rgba(46, 204, 113, 0.15)', textColor: '#2ecc71' },
  { name: '配件存放间', x: 0, y: 620, width: 250, height: 60, color: 'rgba(52, 152, 219, 0.15)', textColor: '#4fc3f7' },
  { name: '工具间', x: 250, y: 620, width: 120, height: 50, color: 'rgba(52, 152, 219, 0.15)', textColor: '#4fc3f7' },
]

// 钢轨配置 - 6条钢轨贯穿全屏
export const rails = [
  { id: 'rail-1', y: LAYOUT.railY[0], name: '1号钢轨' },
  { id: 'rail-2', y: LAYOUT.railY[1], name: '2号钢轨' },
  { id: 'rail-3', y: LAYOUT.railY[2], name: '3号钢轨' },
  { id: 'rail-4', y: LAYOUT.railY[3], name: '4号钢轨' },
  { id: 'rail-5', y: LAYOUT.railY[4], name: '5号钢轨' },
  { id: 'rail-6', y: LAYOUT.railY[5], name: '6号钢轨' },
]

// 生成设备的辅助函数
function createDevice(id, name, area, type, x, y, width = LAYOUT.deviceWidth, height = LAYOUT.deviceHeight, status = 'running', extra = {}) {
  return {
    id,
    name,
    area,
    type,
    x,
    y,
    width,
    height,
    status,
    ...extra
  }
}

// 生成设备数据
export const mockDevices = []

let deviceId = 1

// ==================== 轮轴间设备 ====================
// 钢轨1-3：轮对自动检测机(宽度缩短40，右移40)、轴承退卸机、轮对除锈机（后两列位置不变）
const lunZhouDevices123 = [
  { name: '轮对自动检测机', type: 'detect', x_offset: 120, width: 60 },  // 右移40，宽度60
  { name: '轴承退卸机', type: 'unload', x_offset: 280 },     // 不变
  { name: '轮对除锈机', type: 'rust', x_offset: 420 },       // 不变
]

// 钢轨4-5：轮对自动涂油机(缩小)、双轮磨合机(前移60)、双轮磨合机(右移60)、轴端螺栓紧固机(不变)
const lunZhouDevices45 = [
  { name: '轮对自动涂油机', type: 'oil', x_offset: 0, width: 60 },  // 缩小2/5
  { name: '双轮磨合机', type: 'grind', x_offset: 80 },  // 前移60
  { name: '双轮磨合机', type: 'grind', x_offset: 280 }, // 右移60
  { name: '轴端螺栓紧固机', type: 'bolt', x_offset: 420 }, // 不变
]

// 钢轨6：轮对自动涂油机(缩小)、轮对自动检测机(前移60)、双轮磨合机(右移60)、轴端螺栓紧固机(不变)
const lunZhouDevices6 = [
  { name: '轮对自动涂油机', type: 'oil', x_offset: 0, width: 60 },  // 缩小2/5
  { name: '轮对自动检测机', type: 'detect', x_offset: 80 },  // 前移60
  { name: '双轮磨合机', type: 'grind', x_offset: 280 }, // 右移60
  { name: '轴端螺栓紧固机', type: 'bolt', x_offset: 420 }, // 不变
]

// 钢轨1-3设备
for (let railIdx = 0; railIdx < 3; railIdx++) {
  lunZhouDevices123.forEach((device, deviceIdx) => {
    const x = 30 + device.x_offset
    const y = LAYOUT.railY[railIdx] + 10 - LAYOUT.deviceHeight / 2
    const width = device.width || LAYOUT.deviceWidth
    mockDevices.push(createDevice(
      `D${String(deviceId++).padStart(3, '0')}`,
      `${device.name}-${railIdx + 1}-${deviceIdx + 1}`,
      '轮轴间',
      device.type,
      x, y,
      width, LAYOUT.deviceHeight
    ))
  })
}

// 轴承自动开盖机（第一、二条钢轨，转盘与检测机中间）
for (let i = 0; i < 2; i++) {
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `轴承自动开盖机-${i + 1}`,
    '轮轴间',
    'detect',
    87, LAYOUT.railY[i] + 10 - LAYOUT.deviceHeight / 2,
    40, LAYOUT.deviceHeight
  ))
}

// 配件存放间设备
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '轴承附件清洗机',
  '配件存放间',
  'detect',
  5, 625,
  75, 22
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '附件超声波清洗机',
  '配件存放间',
  'detect',
  90, 625,
  75, 22
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '悬臂吊',
  '配件存放间',
  'crane',
  175, 625,
  70, 22
))

// 标志牌打印机（轴承端盖及配件清洗间内右边）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '标志牌打印机',
  '轴承端盖及配件清洗间',
  'detect',
  145, 527,
  60, 40
))

// 钢轨4-5设备
for (let railIdx = 3; railIdx < 5; railIdx++) {
  lunZhouDevices45.forEach((device, deviceIdx) => {
    // 跳过双轮磨合机-5-3（钢轨5的第3个设备）
    if (railIdx === 4 && deviceIdx === 2) return
    const x = 30 + device.x_offset
    const y = LAYOUT.railY[railIdx] + 10 - LAYOUT.deviceHeight / 2
    const width = device.width || LAYOUT.deviceWidth
    mockDevices.push(createDevice(
      `D${String(deviceId++).padStart(3, '0')}`,
      `${device.name}-${railIdx + 1}-${deviceIdx + 1}`,
      '轮轴间',
      device.type,
      x, y,
      width, LAYOUT.deviceHeight
    ))
  })
}

// 钢轨6设备
lunZhouDevices6.forEach((device, deviceIdx) => {
  // 跳过双轮磨合机-6-3（第3个设备）
  if (deviceIdx === 2) return
  const x = 30 + device.x_offset
  const y = LAYOUT.railY[5] + 10 - LAYOUT.deviceHeight / 2
  const width = device.width || LAYOUT.deviceWidth
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `${device.name}-6-${deviceIdx + 1}`,
    '轮轴间',
    device.type,
    x, y,
    width, LAYOUT.deviceHeight
  ))
})

// 转盘设备
// 第一组：纵向钢轨1与钢轨1、2、3的交叉点处（x=24，对应转盘-1到转盘-3）
// 纵向钢轨1中心在x=44，转盘直径40，x=44-20=24
for (let i = 0; i < 3; i++) {
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `转盘-${i + 1}`,
    '轮轴间',
    'turntable',
    24, LAYOUT.railY[i] - 10,  // 圆心在rail.y+10，减去半径20得到y坐标
    40, 40
  ))
}

// 第二组：纵向钢轨2与钢轨1-6的交叉点处（x=245，对应转盘-4到转盘-9）
// 纵向钢轨2中心在x=260，转盘直径40，x=260-20+5=245
for (let i = 0; i < 6; i++) {
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `转盘-${i + 4}`,
    '轮轴间',
    'turntable',
    245, LAYOUT.railY[i] - 10,
    40, 40
  ))
}

// 第三组：纵向钢轨3与钢轨1-6的交叉点处（x=935，对应转盘-10到转盘-15）
// 纵向钢轨3中心在x=950，转盘直径40，x=950-20+5=935
for (let i = 0; i < 6; i++) {
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `转盘-${i + 10}`,
    '探伤间',
    'turntable',
    935, LAYOUT.railY[i] - 10,
    40, 40
  ))
}

// 轴承堆垛系统（工具间内）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '轴承堆垛系统',
  '工具间',
  'stacker',
  280, 623,
  60, 45,
  'running',
  { capacity: 500, used: 328 }
))

// ==================== 探伤间设备 ====================
// 钢轨1-3：轮对磁粉探伤机、轮对超声波探伤机（人工复探是占位，不算设备）
const tanShangDevices123 = [
  { name: '轮对磁粉探伤机', type: 'flaw' },
  { name: '轮对超声波探伤机', type: 'flaw' },
]

// 钢轨1-3设备（探伤间部分）
// 轮对超声波探伤机往左移动20
// 轮对超声波探伤机-1改名为相控阵探伤机
for (let railIdx = 0; railIdx < 3; railIdx++) {
  tanShangDevices123.forEach((device, deviceIdx) => {
    // 第二列设备（轮对超声波探伤机）往左移动20
    const xOffset = deviceIdx === 1 ? 130 : 150
    const x = LAYOUT.leftWidth + 30 + deviceIdx * xOffset
    const y = LAYOUT.railY[railIdx] + 10 - LAYOUT.deviceHeight / 2  // 钢轨中心偏移
    // 轮对超声波探伤机-1改名为相控阵探伤机
    const deviceName = (railIdx === 0 && deviceIdx === 1) ? '相控阵探伤机' : `${device.name}-${railIdx + 1}`
    mockDevices.push(createDevice(
      `D${String(deviceId++).padStart(3, '0')}`,
      deviceName,
      '探伤间',
      device.type,
      x, y
    ))
  })
}

// 转轮器（探伤间，钢轨1-3）
for (let i = 0; i < 3; i++) {
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `转轮器-${i + 1}`,
    '探伤间',
    'detect',
    LAYOUT.leftWidth + 280, LAYOUT.railY[i] + 10 - 18,
    35, 36
  ))
}

// 钢轨5：轴承压装机、轴颈自动测量机（中间标注轮对压装线2）
const tanShangDevices5 = [
  { name: '轴承压装机', type: 'press' },
  { name: '轴颈自动测量机', type: 'measure' },
]

// 轴承压装机位置
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  `轴承压装机-压装线2`,
  '探伤间',
  'press',
  LAYOUT.leftWidth + 30, LAYOUT.railY[4] + 10 - LAYOUT.deviceHeight / 2,
  LAYOUT.deviceWidth, LAYOUT.deviceHeight
))

// 轴颈自动测量机（压装线2）- 与轴承压装机间隔60
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  `轴颈自动测量机-压装线2`,
  '探伤间',
  'measure',
  LAYOUT.leftWidth + 190, LAYOUT.railY[4] + 10 - LAYOUT.deviceHeight / 2,
  LAYOUT.deviceWidth, LAYOUT.deviceHeight
))

// 钢轨6：轴承压装机、轴颈自动测量机（压装线1）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  `轴承压装机-压装线1`,
  '探伤间',
  'press',
  LAYOUT.leftWidth + 30, LAYOUT.railY[5] + 10 - LAYOUT.deviceHeight / 2,
  LAYOUT.deviceWidth, LAYOUT.deviceHeight
))

// 轴颈自动测量机（压装线1）- 与轴承压装机间隔60
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  `轴颈自动测量机-压装线1`,
  '探伤间',
  'measure',
  LAYOUT.leftWidth + 190, LAYOUT.railY[5] + 10 - LAYOUT.deviceHeight / 2,
  LAYOUT.deviceWidth, LAYOUT.deviceHeight
))

// 轮对识别机（探伤间右边墙体往左5像素处，钢轨1-3）
for (let i = 0; i < 3; i++) {
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `轮对识别机-${i + 1}`,
    '探伤间',
    'detect',
    LAYOUT.leftWidth + LAYOUT.middleWidth - 20, LAYOUT.railY[i] + 10 - LAYOUT.deviceHeight / 2,
    15, LAYOUT.deviceHeight
  ))
}

// 轴承智能选配立体库（钢轨6下方，Y与轮轴间房间平齐）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '轴承智能选配立体库',
  '探伤间',
  'warehouse',
  LAYOUT.leftWidth + 30, 520,
  190, 45,
  'running',
  { capacity: 1000, used: 756 }
))

// 轴承内径测量机（立体库与机器人中间，拆分为2台）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '轴承内径测量机-1',
  '探伤间',
  'measure',
  LAYOUT.leftWidth + 230, 520,
  40, 20
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '轴承内径测量机-2',
  '探伤间',
  'measure',
  LAYOUT.leftWidth + 230, 545,
  40, 20
))

// 轴承上料机器人（在测量机右边）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '轴承上料机器人',
  '探伤间',
  'detect',
  LAYOUT.leftWidth + 280, 520,
  80, 45
))

// 标志牌识别机（3号钢轨起始位置处，轮轴间左边墙体外）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '标志牌识别机',
  '墙外',
  'detect',
  -75, LAYOUT.railY[2] + 10 - LAYOUT.deviceHeight / 2,
  50, 45
))

// ==================== 旋轮间设备 ====================
// 航架机械手（第六条钢轨下方，靠近旋轮间左边墙体，纵向排列，间隔10）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '航架机械手-1',
  '旋轮间',
  'crane',
  LAYOUT.leftWidth + LAYOUT.middleWidth + 110, LAYOUT.railY[5] + 30,
  80, 25
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '航架机械手-2',
  '旋轮间',
  'crane',
  LAYOUT.leftWidth + LAYOUT.middleWidth + 110, LAYOUT.railY[5] + 60,
  80, 25
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '航架天车',
  '旋轮间',
  'crane',
  LAYOUT.leftWidth + LAYOUT.middleWidth + 110, LAYOUT.railY[5] + 90,
  80, 25
))
// 航架设备（虚线右边，间隔10）
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '航架机械手-3',
  '旋轮间',
  'crane',
  LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 + 10, LAYOUT.railY[5] + 30,
  80, 25
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '航架机械手-4',
  '旋轮间',
  'crane',
  LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 + 10, LAYOUT.railY[5] + 60,
  80, 25
))
mockDevices.push(createDevice(
  `D${String(deviceId++).padStart(3, '0')}`,
  '天车',
  '旋轮间',
  'crane',
  LAYOUT.leftWidth + LAYOUT.middleWidth + LAYOUT.rightWidth / 2 + 10, LAYOUT.railY[5] + 90,
  80, 25
))

// 6个车轮车床，布局改为3行2列
// 编号映射：原位置 0,1,2,3,4,5 -> 新编号 01,06,02,05,03,04
const latheNumberMap = [1, 6, 2, 5, 3, 4]

for (let i = 0; i < 6; i++) {
  // 计算行列位置：3行2列
  const row = Math.floor(i / 2)  // 行号 0, 0, 1, 1, 2, 2
  const col = i % 2              // 列号 0, 1, 0, 1, 0, 1

  // 车床尺寸和间距
  const latheWidth = 180
  const latheHeight = 100
  const colGap = 20              // 两列间距
  const rowGap = 30              // 两行间距
  // 居中计算：旋轮间宽度400，两列车床+间距 = 180*2 + 20 = 380，居中偏移 = (400-380)/2 = 10
  const startX = LAYOUT.leftWidth + LAYOUT.middleWidth + 10
  const startY = 100

  // 行偏移：第一行往下10，第三行往上10
  const rowOffset = row === 0 ? 10 : (row === 2 ? -10 : 0)

  // 计算坐标
  const latheX = startX + col * (latheWidth + colGap)
  const latheY = startY + row * (latheHeight + rowGap) + rowOffset

  // 车轮车床主体
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `车轮车床-${String(latheNumberMap[i]).padStart(2, '0')}`,
    '旋轮间',
    'lathe',
    latheX, latheY,
    latheWidth, latheHeight
  ))

  // 防护套自动装卸装置（集成在车床左边1/5处）
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `防护套装卸装置-${String(latheNumberMap[i]).padStart(2, '0')}`,
    '旋轮间',
    'protect',
    latheX + 5, latheY + 8,
    latheWidth / 5 - 8, 38
  ))

  // 升降货叉式上下料装置（集成在车床左边1/5处）
  mockDevices.push(createDevice(
    `D${String(deviceId++).padStart(3, '0')}`,
    `升降货叉装置-${String(latheNumberMap[i]).padStart(2, '0')}`,
    '旋轮间',
    'forklift',
    latheX + 5, latheY + 52,
    latheWidth / 5 - 8, 38
  ))
}

// 故障阈值时间（毫秒）
export const LONG_FAULT_THRESHOLD = 2 * 60 * 60 * 1000 // 2小时
from django.core.management.base import BaseCommand
from django.utils import timezone
from workshop.models import Device, DeviceArea, DeviceType


class Command(BaseCommand):
    help = '初始化车间设备数据（2026-03-24更新）'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化数据...')

        # 获取已有的设备类型和区域（不删除，从数据库获取）
        device_type_map = {dt.code: dt for dt in DeviceType.objects.all()}
        area_map = {da.name: da for da in DeviceArea.objects.all()}

        # 清空现有设备数据
        Device.objects.all().delete()

        # 布局参数
        LEFT_WIDTH = 600      # 轮轴间宽度
        MIDDLE_WIDTH = 400    # 探伤间宽度
        RIGHT_WIDTH = 400     # 旋轮间宽度
        RAIL_Y = [80, 150, 220, 320, 390, 460]  # 6条钢轨Y坐标

        # 设备基础尺寸
        DW, DH = 100, 45
        SMALL_W, SMALL_H = 55, 20

        # 创建设备列表
        devices_data = []
        device_id = 1

        # ==================== 轮轴间设备 ====================
        # 钢轨1-3：轮对自动检测机(宽度缩短40，右移40)、轴承退卸机、轮对除锈机（后两列位置不变）
        lun_zhou_devices_123 = [
            {'name': '轮对自动检测机', 'type': 'detect', 'x_offset': 120, 'width': 60},  # 右移40，宽度60
            {'name': '轴承退卸机', 'type': 'unload', 'x_offset': 280},     # 不变
            {'name': '轮对除锈机', 'type': 'rust', 'x_offset': 420},       # 不变
        ]

        # 钢轨4-5：轮对自动涂油机(缩小)、双轮磨合机(前移60)、双轮磨合机(右移60)、轴端螺栓紧固机(不变)
        lun_zhou_devices_45 = [
            {'name': '轮对自动涂油机', 'type': 'oil', 'x_offset': 0, 'width': 60},  # 缩小2/5
            {'name': '双轮磨合机', 'type': 'grind', 'x_offset': 80},  # 前移60
            {'name': '双轮磨合机', 'type': 'grind', 'x_offset': 280}, # 右移60
            {'name': '轴端螺栓紧固机', 'type': 'bolt', 'x_offset': 420}, # 不变
        ]

        # 钢轨6：轮对自动涂油机(缩小)、轮对自动检测机(前移60)、双轮磨合机(右移60)、轴端螺栓紧固机(不变)
        lun_zhou_devices_6 = [
            {'name': '轮对自动涂油机', 'type': 'oil', 'x_offset': 0, 'width': 60},  # 缩小2/5
            {'name': '轮对自动检测机', 'type': 'detect', 'x_offset': 80},  # 前移60
            {'name': '双轮磨合机', 'type': 'grind', 'x_offset': 280}, # 右移60
            {'name': '轴端螺栓紧固机', 'type': 'bolt', 'x_offset': 420}, # 不变
        ]

        # 钢轨1-3设备
        for rail_idx in range(3):
            for dev_idx, device in enumerate(lun_zhou_devices_123):
                x = 30 + device['x_offset']
                y = RAIL_Y[rail_idx] + 10 - DH // 2
                width = device.get('width', DW)
                devices_data.append({
                    'device_id': f'D{str(device_id).zfill(3)}',
                    'name': f"{device['name']}-{rail_idx + 1}-{dev_idx + 1}",
                    'area': '轮轴间',
                    'device_type': device['type'],
                    'status': 'running',
                    'pos_x': x,
                    'pos_y': y,
                    'pos_width': width,
                    'pos_height': DH,
                })
                device_id += 1

        # 轴承自动开盖机（第一、二条钢轨，转盘与检测机中间）
        for i in range(2):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'轴承自动开盖机-{i + 1}',
                'area': '轮轴间',
                'device_type': 'detect',
                'status': 'running',
                'pos_x': 87,
                'pos_y': RAIL_Y[i] + 10 - DH // 2,
                'pos_width': 40,
                'pos_height': DH,
            })
            device_id += 1

        # 配件存放间设备（归属轮轴间）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承附件清洗机',
            'area': '轮轴间',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': 5,
            'pos_y': 625,
            'pos_width': 75,
            'pos_height': 22,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '附件超声波清洗机',
            'area': '轮轴间',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': 90,
            'pos_y': 625,
            'pos_width': 75,
            'pos_height': 22,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '悬臂吊',
            'area': '轮轴间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': 175,
            'pos_y': 625,
            'pos_width': 70,
            'pos_height': 22,
        })
        device_id += 1

        # 钢轨4-5设备
        for rail_idx in range(3, 5):
            for dev_idx, device in enumerate(lun_zhou_devices_45):
                # 跳过双轮磨合机-5-3（钢轨5的第3个设备）
                if rail_idx == 4 and dev_idx == 2:
                    continue
                x = 30 + device['x_offset']
                y = RAIL_Y[rail_idx] + 10 - DH // 2
                width = device.get('width', DW)
                devices_data.append({
                    'device_id': f'D{str(device_id).zfill(3)}',
                    'name': f"{device['name']}-{rail_idx + 1}-{dev_idx + 1}",
                    'area': '轮轴间',
                    'device_type': device['type'],
                    'status': 'running',
                    'pos_x': x,
                    'pos_y': y,
                    'pos_width': width,
                    'pos_height': DH,
                })
                device_id += 1

        # 钢轨6设备
        for dev_idx, device in enumerate(lun_zhou_devices_6):
            # 跳过双轮磨合机-6-3（第3个设备）
            if dev_idx == 2:
                continue
            x = 30 + device['x_offset']
            y = RAIL_Y[5] + 10 - DH // 2
            width = device.get('width', DW)
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"{device['name']}-6-{dev_idx + 1}",
                'area': '轮轴间',
                'device_type': device['type'],
                'status': 'running',
                'pos_x': x,
                'pos_y': y,
                'pos_width': width,
                'pos_height': DH,
            })
            device_id += 1

        # 标志牌打印机（轴承端盖及配件清洗间内右边，归属轮轴间）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '标志牌打印机',
            'area': '轮轴间',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': 145,
            'pos_y': 527,
            'pos_width': 60,
            'pos_height': 40,
        })
        device_id += 1

        # 轴承堆垛系统（工具间内，归属轮轴间）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承堆垛系统',
            'area': '轮轴间',
            'device_type': 'stacker',
            'status': 'running',
            'pos_x': 280,
            'pos_y': 623,
            'pos_width': 60,
            'pos_height': 45,
        })
        device_id += 1

        # 转盘设备
        # 第一组：纵向钢轨1与钢轨1、2、3的交叉点处（x=24，对应转盘-1到转盘-3）
        # 纵向钢轨1中心在x=44，转盘直径40，x=44-20=24
        for i in range(3):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'转盘-{i + 1}',
                'area': '轮轴间',
                'device_type': 'turntable',
                'status': 'running',
                'pos_x': 24,
                'pos_y': RAIL_Y[i] - 10,  # 圆心在rail_y+10，减去半径20得到y坐标
                'pos_width': 40,
                'pos_height': 40,
            })
            device_id += 1

        # 第二组：纵向钢轨2与钢轨1-6的交叉点处（x=245，对应转盘-4到转盘-9）
        # 纵向钢轨2中心在x=260，转盘直径40，x=260-20+5=245
        for i in range(6):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'转盘-{i + 4}',
                'area': '轮轴间',
                'device_type': 'turntable',
                'status': 'running',
                'pos_x': 245,
                'pos_y': RAIL_Y[i] - 10,
                'pos_width': 40,
                'pos_height': 40,
            })
            device_id += 1

        # 第三组：纵向钢轨3与钢轨1-6的交叉点处（x=935，对应转盘-10到转盘-15）
        # 纵向钢轨3中心在x=950，转盘直径40，x=950-20+5=935
        for i in range(6):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'转盘-{i + 10}',
                'area': '探伤间',
                'device_type': 'turntable',
                'status': 'running',
                'pos_x': 935,
                'pos_y': RAIL_Y[i] - 10,
                'pos_width': 40,
                'pos_height': 40,
            })
            device_id += 1

        # ==================== 探伤间设备 ====================
        # 钢轨1-3：轮对磁粉探伤机、轮对超声波探伤机
        tan_shang_devices_123 = [
            {'name': '轮对磁粉探伤机', 'type': 'flaw'},
            {'name': '轮对超声波探伤机', 'type': 'flaw'},
        ]

        # 钢轨1-3设备（探伤间部分）
        # 轮对超声波探伤机往左移动20
        # 轮对超声波探伤机-1改名为相控阵探伤机
        for rail_idx in range(3):
            for dev_idx, device in enumerate(tan_shang_devices_123):
                # 第二列设备（轮对超声波探伤机）往左移动20
                x_offset = 130 if dev_idx == 1 else 150
                x = LEFT_WIDTH + 30 + dev_idx * x_offset
                y = RAIL_Y[rail_idx] + 10 - DH // 2
                # 轮对超声波探伤机-1改名为相控阵探伤机
                device_name = '相控阵探伤机' if (rail_idx == 0 and dev_idx == 1) else f"{device['name']}-{rail_idx + 1}"
                devices_data.append({
                    'device_id': f'D{str(device_id).zfill(3)}',
                    'name': device_name,
                    'area': '探伤间',
                    'device_type': device['type'],
                    'status': 'running',
                    'pos_x': x,
                    'pos_y': y,
                    'pos_width': DW,
                    'pos_height': DH,
                })
                device_id += 1

        # 转轮器（探伤间，钢轨1-3）
        for i in range(3):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'转轮器-{i + 1}',
                'area': '探伤间',
                'device_type': 'detect',
                'status': 'running',
                'pos_x': LEFT_WIDTH + 280,
                'pos_y': RAIL_Y[i] + 10 - 18,
                'pos_width': 35,
                'pos_height': 36,
            })
            device_id += 1

        # 钢轨5：轴承压装机、轴颈自动测量机（轮对压装线2）
        # 轴承压装机
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': f"轴承压装机-压装线2",
            'area': '探伤间',
            'device_type': 'press',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 30,
            'pos_y': RAIL_Y[4] + 10 - DH // 2,
            'pos_width': DW,
            'pos_height': DH,
        })
        device_id += 1

        # 轴颈自动测量机（压装线2）- 与轴承压装机间隔60
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': f"轴颈自动测量机-压装线2",
            'area': '探伤间',
            'device_type': 'measure',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 190,
            'pos_y': RAIL_Y[4] + 10 - DH // 2,
            'pos_width': DW,
            'pos_height': DH,
        })
        device_id += 1

        # 钢轨6：轴承压装机、轴颈自动测量机（轮对压装线1）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': f"轴承压装机-压装线1",
            'area': '探伤间',
            'device_type': 'press',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 30,
            'pos_y': RAIL_Y[5] + 10 - DH // 2,
            'pos_width': DW,
            'pos_height': DH,
        })
        device_id += 1

        # 轴颈自动测量机（压装线1）- 与轴承压装机间隔60
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': f"轴颈自动测量机-压装线1",
            'area': '探伤间',
            'device_type': 'measure',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 190,
            'pos_y': RAIL_Y[5] + 10 - DH // 2,
            'pos_width': DW,
            'pos_height': DH,
        })
        device_id += 1

        # 轮对识别机（探伤间右边墙体往左5像素处，钢轨1-3）
        for i in range(3):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'轮对识别机-{i + 1}',
                'area': '探伤间',
                'device_type': 'detect',
                'status': 'running',
                'pos_x': LEFT_WIDTH + MIDDLE_WIDTH - 20,
                'pos_y': RAIL_Y[i] + 10 - DH // 2,
                'pos_width': 15,
                'pos_height': DH,
            })
            device_id += 1

        # 轴承智能选配立体库（Y与轮轴间房间平齐）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承智能选配立体库',
            'area': '探伤间',
            'device_type': 'warehouse',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 30,
            'pos_y': 520,
            'pos_width': 190,
            'pos_height': 45,
        })
        device_id += 1

        # 轴承内径测量机（立体库与机器人中间，拆分为2台）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承内径测量机-1',
            'area': '探伤间',
            'device_type': 'measure',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 230,
            'pos_y': 520,
            'pos_width': 40,
            'pos_height': 20,
        })
        device_id += 1
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承内径测量机-2',
            'area': '探伤间',
            'device_type': 'measure',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 230,
            'pos_y': 545,
            'pos_width': 40,
            'pos_height': 20,
        })
        device_id += 1

        # 轴承上料机器人（在测量机右边）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承上料机器人',
            'area': '探伤间',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 280,
            'pos_y': 520,
            'pos_width': 80,
            'pos_height': 45,
        })
        device_id += 1

        # 标志牌识别机（3号钢轨起始位置处，轮轴间左边墙体外，归属轮轴间）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '标志牌识别机',
            'area': '轮轴间',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': -75,
            'pos_y': RAIL_Y[2] + 10 - DH // 2,
            'pos_width': 50,
            'pos_height': 45,
        })
        device_id += 1

        # 天车（轮轴间，与标志牌识别机同y坐标，与轴承自动开盖机-1同x坐标）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '天车',
            'area': '轮轴间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': -75,
            'pos_y': 68,
            'pos_width': 60,
            'pos_height': 25,
        })
        device_id += 1

        # ==================== 旋轮间设备 ====================
        # 航架机械手（第六条钢轨下方，靠近旋轮间左边墙体，纵向排列，间隔10）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '航架机械手-1',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + 110,
            'pos_y': RAIL_Y[5] + 30,
            'pos_width': 80,
            'pos_height': 25,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '航架机械手-2',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + 110,
            'pos_y': RAIL_Y[5] + 60,
            'pos_width': 80,
            'pos_height': 25,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '航架天车',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + 110,
            'pos_y': RAIL_Y[5] + 90,
            'pos_width': 80,
            'pos_height': 25,
        })
        device_id += 1

        # 航架设备（虚线右边，间隔10）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '航架机械手-3',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + RIGHT_WIDTH // 2 + 10,
            'pos_y': RAIL_Y[5] + 30,
            'pos_width': 80,
            'pos_height': 25,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '航架机械手-4',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + RIGHT_WIDTH // 2 + 10,
            'pos_y': RAIL_Y[5] + 60,
            'pos_width': 80,
            'pos_height': 25,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '天车',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + RIGHT_WIDTH // 2 + 10,
            'pos_y': RAIL_Y[5] + 90,
            'pos_width': 80,
            'pos_height': 25,
        })
        device_id += 1

        # 6个车轮车床，布局改为3行2列
        # 编号映射：原位置 0,1,2,3,4,5 -> 新编号 01,06,02,05,03,04
        lathe_width = 90
        lathe_height = 100
        col_gap = 20               # 两列间距
        row_gap = 30               # 两行间距
        start_x = LEFT_WIDTH + MIDDLE_WIDTH + 100
        start_y = 100

        # 第一组：01、02、03（左列）
        group1_numbers = [1, 2, 3]  # 编号01, 02, 03
        group1_positions = [
            {'row': 0, 'row_offset': 10},   # 01: 第一行，偏移+10
            {'row': 1, 'row_offset': 0},    # 02: 第二行，无偏移
            {'row': 2, 'row_offset': -10},  # 03: 第三行，偏移-10
        ]

        for idx, num in enumerate(group1_numbers):
            pos = group1_positions[idx]
            lathe_x = start_x
            lathe_y = start_y + pos['row'] * (lathe_height + row_gap) + pos['row_offset']

            # 车轮车床主体
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"车轮车床-{str(num).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'lathe',
                'status': 'running',
                'pos_x': lathe_x + 20,
                'pos_y': lathe_y,
                'pos_width': lathe_width - 20,
                'pos_height': lathe_height,
            })
            device_id += 1

            # 防护套自动装卸装置
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"防护套装卸装置-{str(num).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'protect',
                'status': 'running',
                'pos_x': lathe_x + 5,
                'pos_y': lathe_y + 8,
                'pos_width': lathe_width // 5 - 8,
                'pos_height': 38,
            })
            device_id += 1

            # 升降货叉式上下料装置
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"升降货叉装置-{str(num).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'forklift',
                'status': 'running',
                'pos_x': lathe_x + 5,
                'pos_y': lathe_y + 52,
                'pos_width': lathe_width // 5 - 8,
                'pos_height': 38,
            })
            device_id += 1

        # 第二组：04、05、06（右列）
        group2_numbers = [4, 5, 6]  # 编号04, 05, 06
        group2_positions = [
            {'row': 2, 'row_offset': -10},  # 04: 第三行，偏移-10
            {'row': 1, 'row_offset': 0},    # 05: 第二行，无偏移
            {'row': 0, 'row_offset': 10},   # 06: 第一行，偏移+10
        ]

        for idx, num in enumerate(group2_numbers):
            pos = group2_positions[idx]
            lathe_x = start_x + lathe_width + col_gap
            lathe_y = start_y + pos['row'] * (lathe_height + row_gap) + pos['row_offset']

            # 车轮车床主体
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"车轮车床-{str(num).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'lathe',
                'status': 'running',
                'pos_x': lathe_x + 5,
                'pos_y': lathe_y,
                'pos_width': lathe_width - 20,
                'pos_height': lathe_height,
            })
            device_id += 1

            # 防护套自动装卸装置
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"防护套装卸装置-{str(num).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'protect',
                'status': 'running',
                'pos_x': lathe_x + 80,
                'pos_y': lathe_y + 52,
                'pos_width': lathe_width // 5 - 8,
                'pos_height': 38,
            })
            device_id += 1

            # 升降货叉式上下料装置
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"升降货叉装置-{str(num).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'forklift',
                'status': 'running',
                'pos_x': lathe_x + 80,
                'pos_y': lathe_y + 8,
                'pos_width': lathe_width // 5 - 8,
                'pos_height': 38,
            })
            device_id += 1

        # 设置部分设备的故障状态（用于演示）
        import random
        random.seed(42)  # 固定随机种子，保证每次初始化结果一致
        fault_devices = random.sample(devices_data, 3)  # 随机选3台设备故障
        fault_time_map = {}
        for dev in fault_devices:
            dev['status'] = 'fault'
            # 随机故障时间：1小时到3小时之间
            hours = random.uniform(1, 3)
            fault_time_map[dev['device_id']] = timezone.now() - timezone.timedelta(hours=hours)

        for device_data in devices_data:
            device_id = device_data['device_id']
            if device_id in fault_time_map:
                device_data['fault_time'] = fault_time_map[device_id]
            # 将字符串转换为外键实例
            device_data['area'] = area_map.get(device_data['area'])
            device_data['device_type'] = device_type_map.get(device_data['device_type'])
            Device.objects.create(**device_data)

        self.stdout.write(f'创建了 {len(devices_data)} 台设备')
        self.stdout.write(self.style.SUCCESS('数据初始化完成！'))
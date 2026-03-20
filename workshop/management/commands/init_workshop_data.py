from django.core.management.base import BaseCommand
from django.utils import timezone
from workshop.models import Device, DeviceArea


class Command(BaseCommand):
    help = '初始化车间设备数据（2026-03-17更新）'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化数据...')

        # 清空现有数据
        Device.objects.all().delete()
        DeviceArea.objects.all().delete()

        # 布局参数
        LEFT_WIDTH = 600      # 轮轴间宽度
        MIDDLE_WIDTH = 400    # 探伤间宽度
        RIGHT_WIDTH = 400     # 旋轮间宽度
        RAIL_Y = [80, 150, 220, 320, 390, 460]  # 6条钢轨Y坐标

        # 创建区域
        areas_data = [
            {
                'name': '轮轴间',
                'pos_x': 10, 'pos_y': 40,
                'width': LEFT_WIDTH - 20, 'height': 540,
                'color': 'rgba(52, 152, 219, 0.06)',
                'border_color': 'rgba(52, 152, 219, 0.5)',
                'sort_order': 1
            },
            {
                'name': '探伤间',
                'pos_x': LEFT_WIDTH + 10, 'pos_y': 40,
                'width': MIDDLE_WIDTH - 20, 'height': 540,
                'color': 'rgba(46, 204, 113, 0.06)',
                'border_color': 'rgba(46, 204, 113, 0.5)',
                'sort_order': 2
            },
            {
                'name': '旋轮间',
                'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + 10, 'pos_y': 40,
                'width': RIGHT_WIDTH - 20, 'height': 540,
                'color': 'rgba(155, 89, 182, 0.06)',
                'border_color': 'rgba(155, 89, 182, 0.5)',
                'sort_order': 3
            },
        ]

        for area_data in areas_data:
            DeviceArea.objects.create(**area_data)
        self.stdout.write(f'创建了 {len(areas_data)} 个区域')

        # 设备基础尺寸
        DW, DH = 100, 45
        SMALL_W, SMALL_H = 55, 20

        # 创建设备列表
        devices_data = []
        device_id = 1

        # ==================== 轮轴间设备 ====================
        # 钢轨1-3：轮对自动检测机(前移60)、轴承退卸机、轮对除锈机（后两列位置不变）
        lun_zhou_devices_123 = [
            {'name': '轮对自动检测机', 'type': 'detect', 'x_offset': 80},  # 前移60
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
                devices_data.append({
                    'device_id': f'D{str(device_id).zfill(3)}',
                    'name': f"{device['name']}-{rail_idx + 1}-{dev_idx + 1}",
                    'area': '轮轴间',
                    'device_type': device['type'],
                    'status': 'running',
                    'pos_x': x,
                    'pos_y': y,
                    'pos_width': DW,
                    'pos_height': DH,
                })
                device_id += 1

        # 钢轨4-5设备
        for rail_idx in range(3, 5):
            for dev_idx, device in enumerate(lun_zhou_devices_45):
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

        # 轴承堆垛系统（墙外下方）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承堆垛系统',
            'area': '墙外',
            'device_type': 'stacker',
            'status': 'running',
            'pos_x': 200,
            'pos_y': 620,
            'pos_width': 180,
            'pos_height': 45,
            'capacity': 500,
            'used': 328,
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

        # 第三组：纵向钢轨3与钢轨1-6的交叉点处（x=945，对应转盘-10到转盘-15）
        # 纵向钢轨3中心在x=960，转盘直径40，x=960-20+5=945
        for i in range(6):
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f'转盘-{i + 10}',
                'area': '探伤间',
                'device_type': 'turntable',
                'status': 'running',
                'pos_x': 945,
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
        for rail_idx in range(3):
            for dev_idx, device in enumerate(tan_shang_devices_123):
                # 第二列设备（轮对超声波探伤机）往左移动20
                x_offset = 130 if dev_idx == 1 else 150
                x = LEFT_WIDTH + 30 + dev_idx * x_offset
                y = RAIL_Y[rail_idx] + 10 - DH // 2
                devices_data.append({
                    'device_id': f'D{str(device_id).zfill(3)}',
                    'name': f"{device['name']}-{rail_idx + 1}",
                    'area': '探伤间',
                    'device_type': device['type'],
                    'status': 'running',
                    'pos_x': x,
                    'pos_y': y,
                    'pos_width': DW,
                    'pos_height': DH,
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

        # 轴承智能选配立体库（Y与轮轴间房间平齐）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承智能选配立体库',
            'area': '探伤间',
            'device_type': 'warehouse',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 30,
            'pos_y': 520,
            'pos_width': 220,
            'pos_height': 45,
            'capacity': 1000,
            'used': 756,
        })
        device_id += 1

        # 轴承上料机器人（在立体库右边）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '轴承上料机器人',
            'area': '探伤间',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': LEFT_WIDTH + 260,
            'pos_y': 520,
            'pos_width': 100,
            'pos_height': 45,
        })
        device_id += 1

        # 标志牌识别机（3号钢轨起始位置处，轮轴间左边墙体外）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '标志牌识别机',
            'area': '墙外',
            'device_type': 'detect',
            'status': 'running',
            'pos_x': -75,
            'pos_y': RAIL_Y[2] + 10 - DH // 2,
            'pos_width': 50,
            'pos_height': 45,
        })
        device_id += 1

        # ==================== 旋轮间设备 ====================
        # 天车设备（第六条钢轨下方，靠近旋轮间左边墙体，纵向排列）
        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '天车设备-1',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + 10,
            'pos_y': RAIL_Y[5] + 50,
            'pos_width': 80,
            'pos_height': 35,
        })
        device_id += 1

        devices_data.append({
            'device_id': f'D{str(device_id).zfill(3)}',
            'name': '天车设备-2',
            'area': '旋轮间',
            'device_type': 'crane',
            'status': 'running',
            'pos_x': LEFT_WIDTH + MIDDLE_WIDTH + 10,
            'pos_y': RAIL_Y[5] + 95,
            'pos_width': 80,
            'pos_height': 35,
        })
        device_id += 1

        # 6个车轮车床，布局改为3行2列
        lathe_width = 90
        lathe_height = 100
        col_gap = 20               # 两列间距
        row_gap = 30               # 两行间距
        # 居中计算：旋轮间宽度400，两列车床+间距 = 180*2 + 20 = 380，居中偏移 = (400-380)/2 = 10
        start_x = LEFT_WIDTH + MIDDLE_WIDTH + 100
        start_y = 100

        for i in range(6):
            # 计算行列位置：3行2列
            row = i // 2      # 行号 0, 0, 1, 1, 2, 2
            col = i % 2       # 列号 0, 1, 0, 1, 0, 1

            # 行偏移：第一行往下10，第三行往上10
            row_offset = 10 if row == 0 else (-10 if row == 2 else 0)

            lathe_x = start_x + col * (lathe_width + col_gap)
            lathe_y = start_y + row * (lathe_height + row_gap) + row_offset

            # 车轮车床主体
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"车轮车床-{str(i + 1).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'lathe',
                'status': 'running',
                'pos_x': lathe_x,
                'pos_y': lathe_y,
                'pos_width': lathe_width,
                'pos_height': lathe_height,
            })
            device_id += 1

            # 防护套自动装卸装置（集成在车床左边1/5处）
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"防护套装卸装置-{str(i + 1).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'protect',
                'status': 'running',
                'pos_x': lathe_x + 5,
                'pos_y': lathe_y + 8,
                'pos_width': lathe_width // 5 - 8,
                'pos_height': 38,
            })
            device_id += 1

            # 升降货叉式上下料装置（集成在车床左边1/5处）
            devices_data.append({
                'device_id': f'D{str(device_id).zfill(3)}',
                'name': f"升降货叉装置-{str(i + 1).zfill(2)}",
                'area': '旋轮间',
                'device_type': 'forklift',
                'status': 'running',
                'pos_x': lathe_x + 5,
                'pos_y': lathe_y + 52,
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
            Device.objects.create(**device_data)

        self.stdout.write(f'创建了 {len(devices_data)} 台设备')
        self.stdout.write(self.style.SUCCESS('数据初始化完成！'))
from django.core.management.base import BaseCommand
from django.utils import timezone
from workshop.models import Device, DeviceArea


class Command(BaseCommand):
    help = '初始化车间设备数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化数据...')

        # 清空现有数据
        Device.objects.all().delete()
        DeviceArea.objects.all().delete()

        # 创建区域
        areas_data = [
            {'name': '测量区', 'pos_x': 80, 'pos_y': 70, 'width': 550, 'height': 130,
             'color': 'rgba(52, 152, 219, 0.08)', 'border_color': 'rgba(52, 152, 219, 0.3)', 'sort_order': 1},
            {'name': '压装区', 'pos_x': 80, 'pos_y': 200, 'width': 580, 'height': 130,
             'color': 'rgba(46, 204, 113, 0.08)', 'border_color': 'rgba(46, 204, 113, 0.3)', 'sort_order': 2},
            {'name': '传输区', 'pos_x': 80, 'pos_y': 330, 'width': 580, 'height': 100,
             'color': 'rgba(241, 196, 15, 0.08)', 'border_color': 'rgba(241, 196, 15, 0.3)', 'sort_order': 3},
            {'name': '立体库', 'pos_x': 680, 'pos_y': 70, 'width': 240, 'height': 360,
             'color': 'rgba(155, 89, 182, 0.08)', 'border_color': 'rgba(155, 89, 182, 0.3)', 'sort_order': 4},
            {'name': '控制区', 'pos_x': 940, 'pos_y': 70, 'width': 200, 'height': 230,
             'color': 'rgba(26, 188, 156, 0.08)', 'border_color': 'rgba(26, 188, 156, 0.3)', 'sort_order': 5},
            {'name': '防护区', 'pos_x': 940, 'pos_y': 300, 'width': 380, 'height': 110,
             'color': 'rgba(52, 73, 94, 0.08)', 'border_color': 'rgba(52, 73, 94, 0.3)', 'sort_order': 6},
            {'name': '动力区', 'pos_x': 1180, 'pos_y': 70, 'width': 280, 'height': 210,
             'color': 'rgba(231, 76, 60, 0.08)', 'border_color': 'rgba(231, 76, 60, 0.3)', 'sort_order': 7},
        ]

        for area_data in areas_data:
            DeviceArea.objects.create(**area_data)
        self.stdout.write(f'创建了 {len(areas_data)} 个区域')

        # 创建设备
        devices_data = [
            # 测量区
            {'device_id': 'D001', 'name': '内径测量机', 'area': '测量区', 'device_type': 'measure',
             'description': '轴承内径自动测量', 'status': 'running',
             'pos_x': 100, 'pos_y': 100, 'pos_width': 140, 'pos_height': 80},
            {'device_id': 'D002', 'name': '轴颈自动测量机-1', 'area': '测量区', 'device_type': 'measure',
             'description': '轴颈尺寸自动测量', 'status': 'running',
             'pos_x': 280, 'pos_y': 100, 'pos_width': 140, 'pos_height': 80},
            {'device_id': 'D003', 'name': '轴颈自动测量机-2', 'area': '测量区', 'device_type': 'measure',
             'description': '轴颈尺寸自动测量', 'status': 'fault',
             'pos_x': 460, 'pos_y': 100, 'pos_width': 140, 'pos_height': 80},

            # 压装区
            {'device_id': 'D004', 'name': '轴承压装机-1', 'area': '压装区', 'device_type': 'press',
             'description': '轴承自动压装', 'status': 'running',
             'pos_x': 100, 'pos_y': 220, 'pos_width': 160, 'pos_height': 90},
            {'device_id': 'D005', 'name': '轴承压装机-2', 'area': '压装区', 'device_type': 'press',
             'description': '轴承自动压装', 'status': 'fault',
             'pos_x': 300, 'pos_y': 220, 'pos_width': 160, 'pos_height': 90},
            {'device_id': 'D006', 'name': '轴承同温定位平台', 'area': '压装区', 'device_type': 'platform',
             'description': '轴承温度平衡与定位', 'status': 'running',
             'pos_x': 500, 'pos_y': 220, 'pos_width': 140, 'pos_height': 90},

            # 传输区
            {'device_id': 'D007', 'name': '轴承上料缓存线', 'area': '传输区', 'device_type': 'conveyor',
             'description': '轴承上料缓存输送', 'status': 'running',
             'pos_x': 100, 'pos_y': 350, 'pos_width': 280, 'pos_height': 60},
            {'device_id': 'D008', 'name': '入库缓存线', 'area': '传输区', 'device_type': 'conveyor',
             'description': '成品入库缓存输送', 'status': 'running',
             'pos_x': 420, 'pos_y': 350, 'pos_width': 220, 'pos_height': 60},

            # 立体库
            {'device_id': 'D009', 'name': '智能选配立体库', 'area': '立体库', 'device_type': 'warehouse',
             'description': '4排×26列×6层=624货位', 'status': 'running',
             'pos_x': 700, 'pos_y': 100, 'pos_width': 200, 'pos_height': 310,
             'capacity': 624, 'used': 458},

            # 控制区
            {'device_id': 'D010', 'name': '1号电控柜', 'area': '控制区', 'device_type': 'cabinet',
             'status': 'running', 'pos_x': 960, 'pos_y': 100, 'pos_width': 70, 'pos_height': 80},
            {'device_id': 'D011', 'name': '2号电控柜', 'area': '控制区', 'device_type': 'cabinet',
             'status': 'running', 'pos_x': 1050, 'pos_y': 100, 'pos_width': 70, 'pos_height': 80},
            {'device_id': 'D012', 'name': '3号电控柜', 'area': '控制区', 'device_type': 'cabinet',
             'status': 'running', 'pos_x': 960, 'pos_y': 200, 'pos_width': 70, 'pos_height': 80},
            {'device_id': 'D013', 'name': '4号电控柜', 'area': '控制区', 'device_type': 'cabinet',
             'status': 'offline', 'pos_x': 1050, 'pos_y': 200, 'pos_width': 70, 'pos_height': 80},

            # 防护区
            {'device_id': 'D014', 'name': '1号有机玻璃房', 'area': '防护区', 'device_type': 'room',
             'status': 'running', 'pos_x': 960, 'pos_y': 320, 'pos_width': 100, 'pos_height': 70},
            {'device_id': 'D015', 'name': '2号有机玻璃房', 'area': '防护区', 'device_type': 'room',
             'status': 'running', 'pos_x': 1080, 'pos_y': 320, 'pos_width': 100, 'pos_height': 70},
            {'device_id': 'D016', 'name': '3号有机玻璃房', 'area': '防护区', 'device_type': 'room',
             'status': 'running', 'pos_x': 1200, 'pos_y': 320, 'pos_width': 100, 'pos_height': 70},

            # 动力区
            {'device_id': 'D017', 'name': '液压站', 'area': '动力区', 'device_type': 'power',
             'status': 'running', 'pos_x': 1200, 'pos_y': 100, 'pos_width': 100, 'pos_height': 70},
            {'device_id': 'D018', 'name': '空压机', 'area': '动力区', 'device_type': 'power',
             'status': 'running', 'pos_x': 1320, 'pos_y': 100, 'pos_width': 80, 'pos_height': 70},
            {'device_id': 'D019', 'name': '冷却水循环系统', 'area': '动力区', 'device_type': 'power',
             'status': 'running', 'pos_x': 1200, 'pos_y': 200, 'pos_width': 120, 'pos_height': 60},
            {'device_id': 'D020', 'name': '集中润滑系统', 'area': '动力区', 'device_type': 'power',
             'status': 'fault', 'pos_x': 1340, 'pos_y': 200, 'pos_width': 100, 'pos_height': 60},
        ]

        # 设置部分设备的故障时间
        fault_times = {
            'D003': timezone.now() - timezone.timedelta(minutes=45),  # 45分钟
            'D005': timezone.now() - timezone.timedelta(hours=3),      # 3小时
            'D020': timezone.now() - timezone.timedelta(hours=1, minutes=30),  # 1.5小时
        }

        for device_data in devices_data:
            device_id = device_data['device_id']
            if device_id in fault_times:
                device_data['fault_time'] = fault_times[device_id]
            Device.objects.create(**device_data)

        self.stdout.write(f'创建了 {len(devices_data)} 台设备')
        self.stdout.write(self.style.SUCCESS('数据初始化完成！'))
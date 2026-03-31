"""
外部数据同步服务
从外部API获取点检和维修数据，更新设备状态
"""
import requests
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from workshop.models import Device, InspectionRecord, RepairRecord, SyncConfig


class DataSyncService:
    """数据同步服务"""

    # 长时间故障阈值（小时）
    LONG_FAULT_HOURS = 2

    @staticmethod
    def _time_equals(t1, t2):
        """比较两个时间是否相等（忽略微秒差异）"""
        if t1 is None and t2 is None:
            return True
        if t1 is None or t2 is None:
            return False
        # 比较到秒级别
        return t1.replace(microsecond=0) == t2.replace(microsecond=0)

    @staticmethod
    def _compare_inspection_data(record, item):
        """比较点检记录与API数据是否相同"""
        start_time = DataSyncService._parse_timestamp(item.get('startTime'))
        end_time = DataSyncService._parse_timestamp(item.get('endTime'))

        return (
            record.device_name == item.get('name', '') and
            record.location == item.get('position', '') and
            DataSyncService._time_equals(record.start_time, start_time) and
            DataSyncService._time_equals(record.end_time, end_time)
        )

    @staticmethod
    def _compare_repair_data(record, item):
        """比较维修记录与API数据是否相同"""
        fault_date = DataSyncService._parse_timestamp(item.get('faultDate'))
        repair_date = DataSyncService._parse_timestamp(item.get('fixDate'))
        is_resolved = repair_date is not None

        return (
            record.device_name == item.get('name', '') and
            record.location == item.get('position', '') and
            record.model == item.get('model', '') and
            record.department == item.get('dpname', '') and
            record.team_name == item.get('teamsname', '') and
            DataSyncService._time_equals(record.fault_date, fault_date) and
            record.reporter == item.get('finder', '') and
            record.phenomenon == item.get('describe', '') and
            record.analysis == item.get('analysis', '') and
            DataSyncService._time_equals(record.repair_date, repair_date) and
            record.repair_team == item.get('fixteamsname', '') and
            record.worker == item.get('fixer', '') and
            record.result == item.get('fixDescribe', '') and
            record.materials == item.get('material', '') and
            record.is_resolved == is_resolved
        )

    @classmethod
    def sync_inspection_data(cls, date=None, teamsname=None):
        """
        同步点检数据

        参数:
            date: 日期字符串，如 '2026-03-18'，默认今天
            teamsname: 班组名称，如 '轮轴班'，不传则获取所有班组

        返回: (success, message, count)
        """
        try:
            config = SyncConfig.objects.get(name='点检数据')
        except SyncConfig.DoesNotExist:
            return False, '请先在后台创建"点检数据"同步配置', 0

        if not config.is_enabled:
            return False, '同步已禁用', 0

        try:
            # 构建请求URL - date默认为今天
            url = config.api_url
            if not date:
                date = timezone.now().strftime('%Y-%m-%d')
            url += f'&date={date}'
            if teamsname:
                url += f'&teamsname={teamsname}'

            headers = {}
            if config.api_key:
                headers['Authorization'] = f'Bearer {config.api_key}'

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 解析数据并保存（智能更新逻辑）
            sync_date = timezone.now().strptime(date, '%Y-%m-%d').date() if date else timezone.now().date()
            count = 0
            updated_count = 0
            skipped_count = 0
            with transaction.atomic():
                for item in data:
                    equipment_no = item.get('equipmentNo')
                    if not equipment_no:
                        continue

                    start_time = cls._parse_timestamp(item.get('startTime'))

                    # 查找该日期该设备的点检记录
                    existing = InspectionRecord.objects.filter(
                        device_id=equipment_no,
                        start_time__date=sync_date
                    ).first()

                    if existing:
                        # 比较数据是否相同
                        if cls._compare_inspection_data(existing, item):
                            skipped_count += 1  # 数据相同，跳过
                            continue
                        else:
                            # 数据不同，更新记录
                            existing.device_name = item.get('name', '')
                            existing.location = item.get('position', '')
                            existing.end_time = cls._parse_timestamp(item.get('endTime'))
                            existing.save()
                            updated_count += 1
                            count += 1
                    else:
                        # 今天无记录，新增
                        InspectionRecord.objects.create(
                            device_id=equipment_no,
                            device_name=item.get('name', ''),
                            location=item.get('position', ''),
                            start_time=start_time,
                            end_time=cls._parse_timestamp(item.get('endTime')),
                        )
                        count += 1

            # 更新同步状态
            config.last_sync = timezone.now()
            config.last_status = 'success'
            config.last_error = ''
            config.save()

            return True, f'成功同步 {count} 条点检记录（新增/更新 {count}，跳过相同 {skipped_count}）', count

        except Exception as e:
            config.last_sync = timezone.now()
            config.last_status = 'failed'
            config.last_error = str(e)
            config.save()
            return False, f'同步失败: {str(e)}', 0

    @classmethod
    def sync_repair_data(cls, date=None, dpname=None):
        """
        同步维修数据

        参数:
            date: 日期字符串，如 '2026-03-11'，默认今天
            dpname: 部门名称，如 '修配车间'

        返回: (success, message, count)
        """
        try:
            config = SyncConfig.objects.get(name='维修数据')
        except SyncConfig.DoesNotExist:
            return False, '请先在后台创建"维修数据"同步配置', 0

        if not config.is_enabled:
            return False, '同步已禁用', 0

        try:
            # 构建请求URL - date默认为今天
            url = config.api_url
            if not date:
                date = timezone.now().strftime('%Y-%m-%d')
            url += f'&date={date}'
            if dpname:
                url += f'&dpname={dpname}'

            headers = {}
            if config.api_key:
                headers['Authorization'] = f'Bearer {config.api_key}'

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 解析数据并保存（智能更新逻辑）
            sync_date = timezone.now().strptime(date, '%Y-%m-%d').date() if date else timezone.now().date()
            count = 0
            skipped_count = 0
            with transaction.atomic():
                for item in data:
                    # 跳过非字典数据
                    if not isinstance(item, dict):
                        continue

                    device_id = item.get('equipmentNo')
                    if not device_id:
                        continue

                    # 解析时间
                    fault_date = cls._parse_timestamp(item.get('faultDate'))
                    repair_date = cls._parse_timestamp(item.get('fixDate'))
                    is_resolved = repair_date is not None
                    external_id = item.get('id')

                    # 查找该日期该设备的维修记录（按外部ID或设备ID+日期）
                    existing = None
                    if external_id:
                        existing = RepairRecord.objects.filter(external_id=external_id).first()
                    if not existing:
                        existing = RepairRecord.objects.filter(
                            device_id=device_id,
                            fault_date__date=sync_date
                        ).first()

                    if existing:
                        # 比较数据是否相同
                        if cls._compare_repair_data(existing, item):
                            skipped_count += 1  # 数据相同，跳过
                            continue
                        else:
                            # 数据不同，更新记录
                            existing.device_name = item.get('name', '')
                            existing.location = item.get('position', '')
                            existing.model = item.get('model', '')
                            existing.department = item.get('dpname', '')
                            existing.team_name = item.get('teamsname', '')
                            existing.fault_date = fault_date
                            existing.reporter = item.get('finder', '')
                            existing.phenomenon = item.get('describe', '')
                            existing.analysis = item.get('analysis', '')
                            existing.repair_date = repair_date
                            existing.repair_team = item.get('fixteamsname', '')
                            existing.worker = item.get('fixer', '')
                            existing.result = item.get('fixDescribe', '')
                            existing.materials = item.get('material', '')
                            existing.is_resolved = is_resolved
                            if external_id:
                                existing.external_id = external_id
                            existing.save()
                            count += 1
                    else:
                        # 今天无记录，新增
                        RepairRecord.objects.create(
                            device_id=device_id,
                            device_name=item.get('name', ''),
                            location=item.get('position', ''),
                            model=item.get('model', ''),
                            department=item.get('dpname', ''),
                            team_name=item.get('teamsname', ''),
                            fault_date=fault_date,
                            reporter=item.get('finder', ''),
                            phenomenon=item.get('describe', ''),
                            analysis=item.get('analysis', ''),
                            repair_date=repair_date,
                            repair_team=item.get('fixteamsname', ''),
                            worker=item.get('fixer', ''),
                            result=item.get('fixDescribe', ''),
                            materials=item.get('material', ''),
                            is_resolved=is_resolved,
                            external_id=external_id,
                        )
                        count += 1

            # 更新同步状态
            config.last_sync = timezone.now()
            config.last_status = 'success'
            config.last_error = ''
            config.save()

            return True, f'成功同步 {count} 条维修记录（新增/更新 {count}，跳过相同 {skipped_count}）', count

        except Exception as e:
            config.last_sync = timezone.now()
            config.last_status = 'failed'
            config.last_error = str(e)
            config.save()
            return False, f'同步失败: {str(e)}', 0

    @classmethod
    def update_device_status(cls):
        """
        根据点检和维修记录更新设备状态

        状态判断逻辑：
        - 如果 auto_status=False：保持手动设置的状态，不自动更新
        - 如果 auto_status=True：根据点检/维修记录自动判断
          1. 维修记录（当天）：
             - 当天有故障日期但没有维修日期 → 故障
             - 超过2小时仍然没有维修日期 → 长时间故障
             - 有故障时间且有维修日期 → 恢复（根据点检判断）
          2. 点检记录：
             - 有开工点检时间但没有完工点检时间 → 运行中
             - 有开工点检时间且有完工点检时间 → 离线
        """
        devices = Device.objects.all()
        updated_count = 0
        today = timezone.now().date()
        now = timezone.now()

        for device in devices:
            # 如果禁用自动状态判断，跳过该设备
            if not device.auto_status:
                continue

            old_status = device.status
            new_status = 'offline'
            fault_time = None

            # 1. 先检查当天的维修记录
            today_faults = RepairRecord.objects.filter(
                device_id=device.device_id,
                fault_date__date=today
            ).order_by('-fault_date')

            # 找出当天有故障日期但没有维修日期的记录
            unresolved_today = today_faults.filter(repair_date__isnull=True).first()

            if unresolved_today:
                fault_time = unresolved_today.fault_date
                # 判断是否超过2小时
                hours_since_fault = (now - fault_time).total_seconds() / 3600
                if hours_since_fault > cls.LONG_FAULT_HOURS:
                    new_status = 'longFault'
                else:
                    new_status = 'fault'
            else:
                # 2. 检查点检状态（只查询当天的点检记录）
                latest_inspection = InspectionRecord.objects.filter(
                    device_id=device.device_id,
                    start_time__date=today
                ).order_by('-start_time').first()

                if latest_inspection:
                    device.inspection_start = latest_inspection.start_time
                    device.inspection_end = latest_inspection.end_time
                    device.inspection_location = latest_inspection.location

                    # 有开工时间且无完工时间 = 运行中
                    if latest_inspection.start_time and not latest_inspection.end_time:
                        new_status = 'running'
                    # 有完工时间 = 离线
                    elif latest_inspection.end_time:
                        new_status = 'offline'
                else:
                    device.inspection_start = None
                    device.inspection_end = None
                    device.inspection_location = ''

            # 更新设备状态
            if new_status != old_status or device.fault_time != fault_time:
                device.status = new_status
                device.fault_time = fault_time
                device.save()
                updated_count += 1

        return updated_count

    @classmethod
    def sync_all(cls, date=None, teamsname=None, dpname=None):
        """
        执行完整同步：同步点检数据、维修数据、更新设备状态

        参数:
            date: 日期字符串
            teamsname: 班组名称（点检数据用）
            dpname: 部门名称（维修数据用）
        """
        results = {
            'inspection': cls.sync_inspection_data(date=date, teamsname=teamsname),
            'repair': cls.sync_repair_data(date=date, dpname=dpname),
            'status_update': 0
        }

        # 如果点检或维修数据同步成功，更新设备状态
        if results['inspection'][0] or results['repair'][0]:
            results['status_update'] = cls.update_device_status()

        return results

    @staticmethod
    def _parse_timestamp(value):
        """
        解析毫秒时间戳

        支持格式:
        - 毫秒时间戳: 1773217620000
        - 秒时间戳: 1773217620
        - ISO格式: 2026-03-18T10:00:00
        - 字符串: 2026-03-18 10:00:00
        """
        if not value:
            return None

        # 如果是数字类型（时间戳）
        if isinstance(value, (int, float)):
            # 判断是秒还是毫秒（毫秒时间戳通常大于1000000000000）
            if value > 1000000000000:
                # 毫秒时间戳
                return datetime.fromtimestamp(value / 1000)
            else:
                # 秒时间戳
                return datetime.fromtimestamp(value)

        # 如果是字符串类型的数字
        if isinstance(value, str):
            try:
                num = float(value)
                if num > 1000000000000:
                    return datetime.fromtimestamp(num / 1000)
                else:
                    return datetime.fromtimestamp(num)
            except ValueError:
                pass

        # 尝试解析日期字符串
        return cls._parse_datetime(value)

    @staticmethod
    def _parse_datetime(value):
        """解析日期时间字符串"""
        if not value:
            return None

        from datetime import datetime

        # 支持多种格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue

        return None
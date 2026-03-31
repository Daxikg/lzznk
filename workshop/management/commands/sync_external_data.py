"""
手动同步数据的管理命令
用法:
  python manage.py sync_external_data
  python manage.py sync_external_data --date=2026-03-18 --teamsname=轮轴班 --dpname=修配车间
"""
from django.core.management.base import BaseCommand
from workshop.services import DataSyncService


class Command(BaseCommand):
    help = '从外部API同步点检和维修数据，更新设备状态'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='指定日期，格式：2026-03-18，默认今天',
        )
        parser.add_argument(
            '--teamsname',
            type=str,
            help='指定班组名称（点检数据用），如：轮轴班',
        )
        parser.add_argument(
            '--dpname',
            type=str,
            help='指定部门名称（维修数据用），如：修配车间',
        )
        parser.add_argument(
            '--inspection',
            action='store_true',
            help='只同步点检数据',
        )
        parser.add_argument(
            '--repair',
            action='store_true',
            help='只同步维修数据',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='只更新设备状态',
        )

    def handle(self, *args, **options):
        service = DataSyncService()
        date = options.get('date')
        teamsname = options.get('teamsname')
        dpname = options.get('dpname')

        if options['inspection']:
            self.stdout.write(f'正在同步点检数据... 日期={date}, 班组={teamsname}')
            success, message, count = service.sync_inspection_data(date=date, teamsname=teamsname)
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))
            return

        if options['repair']:
            self.stdout.write(f'正在同步维修数据... 日期={date}, 部门={dpname}')
            success, message, count = service.sync_repair_data(date=date, dpname=dpname)
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))
            return

        if options['status']:
            self.stdout.write('正在更新设备状态...')
            count = service.update_device_status()
            self.stdout.write(self.style.SUCCESS(f'更新了 {count} 台设备状态'))
            return

        # 默认执行完整同步
        self.stdout.write(f'开始完整同步... 日期={date}, 班组={teamsname}, 部门={dpname}')
        results = service.sync_all(date=date, teamsname=teamsname, dpname=dpname)

        # 输出结果
        insp_success, insp_msg, insp_count = results['inspection']
        if insp_success:
            self.stdout.write(self.style.SUCCESS(f'点检数据: {insp_msg}'))
        else:
            self.stdout.write(self.style.ERROR(f'点检数据: {insp_msg}'))

        repair_success, repair_msg, repair_count = results['repair']
        if repair_success:
            self.stdout.write(self.style.SUCCESS(f'维修数据: {repair_msg}'))
        else:
            self.stdout.write(self.style.ERROR(f'维修数据: {repair_msg}'))

        self.stdout.write(self.style.SUCCESS(f'设备状态更新: {results["status_update"]} 台'))

        self.stdout.write(self.style.SUCCESS('同步完成!'))
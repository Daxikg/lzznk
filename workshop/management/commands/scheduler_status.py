"""
定时任务管理命令
用法:
  python manage.py scheduler_status   # 查看状态
  python manage.py scheduler_start    # 启动
  python manage.py scheduler_stop     # 停止
"""
from django.core.management.base import BaseCommand
from workshop.scheduler import start_scheduler, stop_scheduler, get_scheduler_status


class Command(BaseCommand):
    help = '定时任务管理：查看状态、启动、停止'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['status', 'start', 'stop'],
            help='操作：status(查看状态)、start(启动)、stop(停止)',
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'status':
            status = get_scheduler_status()
            if status['running']:
                self.stdout.write(self.style.SUCCESS('定时任务运行中'))
            else:
                self.stdout.write(self.style.WARNING('定时任务未运行'))

            self.stdout.write('\n定时任务列表:')
            for job in status['jobs']:
                self.stdout.write(f"  - {job['name']}: 下次执行 {job['next_run']}")

        elif action == 'start':
            start_scheduler()
            self.stdout.write(self.style.SUCCESS('定时任务已启动'))

        elif action == 'stop':
            stop_scheduler()
            self.stdout.write(self.style.SUCCESS('定时任务已停止'))
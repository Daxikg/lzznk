from django.apps import AppConfig


class WorkshopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workshop'
    verbose_name = '车间设备监控'

    def ready(self):
        """应用启动时执行"""
        # 避免在 Django 自动重载进程中启动定时任务
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            # 启动定时任务
            from .scheduler import start_scheduler
            start_scheduler()
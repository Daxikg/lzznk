from django.apps import AppConfig


class WorkshopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workshop'
    verbose_name = '车间设备监控'

    def ready(self):
        """应用启动时执行"""
        import os
        import sys
        import logging

        logger = logging.getLogger(__name__)

        # 打印调试信息
        run_main = os.environ.get('RUN_MAIN')
        noreload = '--noreload' in sys.argv
        gunicorn_worker = os.environ.get('GUNICORN_WORKER')
        uwsgi_worker = os.environ.get('UWSGI_WORKER')

        logger.info(f'[workshop] 环境检查: RUN_MAIN={run_main}, noreload={noreload}')
        logger.info(f'[workshop] Worker检查: GUNICORN_WORKER={gunicorn_worker}, UWSGI_WORKER={uwsgi_worker}')

        # 判断是否应该启动定时任务
        # PyCharm runserver: RUN_MAIN为'true'或None（取决于配置）
        # 生产模式：不是worker进程
        should_start = (
            run_main == 'true' or
            noreload or
            (not gunicorn_worker and not uwsgi_worker and run_main is not None)
        )

        logger.info(f'[workshop] should_start={should_start}')

        if should_start:
            from .scheduler import start_scheduler
            start_scheduler()
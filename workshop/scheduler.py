"""
定时任务调度器
每天7:00-19:00，每5分钟同步一次数据
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from workshop.services import DataSyncService


scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)


def sync_inspection_lunzhou():
    """同步轮轴班点检数据"""
    DataSyncService.sync_inspection_data(teamsname='轮轴班')


def sync_inspection_tanshang():
    """同步探伤班点检数据"""
    DataSyncService.sync_inspection_data(teamsname='探伤班')


def sync_repair_xiupei():
    """同步修配车间维修数据"""
    DataSyncService.sync_repair_data(dpname='修配车间')


def start_scheduler():
    """启动定时任务"""
    if scheduler.running:
        return

    # 每天 7:00-19:00，每5分钟执行一次
    # cron表达式: minute="*/5", hour="7-18" (注意：18表示到18:59，即19:00前)

    # 同步轮轴班点检数据
    scheduler.add_job(
        sync_inspection_lunzhou,
        trigger=CronTrigger(minute='*/5', hour='7-18'),
        id='sync_inspection_lunzhou',
        name='同步轮轴班点检数据',
        replace_existing=True,
    )

    # 同步探伤班点检数据
    scheduler.add_job(
        sync_inspection_tanshang,
        trigger=CronTrigger(minute='*/5', hour='7-18'),
        id='sync_inspection_tanshang',
        name='同步探伤班点检数据',
        replace_existing=True,
    )

    # 同步修配车间维修数据
    scheduler.add_job(
        sync_repair_xiupei,
        trigger=CronTrigger(minute='*/5', hour='7-18'),
        id='sync_repair_xiupei',
        name='同步修配车间维修数据',
        replace_existing=True,
    )

    # 同步完成后自动更新设备状态
    scheduler.add_job(
        DataSyncService.update_device_status,
        trigger=CronTrigger(minute='*/5', hour='7-18'),
        id='update_device_status',
        name='更新设备状态',
        replace_existing=True,
    )

    scheduler.start()
    print('定时任务已启动')


def stop_scheduler():
    """停止定时任务"""
    if scheduler.running:
        scheduler.shutdown()
        print('定时任务已停止')


def get_scheduler_status():
    """获取定时任务状态"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': str(job.next_run_time) if job.next_run_time else None,
        })
    return {
        'running': scheduler.running,
        'jobs': jobs,
    }
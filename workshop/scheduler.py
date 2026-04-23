"""
定时任务调度器
全天每5分钟检查一次，仅在7:00-19:00范围内执行同步任务
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
from workshop.services import DataSyncService
from workshop.models import SchedulerLog

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

# 允许执行的时间范围
WORK_START_HOUR = 7
WORK_END_HOUR = 19


def is_work_time():
    """判断当前是否在工作时间范围内（7:00-19:00）"""
    now = datetime.now()
    return WORK_START_HOUR <= now.hour < WORK_END_HOUR


def log_execution(job_id, job_name, in_work_time, success, message):
    """记录任务执行日志到数据库"""
    try:
        SchedulerLog.objects.create(
            job_id=job_id,
            job_name=job_name,
            is_work_time=in_work_time,
            success=success,
            message=message
        )
    except Exception as e:
        logger.error(f'记录日志失败: {e}')


def safe_execute(func, job_id, job_name):
    """安全执行任务，捕获异常防止任务停止，并记录日志"""
    in_work_time = is_work_time()

    if not in_work_time:
        log_execution(job_id, job_name, False, True, '非工作时间，跳过执行')
        return None

    try:
        result = func()
        log_execution(job_id, job_name, True, True, f'执行成功')
        logger.info(f'定时任务 [{job_name}] 执行成功')
        return result
    except Exception as e:
        log_execution(job_id, job_name, True, False, f'执行失败: {str(e)}')
        logger.error(f'定时任务 [{job_name}] 执行失败: {e}')
        return None


def sync_inspection_lunzhou():
    """同步轮轴班点检数据"""
    safe_execute(
        lambda: DataSyncService.sync_inspection_data(teamsname='轮轴班'),
        'sync_inspection_lunzhou',
        '同步轮轴班点检数据'
    )


def sync_inspection_tanshang():
    """同步探伤班点检数据"""
    safe_execute(
        lambda: DataSyncService.sync_inspection_data(teamsname='探伤班'),
        'sync_inspection_tanshang',
        '同步探伤班点检数据'
    )


def sync_inspection_xinxi():
    """同步信息班点检数据"""
    safe_execute(
        lambda: DataSyncService.sync_inspection_data(teamsname='信息班'),
        'sync_inspection_xinxi',
        '同步信息班点检数据'
    )


def sync_repair_xiupei():
    """同步修配车间维修数据"""
    safe_execute(
        lambda: DataSyncService.sync_repair_data(dpname='修配车间'),
        'sync_repair_xiupei',
        '同步修配车间维修数据'
    )


def check_unresolved_repairs():
    """检查未完成的维修记录，重新查询API获取fixDate"""
    safe_execute(
        DataSyncService.check_unresolved_repairs,
        'check_unresolved_repairs',
        '检查未完成维修记录'
    )


def update_device_status():
    """更新设备状态"""
    safe_execute(
        DataSyncService.update_device_status,
        'update_device_status',
        '更新设备状态'
    )


def start_scheduler():
    """启动定时任务"""
    if scheduler.running:
        return

    # 全天每5分钟检查一次，任务内部判断是否在工作时间范围内执行
    # 使用IntervalTrigger确保调度器始终保持活跃状态，避免跨天问题

    # 同步轮轴班点检数据
    scheduler.add_job(
        sync_inspection_lunzhou,
        trigger=IntervalTrigger(minutes=5),
        id='sync_inspection_lunzhou',
        name='同步轮轴班点检数据',
        replace_existing=True,
    )

    # 同步探伤班点检数据
    scheduler.add_job(
        sync_inspection_tanshang,
        trigger=IntervalTrigger(minutes=5),
        id='sync_inspection_tanshang',
        name='同步探伤班点检数据',
        replace_existing=True,
    )

    # 同步信息班点检数据
    scheduler.add_job(
        sync_inspection_xinxi,
        trigger=IntervalTrigger(minutes=5),
        id='sync_inspection_xinxi',
        name='同步信息班点检数据',
        replace_existing=True,
    )

    # 同步修配车间维修数据
    scheduler.add_job(
        sync_repair_xiupei,
        trigger=IntervalTrigger(minutes=5),
        id='sync_repair_xiupei',
        name='同步修配车间维修数据',
        replace_existing=True,
    )

    # 检查未完成的维修记录，重新查询API获取fixDate
    scheduler.add_job(
        check_unresolved_repairs,
        trigger=IntervalTrigger(minutes=5),
        id='check_unresolved_repairs',
        name='检查未完成维修记录',
        replace_existing=True,
    )

    # 同步完成后自动更新设备状态
    scheduler.add_job(
        update_device_status,
        trigger=IntervalTrigger(minutes=5),
        id='update_device_status',
        name='更新设备状态',
        replace_existing=True,
    )

    scheduler.start()
    logger.info('定时任务已启动')


def stop_scheduler():
    """停止定时任务"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info('定时任务已停止')


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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import render
from .models import Device, DeviceArea, InspectionRecord, RepairRecord, SyncConfig
from .services import DataSyncService
from .scheduler import get_scheduler_status, start_scheduler, stop_scheduler


def workshop_screen(request):
    """大屏展示页面"""
    return render(request, 'workshop/screen.html')


@api_view(['GET'])
@permission_classes([AllowAny])
def get_devices(request):
    """获取所有设备状态"""
    devices = Device.objects.all()
    data = []
    for device in devices:
        # 如果设备设置了linked_device，使用关联设备的状态
        if device.linked_device:
            status = device.linked_device.status
            computed_status = device.linked_device.computed_status
            fault_time = device.linked_device.fault_time
        else:
            status = device.status
            computed_status = device.computed_status
            fault_time = device.fault_time

        item = {
            'id': device.device_id,
            'name': device.name,
            'area': device.area.name if device.area else '',
            'type': device.device_type.code if device.device_type else '',
            'description': device.description,
            'status': status,
            'computedStatus': computed_status,
            'x': device.pos_x,
            'y': device.pos_y,
            'width': device.pos_width,
            'height': device.pos_height,
            'linkedDeviceId': device.linked_device.device_id if device.linked_device else None,
        }
        if fault_time:
            item['faultTime'] = int(fault_time.timestamp() * 1000)
        data.append(item)
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_device_detail(request, device_id):
    """获取单个设备详情"""
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        return Response({'error': '设备不存在'}, status=404)

    # 如果设备设置了linked_device，使用关联设备的状态
    if device.linked_device:
        linked = device.linked_device
        status = linked.status
        computed_status = linked.computed_status
        fault_time = linked.fault_time
        linked_info = {
            'deviceId': linked.device_id,
            'name': linked.name,
        }
    else:
        status = device.status
        computed_status = device.computed_status
        fault_time = device.fault_time
        linked_info = None

    data = {
        'id': device.device_id,
        'name': device.name,
        'area': device.area.name if device.area else '',
        'type': device.device_type.code if device.device_type else '',
        'description': device.description,
        'status': status,
        'computedStatus': computed_status,
        'x': device.pos_x,
        'y': device.pos_y,
        'width': device.pos_width,
        'height': device.pos_height,
        'updatedAt': device.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'linkedDevice': linked_info,
    }
    # 二维码图片URL
    if device.qrcode_image:
        data['qrcodeUrl'] = device.qrcode_image.url
    if fault_time:
        data['faultTime'] = int(fault_time.timestamp() * 1000)
        data['faultStartTime'] = fault_time.strftime('%Y-%m-%d %H:%M:%S')

    # 点检信息
    if device.inspection_start:
        data['inspectionStart'] = device.inspection_start.strftime('%Y-%m-%d %H:%M:%S')
    if device.inspection_end:
        data['inspectionEnd'] = device.inspection_end.strftime('%Y-%m-%d %H:%M:%S')
    if device.inspection_location:
        data['inspectionLocation'] = device.inspection_location

    # 最新维修记录
    latest_repair = RepairRecord.objects.filter(device_id=device_id).order_by('-fault_date').first()
    if latest_repair:
        data['latestRepair'] = {
            'faultDate': latest_repair.fault_date.strftime('%Y-%m-%d %H:%M:%S') if latest_repair.fault_date else '',
            'phenomenon': latest_repair.phenomenon,
            'repairDate': latest_repair.repair_date.strftime('%Y-%m-%d %H:%M:%S') if latest_repair.repair_date else '',
            'worker': latest_repair.worker,
            'result': latest_repair.result,
            'isResolved': latest_repair.is_resolved,
        }

    # 获取最近半年的统计数据
    from datetime import datetime, timedelta
    six_months_ago = timezone.now() - timedelta(days=180)

    # 点检次数
    inspection_count = InspectionRecord.objects.filter(
        device_id=device_id,
        start_time__gte=six_months_ago
    ).count()

    # 故障次数
    fault_count = RepairRecord.objects.filter(
        device_id=device_id,
        fault_date__gte=six_months_ago
    ).count()

    # 故障率（故障次数 / 点检次数）
    fault_rate = round((fault_count / inspection_count) * 100, 2) if inspection_count > 0 else 0

    data['halfYearStats'] = {
        'inspectionCount': inspection_count,
        'faultCount': fault_count,
        'faultRate': fault_rate,
    }

    # 获取最近半年的故障记录列表
    repair_records = RepairRecord.objects.filter(
        device_id=device_id,
        fault_date__gte=six_months_ago
    ).order_by('-fault_date')

    data['repairRecords'] = [{
        'id': r.id,
        'faultDate': r.fault_date.strftime('%Y-%m-%d %H:%M:%S') if r.fault_date else '',
        'reporter': r.reporter,
        'phenomenon': r.phenomenon,
        'analysis': r.analysis,
        'repairDate': r.repair_date.strftime('%Y-%m-%d %H:%M:%S') if r.repair_date else '',
        'repairTeam': r.repair_team,
        'worker': r.worker,
        'result': r.result,
        'materials': r.materials,
        'isResolved': r.is_resolved,
    } for r in repair_records]

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_statistics(request):
    """获取统计数据"""
    devices = Device.objects.all()
    total = devices.count()

    # 统计各状态数量
    status_counts = {}
    for device in devices:
        status = device.computed_status
        status_counts[status] = status_counts.get(status, 0) + 1

    running = status_counts.get('running', 0)
    fault = status_counts.get('fault', 0)
    long_fault = status_counts.get('longFault', 0)
    offline = status_counts.get('offline', 0)

    running_rate = round((running / total) * 100, 1) if total > 0 else 0

    return Response({
        'total': total,
        'running': running,
        'fault': fault,
        'longFault': long_fault,
        'offline': offline,
        'runningRate': running_rate,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_areas(request):
    """获取区域配置"""
    areas = DeviceArea.objects.all()
    data = [{
        'name': area.name,
        'x': area.pos_x,
        'y': area.pos_y,
        'width': area.width,
        'height': area.height,
        'color': area.color,
        'borderColor': area.border_color,
    } for area in areas]
    return Response(data)


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_device_status(request, device_id):
    """更新设备状态"""
    try:
        device = Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        return Response({'error': '设备不存在'}, status=404)

    new_status = request.data.get('status')
    if new_status not in ['running', 'fault', 'offline']:
        return Response({'error': '无效的状态值'}, status=400)

    device.status = new_status
    if new_status == 'fault':
        device.fault_time = timezone.now()
    else:
        device.fault_time = None
    device.save()

    # 同步更新所有跟随者（linked_device指向本设备的设备）
    followers = Device.objects.filter(linked_device=device)
    for follower in followers:
        follower.status = new_status
        follower.fault_time = device.fault_time
        follower.save()

    result = {
        'id': device.device_id,
        'status': device.status,
        'computedStatus': device.computed_status,
    }
    if followers.exists():
        result['followerIds'] = [d.device_id for d in followers]

    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_data(request):
    """一次性获取所有数据（用于大屏初始化）"""
    devices = Device.objects.all()
    areas = DeviceArea.objects.all()

    # 设备数据
    device_data = []
    status_counts = {}
    for device in devices:
        # 如果设备设置了linked_device，使用关联设备的状态
        if device.linked_device:
            status = device.linked_device.status
            computed_status = device.linked_device.computed_status
            fault_time = device.linked_device.fault_time
        else:
            status = device.status
            computed_status = device.computed_status
            fault_time = device.fault_time

        status_counts[computed_status] = status_counts.get(computed_status, 0) + 1

        item = {
            'id': device.device_id,
            'name': device.name,
            'area': device.area.name if device.area else '',
            'type': device.device_type.code if device.device_type else '',
            'description': device.description,
            'status': status,
            'computedStatus': computed_status,
            'x': device.pos_x,
            'y': device.pos_y,
            'width': device.pos_width,
            'height': device.pos_height,
            'linkedDeviceId': device.linked_device.device_id if device.linked_device else None,
        }
        # 二维码图片URL
        if device.qrcode_image:
            item['qrcodeUrl'] = device.qrcode_image.url
        if fault_time:
            item['faultTime'] = int(fault_time.timestamp() * 1000)
        device_data.append(item)

    # 区域数据
    area_data = [{
        'name': area.name,
        'x': area.pos_x,
        'y': area.pos_y,
        'width': area.width,
        'height': area.height,
        'color': area.color,
        'borderColor': area.border_color,
    } for area in areas]

    # 统计数据
    total = devices.count()
    running = status_counts.get('running', 0)
    fault = status_counts.get('fault', 0)
    long_fault = status_counts.get('longFault', 0)
    offline = status_counts.get('offline', 0)
    running_rate = round((running / total) * 100, 1) if total > 0 else 0

    # 获取最近一次同步时间
    sync_configs = SyncConfig.objects.filter(last_status='success').order_by('-last_sync')
    last_sync_time = None
    if sync_configs.exists():
        latest_sync = sync_configs.first()
        last_sync_time = int(latest_sync.last_sync.timestamp() * 1000)

    return Response({
        'devices': device_data,
        'areas': area_data,
        'statistics': {
            'total': total,
            'running': running,
            'fault': fault,
            'longFault': long_fault,
            'offline': offline,
            'runningRate': running_rate,
        },
        'lastSyncTime': last_sync_time,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def sync_data(request):
    """手动触发数据同步"""
    sync_type = request.data.get('type', 'all')
    date = request.data.get('date')
    teamsname = request.data.get('teamsname')
    dpname = request.data.get('dpname')

    if sync_type == 'inspection':
        success, message, count = DataSyncService.sync_inspection_data(date=date, teamsname=teamsname)
    elif sync_type == 'repair':
        success, message, count = DataSyncService.sync_repair_data(date=date, dpname=dpname)
    elif sync_type == 'status':
        count = DataSyncService.update_device_status()
        return Response({'success': True, 'message': f'更新了 {count} 台设备状态'})
    else:
        results = DataSyncService.sync_all(date=date, teamsname=teamsname, dpname=dpname)
        return Response({
            'success': True,
            'inspection': {'success': results['inspection'][0], 'message': results['inspection'][1]},
            'repair': {'success': results['repair'][0], 'message': results['repair'][1]},
            'statusUpdate': results['status_update'],
        })

    return Response({'success': success, 'message': message})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_repair_records(request, device_id=None):
    """获取维修记录"""
    if device_id:
        records = RepairRecord.objects.filter(device_id=device_id).order_by('-fault_date')[:10]
    else:
        records = RepairRecord.objects.all().order_by('-fault_date')[:50]

    data = [{
        'deviceId': r.device_id,
        'deviceName': r.device_name,
        'location': r.location,
        'model': r.model,
        'department': r.department,
        'teamName': r.team_name,
        'faultDate': r.fault_date.strftime('%Y-%m-%d %H:%M:%S') if r.fault_date else '',
        'reporter': r.reporter,
        'phenomenon': r.phenomenon,
        'analysis': r.analysis,
        'repairDate': r.repair_date.strftime('%Y-%m-%d %H:%M:%S') if r.repair_date else '',
        'repairTeam': r.repair_team,
        'worker': r.worker,
        'result': r.result,
        'materials': r.materials,
        'isResolved': r.is_resolved,
    } for r in records]

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_scheduler_status_api(request):
    """获取定时任务状态"""
    status = get_scheduler_status()
    return Response(status)


@api_view(['POST'])
@permission_classes([AllowAny])
def control_scheduler(request):
    """控制定时任务"""
    action = request.data.get('action')
    if action == 'start':
        start_scheduler()
        return Response({'success': True, 'message': '定时任务已启动'})
    elif action == 'stop':
        stop_scheduler()
        return Response({'success': True, 'message': '定时任务已停止'})
    else:
        return Response({'success': False, 'message': '无效的操作'}, status=400)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from .models import Device, DeviceArea


@api_view(['GET'])
@permission_classes([AllowAny])
def get_devices(request):
    """获取所有设备状态"""
    devices = Device.objects.all()
    data = []
    for device in devices:
        item = {
            'id': device.device_id,
            'name': device.name,
            'area': device.area,
            'type': device.device_type,
            'description': device.description,
            'status': device.status,
            'computedStatus': device.computed_status,
            'x': device.pos_x,
            'y': device.pos_y,
            'width': device.pos_width,
            'height': device.pos_height,
        }
        if device.fault_time:
            item['faultTime'] = int(device.fault_time.timestamp() * 1000)
        if device.capacity:
            item['capacity'] = device.capacity
            item['used'] = device.used or 0
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

    data = {
        'id': device.device_id,
        'name': device.name,
        'area': device.area,
        'type': device.device_type,
        'description': device.description,
        'status': device.status,
        'computedStatus': device.computed_status,
        'x': device.pos_x,
        'y': device.pos_y,
        'width': device.pos_width,
        'height': device.pos_height,
        'updatedAt': device.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }
    if device.fault_time:
        data['faultTime'] = int(device.fault_time.timestamp() * 1000)
        data['faultStartTime'] = device.fault_time.strftime('%Y-%m-%d %H:%M:%S')
    if device.capacity:
        data['capacity'] = device.capacity
        data['used'] = device.used or 0
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

    return Response({
        'id': device.device_id,
        'status': device.status,
        'computedStatus': device.computed_status,
    })


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
        status = device.computed_status
        status_counts[status] = status_counts.get(status, 0) + 1

        item = {
            'id': device.device_id,
            'name': device.name,
            'area': device.area,
            'type': device.device_type,
            'description': device.description,
            'status': device.status,
            'computedStatus': status,
            'x': device.pos_x,
            'y': device.pos_y,
            'width': device.pos_width,
            'height': device.pos_height,
        }
        if device.fault_time:
            item['faultTime'] = int(device.fault_time.timestamp() * 1000)
        if device.capacity:
            item['capacity'] = device.capacity
            item['used'] = device.used or 0
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
        }
    })
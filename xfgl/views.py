import calendar
import datetime

import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib import messages
from django.db.models import Q, Count
from django import forms
from django.forms import ModelForm
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app01.views import LoginForm, logger, check_if_user_is_logged_in
from app01 import models
from .models import Equipment, Operater, Equipment_log

ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]


def create_qr(equipment):
    inspect = equipment.inspect
    url = "http://10.199.102.18:10003/xfgl/sign{}/{}".format(inspect, equipment.id)
    img = qrcode.make(url)
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    device = equipment.get_device_display()
    filename = device + '{}.png'.format(equipment.id)

    # 如果存在同名的文件，先删除旧文件，然后保存新文件
    if default_storage.exists(filename):
        default_storage.delete(filename)

    equipment.qrcode.save(filename, ContentFile(img_io.getvalue()), save=False)


def xfgl_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "xfgl_login.html", {"form": form})
    form = LoginForm(data=request.POST)
    if form.is_valid():
        admin_object = models.Admin.objects.filter(**form.cleaned_data).first()
        if not admin_object:
            form.add_error("password", "账号或密码错误！")
            return render(request, "xfgl_login.html", {"form": form})

        username = admin_object.username
        logger.info(f'{username} 在{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了消防管理。')  # 记录登录信息

        request.session["username"] = admin_object.username
        request.session["info"] = {'id': admin_object.id,
                                   'name': admin_object.username,
                                   'role': admin_object.get_role_display(),
                                   'role_code': admin_object.role,
                                   'banzu': admin_object.banzu,
                                   'chejian': admin_object.chejian,
                                   }
        # 检查用户是否勾选了"保持登录状态"，并设置会话的到期时间
        if "keep_logged_in" in request.POST:
            request.session.set_expiry(60 * 60 * 8)  # 会话将在8小时后过期
        else:
            request.session.set_expiry(None)  # 会话将在浏览器关闭时过期
        return redirect('xfgl:xfgl')
    return render(request, "xfgl_login.html", {"form": form})


def register_xfgl(request):
    from app01.auth_system import unified_logout
    return unified_logout(request, redirect_url='/xfgl/xfgl_login/')


class EquipmentForm(ModelForm):
    class Meta:
        model = Equipment
        fields = ['user', 'banzu', 'device', 'number', 'type', 'inspect', 'production_time', 'check_item1',
                  'check_item2', 'check_item3', 'check_item4', 'check_item5', 'check_item6', 'check_item7',
                  'check_item8', 'check_item9', 'check_item10']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ['check_item1', 'check_item2', 'check_item3', 'check_item4', 'check_item5',
                        'check_item6', 'check_item7', 'check_item8', 'check_item9', 'check_item10']:
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


class OperaterForm(ModelForm):
    class Meta:
        model = Operater
        fields = ['name', 'banzu', 'phone', 'chejian']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ['name', 'phone']:
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def xfgl_index(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/xfgl/xfgl_login/')
    banzu = request.session['info']['banzu']
    role = request.session['info']['role']

    # 只获取属于当前用户所在班组的设备
    if banzu == 13:
        equipments = Equipment.objects.all()
    else:
        equipments = Equipment.objects.filter(banzu=banzu)
    total_equipment = equipments.count()

    type_counts = equipments.values('type').annotate(count=Count('type')).order_by('type')
    type_dict = {type_count['type']: type_count['count'] for type_count in type_counts}
    return render(
        request,
        "xfgl_index.html",
        {
            'equipments': equipments,
            'total_equipment': total_equipment,
            'type1_count': type_dict.get(1, 0),
            'type2_count': type_dict.get(2, 0),
            'type3_count': type_dict.get(3, 0),
            'type4_count': type_dict.get(4, 0),
            'role': role,
            "admin": ADMIN,
            "xiuche": XIUCHE,
            "xiupei": XIUPEI,
        }
    )


# def xfgl(request):
#     logged_in = check_if_user_is_logged_in(request)
#     if not logged_in:
#         return HttpResponseRedirect('/xfgl/login5/')
#     role = request.session['info']['role']
#     context = {
#         'role': role,
#     }
#     return render(request, "xfgl.html", context)
def xfgl(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/xfgl/xfgl_login/')
    banzu = request.session['info']['banzu']
    role = request.session['info']['role']
    # 只获取属于当前用户所在班组的设备
    if banzu == 13:
        equipments = Equipment.objects.all()
    else:
        equipments = Equipment.objects.filter(banzu=banzu)
    form = EquipmentForm
    total_equipment = equipments.count()
    type_counts = Equipment.objects.values('type').annotate(count=Count('type')).order_by('type')
    type_dict = {type_count['type']: type_count['count'] for type_count in type_counts}
    return render(
        request,
        "xfgl.html",
        {
            'form': form,
            'equipments': equipments,
            'total_equipment': total_equipment,
            'type1_count': type_dict.get(1, 0),
            'type2_count': type_dict.get(2, 0),
            'type3_count': type_dict.get(3, 0),
            'type4_count': type_dict.get(4, 0),
            'role': role,
            "admin": ADMIN,
            "xiuche": XIUCHE,
            "xiupei": XIUPEI,
        }
    )


def operater(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/xfgl/xfgl_login/')
    banzu = request.session['info']['banzu']
    role = request.session['info']['role']
    if banzu == 13:
        operater = Operater.objects.all()
    else:
        operater = Operater.objects.filter(banzu=banzu)
    form = OperaterForm
    operater_count = operater.count()
    return render(request, "operater.html",
                  {'form': form, "operater": operater, "operater_count": operater_count, 'banzu': banzu, 'role': role,
                   "admin": ADMIN,
                   "xiuche": XIUCHE,
                   "xiupei": XIUPEI, })


@csrf_exempt
def add_operater(request):
    role = request.session['info']['role']
    if request.method == 'POST':
        form = OperaterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'负责人添加成功！')
            # 如果没有错误发生，重定向到指定的url
            redirect_url = reverse('xfgl:operater')
            return HttpResponseRedirect(redirect_url)
        else:
            return render(request, 'operater.html', {'form': form, 'role': role,
                                                     "admin": ADMIN,
                                                     "xiuche": XIUCHE,
                                                     "xiupei": XIUPEI, })
    else:
        form = OperaterForm()
        return render(request, 'operater.html', {'form': form, 'role': role,
                                                 "admin": ADMIN,
                                                 "xiuche": XIUCHE,
                                                 "xiupei": XIUPEI, })


@csrf_exempt
def edit_operater(request):
    role = request.session['info']['role']
    if request.method == 'POST':
        log_id = request.POST.get('logid')  # 注意参数名称匹配
        log = get_object_or_404(Operater, id=log_id)
        form = OperaterForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            messages.success(request, f'负责人信息修改成功！')
            return JsonResponse({'message': '保存成功!'})
        return JsonResponse({'error': str(form.errors)}, status=400)
    return JsonResponse({'error': '无效请求'}, status=400)


@csrf_exempt
def add_xfgl(request):
    role = request.session['info']['role']
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'新设备添加成功！')
            # 如果没有错误发生，重定向到指定的url
            redirect_url = reverse('xfgl:xfgl')
            return HttpResponseRedirect(redirect_url)
        else:
            # 如果表单无效（例如，因为提供的数据无效），则重新显示表单
            return render(request, 'xfgl.html', {'form': form, 'role': role,
                                                 "admin": ADMIN,
                                                 "xiuche": XIUCHE,
                                                 "xiupei": XIUPEI, })
    else:
        form = EquipmentForm()
        return render(request, 'xfgl.html', {'form': form, 'role': role,
                                             "admin": ADMIN,
                                             "xiuche": XIUCHE,
                                             "xiupei": XIUPEI, })


@csrf_exempt
def edit_xfgl(request):
    if request.method == 'POST':
        log_id = request.POST.get('logid')  # 注意参数名称匹配
        log = get_object_or_404(Equipment, id=log_id)
        form = EquipmentForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            messages.success(request, f'设备信息修改成功！')
            return JsonResponse({'message': '保存成功!'})
        return JsonResponse({'error': str(form.errors)}, status=400)
    return JsonResponse({'error': '无效请求'}, status=400)


def info1(request, id):
    equipment = Equipment.objects.get(id=id)
    # 如果还没有二维码图像，那么就创建一个
    if not equipment.qrcode:
        create_qr(equipment)
        equipment.save()
    user = Operater.objects.get(id=equipment.user.id) if equipment.user else None
    logs = Equipment_log.objects.filter(device=equipment)

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    role = request.session['info']['role']

    if request.method == 'POST':
        current_year = int(request.POST.get('year'))
        current_month = int(request.POST.get('month'))

    days_in_month = calendar.monthrange(current_year, current_month)[1]
    month_log = []

    for day in range(1, days_in_month + 1):
        start_time = datetime.datetime(current_year, current_month, day, 0, 0, 0)
        end_time = datetime.datetime(current_year, current_month, day, 23, 59, 59)

        log = logs.filter(Q(create_time__gte=start_time), Q(create_time__lt=end_time),
                          device=equipment).first()  # 获取这一天的记录

        log_id = log.id if log else None
        month_log.append((day, log_id, log))

    context = {
        'equipment': equipment,
        'user': user,
        'month_log': month_log,
        'month': current_month,
        'year': current_year,
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
    }
    return render(request, "info1.html", context)


def info2(request, id):
    equipment = Equipment.objects.get(id=id)
    # 如果还没有二维码图像，那么就创建一个
    if not equipment.qrcode:
        create_qr(equipment)
        equipment.save()
    user = Operater.objects.get(id=equipment.user.id) if equipment.user else None
    logs = Equipment_log.objects.filter(device=equipment)

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    role = request.session['info']['role']

    if request.method == 'POST':
        current_year = int(request.POST.get('year'))
        current_month = int(request.POST.get('month'))

    month_log = []
    days_in_month = calendar.monthrange(current_year, current_month)[1]

    for day in range(1, days_in_month + 1):
        start_time = datetime.datetime(current_year, current_month, day, 0, 0, 0)
        end_time = datetime.datetime(current_year, current_month, day, 23, 59, 59)

        log = logs.filter(Q(create_time__gte=start_time), Q(create_time__lt=end_time)).first()  # 获取这一天的记录
        log_id = log.id if log else None  # 如果记录存在，保存记录的 id
        month_log.append((day, log, log_id))

    context = {
        'equipment': equipment,
        'user': user,
        'month_log': month_log,
        'month': current_month,
        'year': current_year,
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
    }
    return render(request, "info2.html", context)


def info3(request, id):
    equipment = Equipment.objects.get(id=id)
    # 如果还没有二维码图像，那么就创建一个
    if not equipment.qrcode:
        create_qr(equipment)
        equipment.save()
    user = Operater.objects.get(id=equipment.user.id) if equipment.user else None
    logs = Equipment_log.objects.filter(device=equipment)
    year = datetime.datetime.now().year

    role = request.session['info']['role']

    if request.method == 'POST':
        year = int(request.POST.get('year'))
    months = list(range(1, 13))  # 创建一个包含12个月份的列表
    month_logs = []

    for month in months:
        next_month = month + 1 if month != 12 else 1
        next_year = year if month != 12 else year + 1
        start_time = datetime.datetime(year=year, month=month, day=1)
        end_time = datetime.datetime(year=next_year, month=next_month, day=1)

        log = logs.filter(Q(create_time__gte=start_time), Q(create_time__lt=end_time), device=equipment).first()
        log_id = log.id if log else None

        month_logs.append((month, log, log_id))

    context = {
        'equipment': equipment,
        'user': user,
        'month_logs': month_logs,
        'year': year,
        'months': months,
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
    }
    return render(request, "info3.html", context)


def sign1(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    today = datetime.datetime.now().date()
    start = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)
    # 查询当天的检查记录
    try:
        log_entry = Equipment_log.objects.get(device=equipment, create_time__range=(start, end))
        if log_entry is None:
            raise Equipment_log.DoesNotExist
    except Equipment_log.DoesNotExist:
        log_entry = None

    if request.method == 'POST':
        beizhu = request.POST.get('beizhu', '')

        if not log_entry:  # 没有当天记录，进行开工检查
            operater_id = equipment.user.id

            # 创建新记录并保存开工检查数据
            log_entry = Equipment_log(
                device=equipment,
                name_id=operater_id,
                beizhu=beizhu,
                pic1=request.FILES.get('pic1'),
            )
            log_entry.check_item1 = True
            log_entry.create_time = datetime.datetime.now()
            log_entry.save()

        else:  # 存在当天记录，进行完工检查
            log_entry.check_item1 = True
            log_entry.check_item2 = True
            log_entry.pic2 = request.FILES.get('pic2') or log_entry.pic2
            log_entry.beizhu = beizhu
            log_entry.create_time1 = datetime.datetime.now()
            log_entry.save()

        # 更新设备最后检查时间
        equipment.check_date = datetime.datetime.now()
        equipment.save()
        return redirect('xfgl:check_complete', id=log_entry.id)

    else:  # GET请求处理
        if not log_entry:  # 显示开工检查表单
            return render(request, 'sign1_start.html', {
                'equipment': equipment
            })
        else:
            if not log_entry.check_item2:  # 显示完工检查表单
                return render(request, 'sign1_end.html', {
                    'equipment': equipment,
                    'log_entry': log_entry
                })
            else:  # 重定向到已完成点检页面
                return redirect('xfgl:check_complete', id=log_entry.id)


def sign2(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    today = datetime.datetime.now().date()
    start = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)
    try:
        log_entry = Equipment_log.objects.get(device=equipment, create_time__range=(start, end))
    except Equipment_log.DoesNotExist:
        log_entry = None
    if log_entry is not None:
        return redirect('xfgl:check_complete', id=log_entry.id)

    if request.method == 'POST':
        operater_id = equipment.user.id
        selected_checks = request.POST.getlist('checks')
        pic1 = request.FILES.get('pic1', None)  # 允许在不上传文件的情况下获取文件
        beizhu = request.POST.get('beizhu', '')
        request.session['beizhu'] = beizhu
        # 设置或创建点检日志
        if log_entry:
            log_entry.name_id = operater_id
            log_entry.pic1 = pic1 or log_entry.pic1
        else:
            log_entry = Equipment_log(device=equipment, name_id=operater_id, pic1=pic1)

        for i in range(1, 11):
            setattr(log_entry, f'check_item{i}', str(i) in selected_checks)
        log_entry.create_time = datetime.datetime.now()
        log_entry.create_time1 = datetime.datetime.now()
        log_entry.save()

        # 更新 Equipment 对象的 check_date 字段
        equipment.check_date = datetime.datetime.now()
        equipment.save()

        log_id = log_entry.id
        return redirect('xfgl:check_complete', id=log_id)

    else:  # GET请求处理
        check_items = []
        for i in range(1, 11):
            item_name = getattr(equipment, f'check_item{i}', '')
            if item_name:
                check_items.append({'num': i, 'name': item_name})

        return render(request, 'sign2.html', {
            'equipment': equipment,
            'log_entry': log_entry,
            'check_items': check_items,
        })


def sign3(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    now = datetime.datetime.now()

    log_entry = Equipment_log.objects.filter(device=equipment, create_time__year=now.year,
                                             create_time__month=now.month).last()
    if log_entry is None:
        step = '1'
    elif not log_entry.pic1:
        step = '1'
    elif not log_entry.pic2:
        step = '2'
        request.session['log_entry_id'] = log_entry.id
    else:
        return redirect('xfgl:check_complete', id=log_entry.id)

    if request.method == 'POST':
        if step == '1':
            # 处理第一步提交
            operater_id = equipment.user.id
            selected_checks = request.POST.getlist('checks')
            pic1 = request.FILES.get('pic1', None)  # 允许在不上传文件的情况下获取文件
            beizhu = request.POST.get('beizhu', '')
            request.session['beizhu'] = beizhu
            # 设置或创建点检日志（只填充前5项）
            if log_entry:
                log_entry.name_id = operater_id
                log_entry.pic1 = pic1 or log_entry.pic1
            else:
                log_entry = Equipment_log(device=equipment, name_id=operater_id, pic1=pic1)

            # 设置前5个检查项的状态
            for i in range(1, 6):
                setattr(log_entry, f'check_item{i}', str(i) in selected_checks)
            log_entry.create_time = datetime.datetime.now()
            log_entry.save()
            # 更新 Equipment 对象的 check_date 字段
            equipment.check_date = datetime.datetime.now()
            equipment.save()

            return redirect(f"{reverse('xfgl:sign3', args=[id])}?step=2&log_id={log_entry.id}")

        elif step == '2':
            # 处理第二步提交
            log_entry_id = request.session.get('log_entry_id')
            log_entry = get_object_or_404(Equipment_log, id=log_entry_id)
            selected_checks = request.POST.getlist('checks')
            pic2 = request.FILES.get('pic2', None)  # 允许在不上传文件的情况下获取文件
            beizhu = request.POST.get('beizhu', '')
            full_beizhu = request.session.get('beizhu', '') + beizhu
            log_entry.beizhu = full_beizhu
            # 更新后5个检查项和照片
            for i in range(6, 11):
                setattr(log_entry, f'check_item{i}', str(i) in selected_checks)
            if pic2:
                log_entry.pic2 = pic2
            log_entry.create_time1 = datetime.datetime.now()
            log_entry.save()
            # 更新 Equipment 对象的 check_date 字段
            equipment.check_date = datetime.datetime.now()
            equipment.save()
            return redirect('xfgl:check_complete', id=log_entry_id)  # 跳转到完成页面

    else:  # GET请求处理
        check_items = []
        log_entry_id = request.session.get('log_entry_id')
        if step == '2':  # 第二步：获取后5个检查项
            log_entry = get_object_or_404(Equipment_log, id=log_entry_id)
            beizhu = request.session.get('beizhu', '')
            for i in range(6, 11):
                item_name = getattr(equipment, f'check_item{i}', '')
                if item_name:
                    check_items.append({'num': i, 'name': item_name})
            return render(request, 'sign3_step2.html', {
                'equipment': equipment,
                'check_items': check_items,
                'log_entry': log_entry,
                'beizhu': beizhu,
            })
        else:  # 第一步：获取前5个检查项和相关操作者
            # operaters = Operater.objects.filter(banzu=equipment.banzu)
            for i in range(1, 6):
                item_name = getattr(equipment, f'check_item{i}', '')
                if item_name:
                    check_items.append({'num': i, 'name': item_name})
            return render(request, 'sign3_step1.html', {
                'equipment': equipment,
                'check_items': check_items,
                # 'operaters': operaters
            })


def check_complete(request, id):
    log_entry = get_object_or_404(Equipment_log, id=id)
    log_entry1 = get_object_or_404(Equipment, id=log_entry.device.id)
    return render(request, 'check_complete.html', {'log_entry': log_entry, 'log_entry1': log_entry1})


def check_complete1(request, id):
    role = request.session['info']['role']
    log_entry = get_object_or_404(Equipment_log, id=id)
    log_entry1 = get_object_or_404(Equipment, id=log_entry.device.id)
    return render(request, 'check_complete1.html', {'log_entry': log_entry, 'log_entry1': log_entry1,
                                                    'role': role,
                                                    "admin": ADMIN,
                                                    "xiuche": XIUCHE,
                                                    "xiupei": XIUPEI,
                                                    })


@require_POST
def delete_check(request, id):
    log_entry = get_object_or_404(Equipment_log, id=id)
    inspect = log_entry.device.inspect
    equip_id = log_entry.device.id
    print(equip_id)
    print(inspect)
    log_entry.delete()
    if inspect == 1:
        return redirect('xfgl:sign1', id=equip_id)
    elif inspect == 2:
        return redirect('xfgl:sign2', id=equip_id)
    elif inspect == 3:
        return redirect('xfgl:sign3', id=equip_id)

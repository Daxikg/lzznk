import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from itertools import groupby
from app01.models import Transactions
from app01.views import check_if_user_is_logged_in
from bzrz.models import TeamUser
from .models import Circulates, CirculateAttachment, CirculateReads
from django.utils import timezone


ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]
XIUCHE_BANZU = [1, 4, 5, 8, 9, 10, 16]
XIUPEI_BANZU = [2, 3, 6, 7, 12, 15]


def wjcy(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)

    role = request.session['info']['role']
    admin_id = request.session['info']['id']
    chejian = request.session['info']['chejian']
    banzu = request.session['info']['banzu']  # 获取当前用户的班组信息

    # 获取当前班组在职的所有成员
    current_banzu_users = TeamUser.objects.filter(retire=1)

    # 获取所有传阅记录
    if banzu == 13:
        if chejian == 0:
            circulates = Circulates.objects.filter(status=0).distinct().order_by('-create_time')
        else:
            circulates = Circulates.objects.filter(chejian=chejian, status=0).distinct().order_by('-create_time')
    else:
        current_banzu_users = TeamUser.objects.filter(banzu=banzu, retire=1)
        circulates = Circulates.objects.filter(status=0,
                                               circulatereads__user__in=current_banzu_users).distinct().order_by(
            '-create_time')

    # 添加未读人数统计到每个传阅对象
    for circulate in circulates:
        total_reads = CirculateReads.objects.filter(
            circulate=circulate,
            user__in=current_banzu_users
        ).count()
        unread_count = CirculateReads.objects.filter(
            circulate=circulate,
            read=False,
            user__in=current_banzu_users
        ).count()
        circulate.total_reads = total_reads
        circulate.unread_count = unread_count

    context = {
        'role': role,
        'admin_id': admin_id,
        'chejian': chejian,
        'banzu': banzu,
        'circulates': circulates,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'xiuche_banzu': XIUCHE_BANZU,
        'xiupei_banzu': XIUPEI_BANZU,
        'banzu_choices': TeamUser.banzu_choices,
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    }
    return render(request, "wjcy_index.html", context)


def add_circulate(request):
    if request.method == 'POST':
        classification = request.POST.get('classification')
        title = request.POST.get('title')
        print(title)
        name = request.POST.get('name')
        print(name)
        key_remindertitle = request.POST.get('key_remindertitle')
        create_time = request.POST.get('create_time')
        selected_users = request.POST.getlist('selected_users[]')
        chejian = request.session['info']['chejian']

        if not create_time:
            create_time = timezone.now()

        try:
            with transaction.atomic():
                # 创建传阅记录
                circulate = Circulates.objects.create(
                    classification=classification,
                    title=title,
                    name=name,
                    key_remindertitle=key_remindertitle,
                    chejian=int(chejian),
                    create_time=create_time
                )

                # 处理文件上传
                if request.FILES.getlist('files'):
                    for file in request.FILES.getlist('files'):
                        # 使用原始文件名存储
                        CirculateAttachment.objects.create(
                            circulate=circulate,
                            file=file
                        )

                # 处理用户
                unique_users = set(selected_users)
                circulate_reads = []
                for user_id in unique_users:
                    try:
                        user = TeamUser.objects.get(id=user_id)
                        circulate_reads.append(CirculateReads(
                            circulate=circulate,
                            user=user,
                            read=0
                        ))
                    except TeamUser.DoesNotExist:
                        print(f"User with id {user_id} not found")

                CirculateReads.objects.bulk_create(circulate_reads)

            return JsonResponse({'status': 'success', 'message': '文件传阅发布成功！'})
        except Exception as e:
            print(f"Error creating circulate: {str(e)}")
            return JsonResponse({'status': 'error', 'message': '发布失败，请重试！'})

    return JsonResponse({'status': 'error', 'message': '无效的请求！'})


def get_team_users(request):
    banzu = request.GET.get('banzu')
    search = request.GET.get('search')
    role = request.session['info']['role']

    # 根据角色确定班组列表
    if role == "修配管理员":
        banzu_list = XIUPEI_BANZU
    elif role == "修车管理员":
        banzu_list = XIUCHE_BANZU
    else:
        banzu_list = []

    # 获取所有班组的显示名称
    banzu_names = dict(TeamUser.banzu_choices)
    users = TeamUser.objects.filter(banzu__in=banzu_list, retire=1)

    if banzu:
        users = users.filter(banzu=int(banzu))
    if search:
        users = users.filter(name__icontains=search)

    user_list = [{
        'id': user.id,
        'name': user.name,
        'banzu': banzu_names.get(user.banzu, '未知班组')
    } for user in users]

    return JsonResponse({'users': user_list})


def get_user_info(request, user_id):
    user = TeamUser.objects.get(id=user_id, retire=1)
    return JsonResponse({
        'id': user.id,
        'name': user.name,
        'banzu': user.get_banzu_display()
    })


@csrf_exempt
def end_circulate(request, circulate_id):
    if request.method == 'POST':
        try:
            circulate = get_object_or_404(Circulates, id=circulate_id)
            circulate.status = 1
            circulate.save()
            return JsonResponse({'status': 'success', 'message': '传阅已结束！'})
        except Exception as e:
            print(f"Error ending circulate: {str(e)}")
            return JsonResponse({'status': 'error', 'message': '结束传阅失败，请重试！'})
    return JsonResponse({'status': 'error', 'message': '无效的请求！'})


@csrf_exempt
def wjcy_delete(request, circulate_id):
    if request.method == 'POST':
        try:
            circulate = get_object_or_404(Circulates, id=circulate_id)
            # 删除相关附件
            for attachment in circulate.attachments.all():
                attachment.file.delete()
                attachment.delete()
            # 删除传阅记录
            circulate.delete()
            return JsonResponse({'status': 'success', 'message': '传阅已删除！'})
        except Exception as e:
            print(f"Error deleting circulate: {str(e)}")
            return JsonResponse({'status': 'error', 'message': '删除传阅失败，请重试！'})
    return JsonResponse({'status': 'error', 'message': '无效的请求！'})


def history(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"login1/?next={request.path}"
        return redirect(login_url)

    role = request.session['info']['role']
    admin_id = request.session['info']['id']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    # 获取当前班组的所有成员
    current_banzu_users = TeamUser.objects.filter(retire=1)

    # 获取所有传阅记录
    if banzu == 13:
        if chejian == 0:
            circulates = Circulates.objects.filter(status=1).distinct().order_by('-create_time')
        else:
            circulates = Circulates.objects.filter(chejian=chejian, status=1).distinct().order_by('-create_time')
    else:
        current_banzu_users = TeamUser.objects.filter(banzu=banzu, retire=1)
        circulates = Circulates.objects.filter(status=1,
                                               circulatereads__user__in=current_banzu_users).distinct().order_by(
            '-create_time')

    # 添加未读人数统计到每个传阅对象
    for circulate in circulates:
        total_reads = CirculateReads.objects.filter(
            circulate=circulate,
            user__in=current_banzu_users
        ).count()
        unread_count = CirculateReads.objects.filter(
            circulate=circulate,
            read=False,
            user__in=current_banzu_users
        ).count()
        circulate.total_reads = total_reads
        circulate.unread_count = unread_count

    context = {
        'role': role,
        'admin_id': admin_id,
        'chejian': chejian,
        'circulates': circulates,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'xiuche_banzu': XIUCHE_BANZU,
        'xiupei_banzu': XIUPEI_BANZU,
        'banzu_choices': TeamUser.banzu_choices,
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
    }
    return render(request, "wjcy_history.html", context)


def circulate_detail(request, circulate_id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)

    role = request.session['info']['role']
    admin_id = request.session['info']['id']
    chejian = request.session['info']['chejian']
    banzu = request.session['info']['banzu']

    circulate = get_object_or_404(Circulates, id=circulate_id)
    attachments = circulate.attachments.all()

    # 获取所有事务数据用于导航栏
    all_transactions = Transactions.objects.filter(chejian=chejian).order_by('-todaytime')
    all_circulates = Circulates.objects.all().distinct().order_by('-create_time')
    if chejian != 0:
        all_circulates = all_circulates.filter(chejian=chejian)

    # 获取当前年月
    current_year = circulate.create_time.year
    current_month = circulate.create_time.month

    # 组合所有数据用于导航栏
    all_combined_data = []
    for trans in all_transactions:
        all_combined_data.append({
            'type': 'transaction',
            'data': trans,
            'time': trans.todaytime,
        })
    for circ in all_circulates:
        all_combined_data.append({
            'type': 'circulate',
            'data': circ,
            'time': circ.create_time,
        })
    all_combined_data.sort(key=lambda x: x['time'], reverse=True)

    # 按年月分组用于导航栏
    combined_years = []
    for year, year_items in groupby(all_combined_data, key=lambda x: x['time'].year):
        year_items = list(year_items)
        months = []
        for month, month_items in groupby(year_items, key=lambda x: x['time'].month):
            months.append({
                'month': month,
                'items': list(month_items)
            })
        combined_years.append({
            'year': year,
            'months': months
        })

    # 处理传阅的阅读状态
    if banzu == 13:
        reads = circulate.circulatereads_set.all()
    else:
        reads = circulate.circulatereads_set.filter(user__banzu=banzu)

    # 按班组分类用户
    users_by_banzu = {}
    for read in reads:
        banzu = read.user.get_banzu_display()
        if banzu not in users_by_banzu:
            users_by_banzu[banzu] = []
        users_by_banzu[banzu].append({
            'id': read.user.id,
            'name': read.user.name,
            'read': read.read,
            'photo': read.photo,
            'beizhu': read.beizhu,
            'photo_at': read.photo_at,
        })

    context = {
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'admin_id': admin_id,
        'chejian': chejian,
        'circulate': circulate,
        'attachments': attachments,
        'users_by_banzu': users_by_banzu,
        'banzu_choices': TeamUser.banzu_choices,
        'year': current_year,
        'month': current_month,
        'combined_years': combined_years  # 添加导航栏数据
    }
    return render(request, "wjcy_detail.html", context)


@csrf_exempt
def mark_as_read(request):
    if request.method == 'POST':
        circulate_id = request.POST.get('circulate_id')
        user_id = request.POST.get('user_id')

        try:
            circulate_read = CirculateReads.objects.get(
                circulate_id=circulate_id,
                user_id=user_id
            )

            # 设置为已读
            circulate_read.read = True
            circulate_read.save()

            return JsonResponse({'status': 'success', 'message': '标记为已读成功'})

        except CirculateReads.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '找不到对应的传阅记录'})

    return JsonResponse({'status': 'error', 'message': '无效的请求'})


@csrf_exempt
def upload_photo(request):
    if request.method == 'POST':
        circulate_id = request.POST.get('circulate_id')
        user_id = request.POST.get('user_id')

        try:
            circulate_read = CirculateReads.objects.get(
                circulate_id=circulate_id,
                user_id=user_id
            )

            if 'photo' in request.FILES:
                circulate_read.photo = request.FILES['photo']
                circulate_read.read = True
                circulate_read.photo_at = timezone.now()
                circulate_read.save()

                return JsonResponse({'status': 'success', 'message': '照片上传成功！'})
            else:
                return JsonResponse({'status': 'error', 'message': '没有上传照片！'})

        except CirculateReads.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '找不到对应的传阅记录！'})

    return JsonResponse({'status': 'error', 'message': '无效的请求！'})


@csrf_exempt
def save_beizhu(request):
    if request.method == 'POST':
        try:
            circulate_id = request.POST.get('circulate_id')
            user_id = request.POST.get('user_id')
            beizhu = request.POST.get('beizhu')

            circulate_read = CirculateReads.objects.get(circulate_id=circulate_id, user_id=user_id)
            circulate_read.beizhu = beizhu
            circulate_read.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': '无效的请求'})


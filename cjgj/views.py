from datetime import datetime

import datetime
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from app01.views import LoginForm, logger, check_if_user_is_logged_in
from app01 import models
from bzrz.models import TeamUser
from django.db.models import Count, Q
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login
import os


def cjgj_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "cjgj_login.html", {"form": form})
    form = LoginForm(data=request.POST)
    if form.is_valid():
        # 使用Django内置认证系统
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        
        if user is not None:
            # 登录用户
            auth_login(request, user)
            
            # 获取对应的Admin对象用于session信息
            try:
                admin_object = models.Admin.objects.get(username=user.username)
                username = admin_object.username
                logger.info(f'{username} 在{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了车间构建。')
                
                request.session["username"] = admin_object.username
                request.session["info"] = {
                    'id': admin_object.id,
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
                return redirect('cjgj:cjgj')
            except models.Admin.DoesNotExist:
                form.add_error("password", "用户信息不存在！")
                return render(request, "cjgj_login.html", {"form": form})
        else:
            form.add_error("password", "账号或密码错误！")
            return render(request, "cjgj_login.html", {"form": form})
    return render(request, "cjgj_login.html", {"form": form})


def cjgj_register(request):
    from app01.auth_system import unified_logout
    return unified_logout(request, redirect_url='/cjgj/cjgj_login/')


ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班",  "修车管理员"]


def calculate_workshop_stats():
    # 修车车间班组
    xiu_che_banzu = [1, 4, 5, 8, 9, 10, 16, 18]
    # 修配车间班组
    xiu_pei_banzu = [2, 3, 6, 7, 12, 15, 17]

    # 获取修车车间的数据
    xiu_che_users = TeamUser.objects.filter(banzu__in=xiu_che_banzu, retire=1)
    # 获取修配车间的数据
    xiu_pei_users = TeamUser.objects.filter(banzu__in=xiu_pei_banzu, retire=1)

    # 计算总人数
    xiu_che_total = xiu_che_users.count()
    xiu_pei_total = xiu_pei_users.count()

    # 计算性别分布
    xiu_che_gender = xiu_che_users.aggregate(
        male=Count('id', filter=Q(gender=1)),
        female=Count('id', filter=Q(gender=2))
    )

    # 计算性别百分比
    xiu_che_gender_pct = {
        'male_pct': round((xiu_che_gender['male'] / xiu_che_total * 100), 1) if xiu_che_total > 0 else 0,
        'female_pct': round((xiu_che_gender['female'] / xiu_che_total * 100), 1) if xiu_che_total > 0 else 0
    }

    xiu_pei_gender = xiu_pei_users.aggregate(
        male=Count('id', filter=Q(gender=1)),
        female=Count('id', filter=Q(gender=2))
    )

    # 计算性别百分比
    xiu_pei_gender_pct = {
        'male_pct': round((xiu_pei_gender['male'] / xiu_pei_total * 100), 1) if xiu_pei_total > 0 else 0,
        'female_pct': round((xiu_pei_gender['female'] / xiu_pei_total * 100), 1) if xiu_pei_total > 0 else 0
    }

    # 计算政治面貌
    xiu_che_mianmao = xiu_che_users.aggregate(
        dangyuan=Count('id', filter=Q(mianmao=3)),
        tuanyuan=Count('id', filter=Q(mianmao=1))
    )

    xiu_pei_mianmao = xiu_pei_users.aggregate(
        dangyuan=Count('id', filter=Q(mianmao=3)),
        tuanyuan=Count('id', filter=Q(mianmao=1))
    )

    # 计算技能等级
    xiu_che_dengji = xiu_che_users.aggregate(
        chujigong=Count('id', filter=Q(dengji=1)),
        zhongjigong=Count('id', filter=Q(dengji=2)),
        gaojigong=Count('id', filter=Q(dengji=3)),
        jishi=Count('id', filter=Q(dengji=4)),
        gaojishi=Count('id', filter=Q(dengji=5))
    )

    xiu_pei_dengji = xiu_pei_users.aggregate(
        chujigong=Count('id', filter=Q(dengji=1)),
        zhongjigong=Count('id', filter=Q(dengji=2)),
        gaojigong=Count('id', filter=Q(dengji=3)),
        jishi=Count('id', filter=Q(dengji=4)),
        gaojishi=Count('id', filter=Q(dengji=5))
    )

    # 计算学历分布
    xiu_che_wenhua = xiu_che_users.aggregate(
        chuzhong=Count('id', filter=Q(wenhua=1)),
        gaozhong=Count('id', filter=Q(wenhua=2)),
        zhongzhuan=Count('id', filter=Q(wenhua=3)),
        zhongji=Count('id', filter=Q(wenhua=4)),
        zhuanyekao=Count('id', filter=Q(wenhua=5)),
        benke=Count('id', filter=Q(wenhua=6)),
        yanjiusheng=Count('id', filter=Q(wenhua=7))
    )

    xiu_pei_wenhua = xiu_pei_users.aggregate(
        chuzhong=Count('id', filter=Q(wenhua=1)),
        gaozhong=Count('id', filter=Q(wenhua=2)),
        zhongzhuan=Count('id', filter=Q(wenhua=3)),
        zhongji=Count('id', filter=Q(wenhua=4)),
        zhuanyekao=Count('id', filter=Q(wenhua=5)),
        benke=Count('id', filter=Q(wenhua=6)),
        yanjiusheng=Count('id', filter=Q(wenhua=7))
    )

    return {
        'xiu_che': {
            'total': xiu_che_total,
            'gender': xiu_che_gender,
            'gender_pct': xiu_che_gender_pct,
            'mianmao': xiu_che_mianmao,
            'dengji': xiu_che_dengji,
            'wenhua': xiu_che_wenhua
        },
        'xiu_pei': {
            'total': xiu_pei_total,
            'gender': xiu_pei_gender,
            'gender_pct': xiu_pei_gender_pct,
            'mianmao': xiu_pei_mianmao,
            'dengji': xiu_pei_dengji,
            'wenhua': xiu_pei_wenhua
        }
    }


def zzgljg(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/cjgj/cjgj_login/')

    role = request.session['info']['role']
    contxt = {"role": role, "admin": ADMIN, "xiuche": XIUCHE, "xiupei": XIUPEI}

    # 添加统计信息到上下文
    stats = calculate_workshop_stats()
    contxt.update(stats)

    if role in ADMIN:
        return render(request, "zzgljg.html", contxt)
    elif role in XIUPEI:
        return render(request, "xpzzgljg.html", contxt)
    else:
        return render(request, "xczzgljg.html", contxt)


def cjgj(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/cjgj/cjgj_login/')

    role = request.session['info']['role']
    contxt = {"role": role, "admin": ADMIN, "xiuche": XIUCHE, "xiupei": XIUPEI}
    if role in ADMIN:
        return render(request, "cjgj.html", contxt)
    elif role in XIUPEI:
        return render(request, "xpcjgj.html", contxt)
    else:
        return render(request, "xccjgj.html", contxt)


def cjglzd(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/cjgj/cjgj_login/')

    role = request.session['info']['role']
    contxt = {"role": role, "admin": ADMIN, "xiuche": XIUCHE, "xiupei": XIUPEI}
    if role in ADMIN:
        return render(request, "cjglzd.html", contxt)
    elif role in XIUPEI:
        return render(request, "cjglzd.html", contxt)
    else:
        return render(request, "cjglzd.html", contxt)


def upload_rule(request):
    role = request.session.get('info', {}).get('role')
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf = request.FILES['pdf_file']
        if not pdf.name.lower().endswith('.pdf'):
            return JsonResponse({'message': '只能上传 PDF 文件。'}, status=400)
        if role == "修配管理员":
            target_filename = '修配车间管理细则.pdf'
        elif role == '修车管理员':
            target_filename = '修车车间管理细则.pdf'
        else:
            return JsonResponse({'message': '无权限上传文件。'}, status=403)

        parent_dir = os.path.dirname(settings.BASE_DIR)
        pdf_folder = os.path.join(parent_dir, 'app01', 'static', 'text')
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
        pdf_path = os.path.join(pdf_folder, target_filename)
        print(pdf_path)
        with open(pdf_path, 'wb') as f:
            for chunk in pdf.chunks():
                f.write(chunk)
        return JsonResponse({'message': '上传成功，文件已更新。'})
    return JsonResponse({'message': '没有接收到文件。'}, status=400)


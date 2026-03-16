import hashlib
import json
import shutil
import logging
import os
import re
from datetime import datetime, timedelta
import difflib

from django.utils import timezone
from pypinyin import lazy_pinyin

from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.http import FileResponse, Http404
from django.db.models import Q
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm, modelformset_factory
from django.forms import formset_factory
from django.http import HttpResponseForbidden
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, resolve
from django.views.decorators.csrf import csrf_exempt
from itertools import groupby
from operator import attrgetter

from app01 import models
from bzrz.models import TeamUser
from jkrq.models import JkrqList, JkrqList1Log
from wjcy.models import Circulates, CirculateReads
from .models import initial, bogie, order, Admin, tasks, Transactions, TransactionReads, TransactionAttachment
from .forms import PasswordChangeForm
from .decorators import allowed_users

from rest_framework import serializers
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from django import template
import requests
from datetime import date

ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]
XIUCHE_BANZU = [1, 4, 5, 8, 9, 10, 16]
XIUPEI_BANZU = [2, 3, 6, 7, 12, 15]

today = date.today()
logger = logging.getLogger(__name__)
register = template.Library()


@register.filter
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""

    return getattr(value, arg)


class InitialSerializer(serializers.ModelSerializer):
    taiwei = serializers.CharField(source='get_taiwei_display')
    shunxu = serializers.CharField(source='get_shunxu_display')
    xiucheng = serializers.CharField(source='get_xiucheng_display')
    chexing = serializers.CharField(source='get_chexing_display')
    todaytime = serializers.DateTimeField()

    class Meta:
        model = initial
        fields = ['taiwei', 'shunxu', 'xiucheng', 'chexing', 'todaytime']


class InitialView(APIView):
    def get(self, request, *args, **kwargs):
        today = datetime.today().date().isoformat()
        instances = initial.objects.filter(todaytime=today)

        if not instances:
            return Response({"error": "今日暂无数据."}, status=status.HTTP_404_NOT_FOUND)

        serializer = InitialSerializer(instances, many=True)
        return Response(serializer.data, status=200)


def get_and_save_data(request):
    try:
        response = requests.get('http://127.0.0.1:10002/yxxxgx/api/yxxx_screen')
        data = response.json()
        task = tasks.objects.get(id=1)
    except Exception as e:
        messages.error(request, f'远程服务未启动，未获取到数据。')
        return HttpResponseRedirect('/1/')

    if "t_list" in data:
        t_list = data["t_list"]
        for task_data in t_list:
            # if 'name' in task_data and task_data['name'] == '敞车门锁改造':
            #     task.changche1 = task_data["plan"]
            #     task.changche2 = task_data["finish"]
            if 'name' in task_data and task_data['name'] == '复合地板':
                task.diban1 = task_data["finish"]
            if 'name' in task_data and task_data['name'] == 'K2改造':
                task.TgaiK = task_data["finish"]
            if 'name' in task_data and task_data['name'] == '木地板专项修':
                task.zhengzhi = task_data["finish"]
    if "c_plan" in data:
        c_plan = data["c_plan"]
        task.duanxiu1 = c_plan.get("gtdx")
        task.duanxiu3 = c_plan.get("jgnc")
        task.duanxiu5 = c_plan.get("zbdx")
        task.changxiu1 = c_plan.get("gtcx")
        task.changxiu3 = c_plan.get("zbcx")
        task.linxiu = c_plan.get("lxc")

    if "cc_plan" in data:
        cc_plan = data["cc_plan"]
        task.duanxiu2 = cc_plan.get("gtdx")
        task.duanxiu4 = cc_plan.get("jgnc")
        task.duanxiu6 = cc_plan.get("zbdx")
        task.changxiu2 = cc_plan.get("gtcx")
        task.changxiu4 = cc_plan.get("zbcx")
        task.linxiu1 = cc_plan.get("lxc")

    if "y_data" in data:
        y_data = data["y_data"]
        task.guotie6 = y_data.get("qnzbdxwc")
        task.guotie3 = y_data.get("qnzbcxwc")
        task.changche2 = y_data.get("qnccmsgzwc")
        task.guotie2 = y_data.get("qncxwc") - y_data.get("qnzbcxwc")
        task.guotie5 = y_data.get("qndxwc") - y_data.get("qnzbdxwc")
        task.pengche4 = y_data.get("qnpcmsgzwc")
        task.pengche2 = y_data.get("qnpcccgzwc")
        task.diban2 = y_data.get("qnfhdbwc")

    task.heji1 = task.duanxiu1 + task.duanxiu3 + task.duanxiu5 + task.changxiu1 + task.changxiu3
    task.heji2 = task.duanxiu2 + task.duanxiu4 + task.duanxiu6 + task.changxiu2 + task.changxiu4
    task.save()
    return HttpResponseRedirect('/1/')


def create_data(request):
    if request.method == 'POST':  # 确保只在 POST 请求时处理
        # 检查是否今天已经创建过表格
        today_min = datetime.combine(datetime.today(), datetime.min.time())
        today_max = datetime.combine(datetime.today(), datetime.max.time())

        # 获取今天所有的 initial 对象
        todays_data = initial.objects.filter(todaytime__range=(today_min, today_max))

        if todays_data.count() == 54:  # 检查今日数据是否全部存在
            messages.error(request, '表格已存在')
            return HttpResponseRedirect('/架车班信息采集界面1/')  # 重定向到指定页面

        try:
            taiwei_choices = range(1, 28)
            shunxu_choices = [1, 2]

            for taiwei in taiwei_choices:
                for shunxu in shunxu_choices:
                    obj = initial(todaytime=datetime.now().strftime("%Y-%m-%d"), taiwei=taiwei, shunxu=shunxu)

                    # 检查这条数据是否已经存在
                    already_exists = todays_data.filter(taiwei=taiwei, shunxu=shunxu).exists()

                    if not already_exists:
                        obj.save()

            messages.success(request, '创建成功')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

        return HttpResponseRedirect('/架车班信息采集界面1/')  # 在完成后重定向到前端页面

    else:
        return HttpResponseRedirect('/error-url')  # 如果请求不是 POST，重定向到错误页面


def create_data1(request):
    if request.method == 'POST':  # 确保只在 POST 请求时处理
        # 检查是否今天已经创建过表格
        today_min = datetime.combine(datetime.today(), datetime.min.time())
        today_max = datetime.combine(datetime.today(), datetime.max.time())

        # 获取今天所有的 initial 对象
        todays_data = initial.objects.filter(todaytime__range=(today_min, today_max))

        if todays_data.count() == 54:  # 检查今日数据是否全部存在
            messages.error(request, '表格已存在')
            return HttpResponseRedirect('/架车班信息手持机查看界面1/')  # 重定向到指定页面

        try:
            taiwei_choices = range(1, 28)
            shunxu_choices = [1, 2]

            for taiwei in taiwei_choices:
                for shunxu in shunxu_choices:
                    obj = initial(todaytime=datetime.now().strftime("%Y-%m-%d"), taiwei=taiwei, shunxu=shunxu)

                    # 检查这条数据是否已经存在
                    already_exists = todays_data.filter(taiwei=taiwei, shunxu=shunxu).exists()

                    if not already_exists:
                        obj.save()

            messages.success(request, '创建成功')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

        return HttpResponseRedirect('/架车班信息手持机查看界面1/')  # 在完成后重定向到前端页面

    else:
        return HttpResponseRedirect('/架车班信息手持机查看界面1/')  # 如果请求不是 POST，重定向到错误页面


def create_data2(request):
    if request.method == 'POST':  # 确保只在 POST 请求时处理
        # 检查是否今天已经创建过表格
        today_min = datetime.combine(datetime.today(), datetime.min.time())
        today_max = datetime.combine(datetime.today(), datetime.max.time())

        # 获取今天所有的 initial 对象
        todays_data = initial.objects.filter(todaytime__range=(today_min, today_max))

        if todays_data.count() == 54:  # 检查今日数据是否全部存在
            messages.error(request, '表格已存在')
            return HttpResponseRedirect('/轮轴班信息采集界面1/')  # 重定向到指定页面

        try:
            taiwei_choices = range(1, 28)
            shunxu_choices = [1, 2]

            for taiwei in taiwei_choices:
                for shunxu in shunxu_choices:
                    obj = initial(todaytime=datetime.now().strftime("%Y-%m-%d"), taiwei=taiwei, shunxu=shunxu)

                    # 检查这条数据是否已经存在
                    already_exists = todays_data.filter(taiwei=taiwei, shunxu=shunxu).exists()

                    if not already_exists:
                        obj.save()

            messages.success(request, '创建成功')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

        return HttpResponseRedirect('/轮轴班信息采集界面1/')  # 在完成后重定向到前端页面

    else:
        return HttpResponseRedirect('/轮轴班信息采集界面1/')  # 如果请求不是 POST，重定向到错误页面


def create_data3(request):
    if request.method == 'POST':  # 确保只在 POST 请求时处理
        # 检查是否今天已经创建过表格
        today_min = datetime.combine(datetime.today(), datetime.min.time())
        today_max = datetime.combine(datetime.today(), datetime.max.time())

        # 获取今天所有的 initial 对象
        todays_data = initial.objects.filter(todaytime__range=(today_min, today_max))

        if todays_data.count() == 54:  # 检查今日数据是否全部存在
            messages.error(request, '表格已存在')
            return HttpResponseRedirect('/台车班顺序编辑1/')  # 重定向到指定页面

        try:
            taiwei_choices = range(1, 28)
            shunxu_choices = [1, 2]

            for taiwei in taiwei_choices:
                for shunxu in shunxu_choices:
                    obj = initial(todaytime=datetime.now().strftime("%Y-%m-%d"), taiwei=taiwei, shunxu=shunxu)

                    # 检查这条数据是否已经存在
                    already_exists = todays_data.filter(taiwei=taiwei, shunxu=shunxu).exists()

                    if not already_exists:
                        obj.save()

            messages.success(request, '创建成功')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')

        return HttpResponseRedirect('/台车班顺序编辑1/')  # 在完成后重定向到前端页面

    else:
        return HttpResponseRedirect('/台车班顺序编辑1/')  # 如果请求不是 POST，重定向到错误页面


def view_log(request):
    with open('django_debug.log', 'r') as f:
        log_content = f.read()

    return render(request, 'view_log.html', {'log_content': log_content})


def md5(data_string):
    obj = hashlib.md5(settings.SECRET_KEY.encode("utf-8"))
    obj.update(data_string.encode("utf-8"))
    return obj.hexdigest()


class LoginForm(forms.Form):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg border-left-0"}),
        required=True
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg border-left-0"}),
        required=True
    )


def login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "login.html", {"form": form})
    
    form = LoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        
        # 使用Django内置认证
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 登录用户
            auth_login(request, user)
            
            logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了平台。')
            
            # 设置session信息（为了兼容旧的检查逻辑）
            try:
                admin_user = Admin.objects.get(username=username)
                request.session["username"] = admin_user.username
                request.session["info"] = {
                    'id': admin_user.id,
                    'name': admin_user.username,
                    'role': admin_user.get_role_display(),
                    'role_code': admin_user.role,
                    'banzu': admin_user.banzu,
                    'chejian': admin_user.chejian,
                }
                
                # 检查用户是否勾选了"保持登录状态"
                if "keep_logged_in" in request.POST:
                    request.session.set_expiry(60 * 60 * 8)  # 8小时
                else:
                    request.session.set_expiry(0)  # 浏览器关闭时过期
                
                # 根据用户角色重定向
                role_redirect_map = {
                    'role1': "/index/",      # 总管理员
                    'role19': "/index/",     # 修配管理员
                    'role20': "/index/",     # 修车管理员
                    'role2': "/架车班信息采集界面1/",   # 架车班
                    'role3': "/轮轴班信息采集界面1/",   # 轮轴班
                    'role4': "/台车班顺序编辑1/",     # 台车班
                    'role5': "/架车班信息手持机查看界面1/", # 架车班手持机
                    'role6': "/index7/",     # 轮轴班手持机
                    'role7': "/1/",          # 调度员
                    'role8': "/1/",          # 安全员
                    'role9': "/1/",          # 技术员
                    'role10': "/1/",         # 内制动班
                    'role11': "/1/",         # 外制动班
                    'role12': "/1/",         # 车钩班
                    'role13': "/1/",         # 探伤班
                    'role14': "/1/",         # 调车组
                    'role15': "/1/",         # 车体班
                    'role16': "/1/",         # 预修班
                    'role18': "/1/",         # 信息班
                }
                
                redirect_url = role_redirect_map.get(admin_user.role, "/1/")
                return HttpResponseRedirect(redirect_url)
                
            except Admin.DoesNotExist:
                return HttpResponseRedirect("/1/")
        else:
            # 认证失败
            form.add_error(None, "账号或密码错误！")
            return render(request, "login.html", {"form": form})
    
    return render(request, "login.html", {"form": form})


def login1(request):
    if request.method == "GET":
        # 获取next参数值
        next_url = request.GET.get('next', '/1/')
        form = LoginForm()
        return render(request, "login1.html", {"form": form, 'next': next_url})

    form = LoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        
        # 使用Django内置认证
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 登录用户
            auth_login(request, user)
            
            logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了综合平台。')
            
            # 设置session信息（为了兼容旧的检查逻辑）
            try:
                admin_user = Admin.objects.get(username=username)
                request.session["username"] = admin_user.username
                request.session["info"] = {
                    'id': admin_user.id,
                    'name': admin_user.username,
                    'role': admin_user.get_role_display(),
                    'role_code': admin_user.role,
                    'banzu': admin_user.banzu,
                    'chejian': admin_user.chejian,
                }
            except Admin.DoesNotExist:
                pass
            
            # 检查用户是否勾选了"保持登录状态"
            if "keep_logged_in" in request.POST:
                request.session.set_expiry(60 * 60 * 8)  # 8小时
            else:
                request.session.set_expiry(0)  # 浏览器关闭时过期
            
            # 根据用户角色重定向
            try:
                admin_user = Admin.objects.get(username=username)
                role = admin_user.role
                
                role_redirect_map = {
                    'role1': "/index/",      # 总管理员
                    'role19': "/index/",     # 修配管理员
                    'role20': "/index/",     # 修车管理员
                    'role2': "/架车班信息采集界面1/",   # 架车班
                    'role3': "/轮轴班信息采集界面1/",   # 轮轴班
                    'role4': "/台车班顺序编辑1/",     # 台车班
                    'role5': "/架车班信息手持机查看界面1/", # 架车班手持机
                    'role6': "/index7/",     # 轮轴班手持机
                    'role7': "/1/",          # 调度员
                    'role8': "/1/",          # 安全员
                    'role9': "/1/",          # 技术员
                    'role10': "/1/",         # 内制动班
                    'role11': "/1/",         # 外制动班
                    'role12': "/1/",         # 车钩班
                    'role13': "/1/",         # 探伤班
                    'role14': "/1/",         # 调车组
                    'role15': "/1/",         # 车体班
                    'role16': "/1/",         # 预修班
                    'role18': "/1/",         # 信息班
                }
                
                # 获取next参数并重定向
                next_url = request.POST.get('next', role_redirect_map.get(role, '/1/'))
                return HttpResponseRedirect(next_url)
                
            except Admin.DoesNotExist:
                next_url = request.POST.get('next', '/1/')
                return HttpResponseRedirect(next_url)
        else:
            # 认证失败
            form.add_error(None, "账号或密码错误！")
            next_url = request.GET.get('next', '/1/')
            return render(request, "login1.html", {"form": form, 'next': next_url})
    
    next_url = request.GET.get('next', '/1/')
    return render(request, "login1.html", {"form": form, 'next': next_url})


def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            current_password = form.cleaned_data["current_password"]
            new_password = form.cleaned_data["new_password"]

            try:
                user = Admin.objects.get(username=username)
                # 验证当前密码
                if md5(current_password) != user.password:
                    messages.error(request, "用户名或当前密码错误！")
                    return render(request, "change_password.html", {"form": form})

                # 更新密码
                user.password = md5(new_password)
                user.save()

                # 记录密码修改日志
                logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}修改密码为{new_password}。')

                messages.success(request, "密码修改成功！请重新登录。")
                return render(request, "change_password.html", {"form": form})
            except Admin.DoesNotExist:
                messages.error(request, "用户名不存在！")
                return render(request, "change_password.html", {"form": form})
    else:
        form = PasswordChangeForm()

    return render(request, "change_password.html", {"form": form})


def register(request):
    auth_logout(request)
    return redirect('/login/')


def register1(request):
    auth_logout(request)
    return redirect('/1/')


def allowed_users(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            username = request.session.get('username')
            if username is None:
                return redirect('login')  # Redirect to login page if user is not logged in

            try:
                user = Admin.objects.get(username=username)
                if user.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseForbidden()
            except Admin.DoesNotExist:
                return redirect('login')  # Redirect to login if user does not exist

        return _wrapped_view

    return decorator


def get_data_for_position1(taiwei, todaytime, shunxu):
    try:
        return bogie.objects.get(todaytime=todaytime, shunxu=str(shunxu), taiwei=str(taiwei))

    except ObjectDoesNotExist:
        return None


def get_data_for_position2(taiwei, todaytime, shunxu):
    try:
        return initial.objects.get(todaytime=todaytime, shunxu=str(shunxu), taiwei=str(taiwei))

    except ObjectDoesNotExist:
        return None


def get_data_for_position4(todaytime):
    try:
        return order.objects.get(todaytime=todaytime, )

    except ObjectDoesNotExist:
        return None


@allowed_users(
    ['role1', 'role2', 'role3', 'role4', 'role5', 'role6', 'role19', 'role20'])
def index(request):
    context1 = {}
    current_url_name = resolve(request.path_info).url_name
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'), (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'),
                         (16, '8-7'), (17, '8-8'), (18, '8-9'), (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'),
                         (23, '9-5'), (24, '9-6'), (25, '9-7'), (26, '9-8'), (27, '9-9'),
                         ]
    if request.method == 'POST':
        shunxu = request.POST.get('shunxu')
        date_str = request.POST.get('date')
        shunxu_choise = {
            '1': "一次入库",
            '2': "二次入库",
            '3': "三次入库",
        }
        if shunxu in shunxu_choise:
            context1['shunxu_display'] = shunxu_choise[shunxu]
        else:
            context1['shunxu_display'] = "未知入库选项"
        if date_str:
            today = datetime.strptime(date_str, "%m/%d/%Y")
        else:
            today = datetime.now().strftime("%Y-%m-%d")
        orders = order.objects.filter(todaytime__date=today)
        position_data1 = {}
        position_data2 = {}
        combined_positions = {}
        for pos in positions:
            matched_number = next((number for number, position in positions_choices if position == pos), None)
            if matched_number is not None:
                position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
                position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
                combined_positions[pos] = {
                    "data1": position_data1.get(pos),
                    "data2": position_data2.get(pos)
                }
        data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
        context = {'shunxu': shunxu, 'date': date_str, 'context1': context1, 'orders': orders, 'data_list': data_list,
                   'current_url_name': current_url_name, 'today': today}
        return render(request, 'index.html', context)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        orders = order.objects.filter(todaytime__date=today)
        shunxu = "1"
        date_str = datetime.now().strftime('%m/%d/%Y')
        shunxu_choise = {
            '1': "一次入库",
            '2': "二次入库",
            '3': "三次入库",
        }
        if shunxu in shunxu_choise:
            context1['shunxu_display'] = shunxu_choise[shunxu]
        else:
            context1['shunxu_display'] = "未知入库选项"
        position_data1 = {}
        position_data2 = {}
        combined_positions = {}
        for pos in positions:
            matched_number = next((number for number, position in positions_choices if position == pos), None)
            if matched_number is not None:
                position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
                position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
                combined_positions[pos] = {
                    "data1": position_data1.get(pos),
                    "data2": position_data2.get(pos)
                }
        data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
        context = {'shunxu': shunxu, 'date': date_str, 'context1': context1, 'orders': orders, 'data_list': data_list,
                   'current_url_name': current_url_name, 'today': today}
        return render(request, 'index.html', context)


@allowed_users(['role1', 'role2', 'role3', 'role5', 'role19', 'role20'])
def index1(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "1"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data1.get(pos),
                "data2": position_data2.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
    return render(request, 'index1.html',
                  {'orders': orders, 'data_list': data_list, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def index4(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "1"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data1.get(pos),
                "data2": position_data2.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
    return render(request, 'index4.html',
                  {'orders': orders, 'data_list': data_list, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role3', 'role6', 'role19', 'role20'])
def index7(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    shunxu = "1"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data2.get(pos),
                "data2": position_data1.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data1'].beizhu, x['position']))
            if x['data']['data1'] and x['data']['data1'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )

    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', ]

    context = {
        'orders': orders,
        'highlight_list': highlight_list,
        'data_list': data_list,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today
    }
    return render(request, 'index7.html', context)


def find_nearest(lst, target):
    return min(lst, key=lambda x: abs(x - target))


def copy_data1(request):
    global new_data, n11, n12
    lst = [-20, -15, -12, -10, -8, -5, -2, 0, 8, 10, 12, 14, 16, 18, 20, 25, 28, 30, 32, 34, 35, 36, 38, 40, 42, 45, 48,
           50, 55, 60]
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    taiwei = request.GET.get('position')
    taiwei_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                      (9, '7-9'),
                      (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                      (17, '8-8'), (18, '8-9'),
                      (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                      (26, '9-8'), (27, '9-9'),
                      ]

    # 在taiwei_choices中查找位置为taiwei的元素
    matched_number = next((number for number, position in taiwei_choices if position == taiwei), None)
    shunxu = "1"
    data_from_1 = initial.objects.filter(todaytime=today, shunxu=shunxu, taiwei=matched_number).first()

    if not data_from_1.lunjing1 or not data_from_1.lunjing2:
        return JsonResponse({"success": False, "reason": "缺少数据！"})

    n1 = data_from_1.chegou1
    n2 = data_from_1.chegou2
    n3 = data_from_1.dianban1
    n4 = data_from_1.dianban2
    n5 = data_from_1.lunjing1
    n6 = data_from_1.lunjing2
    n7 = n3
    n11 = find_nearest(lst, n7)
    n9 = n5 - 8 / 5 * (n1 - 875) + n3 - n7
    if n9 < 796:
        n9 = 796
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)
    if n9 > 845:
        n9 = 845
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)

    n8 = n4
    n12 = find_nearest(lst, n8)
    n10 = n6 - 8 / 5 * (n2 - 875) + n4 - n8
    if n10 < 796:
        n10 = 796
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)
    if n10 > 845:
        n10 = 845
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)

    def adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12):
        while abs(n9 - n10) > 10:
            if n9 > n10:
                n9 -= 3
                n10 += 2
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)
            else:
                n10 -= 3
                n9 += 2
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n9 < 796:
                n9 = 796
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n9 > 845:
                n9 = 845
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n10 < 796:
                n10 = 796
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n10 > 845:
                n10 = 845
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

        return n9, n10, n11, n12

    n9, n10, n11, n12 = adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12)

    new_data = bogie(
        taiwei=data_from_1.taiwei,
        shunxu=data_from_1.shunxu,
        dianban1=n11,
        dianban2=n12,
        lunjing1=n9,
        lunjing2=n10,
        todaytime=today,
    )

    if bogie.objects.filter(todaytime=today, taiwei=matched_number, shunxu=shunxu).exists():
        return JsonResponse({"success": False, "reason": "数据已存在！"})

    new_data.save()
    # 记录用户的保存操作。假设用户已经登录，用户名已经保存在session中
    username = request.session.get("username", "unknown user")
    logger.info(
        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}重新计算了{taiwei}一次入库的数据。')
    return JsonResponse({"success": True})


@allowed_users(['role1', 'role2', 'role3', 'role5', 'role19', 'role20'])
def index2(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "2"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data1.get(pos),
                "data2": position_data2.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
    return render(request, 'index2.html',
                  {'orders': orders, 'data_list': data_list, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def index5(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "2"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data1.get(pos),
                "data2": position_data2.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
    return render(request, 'index5.html',
                  {'orders': orders, 'data_list': data_list, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role3', 'role6', 'role19', 'role20'])
def index8(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    shunxu = "2"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data2.get(pos),
                "data2": position_data1.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data1'].beizhu, x['position']))
            if x['data']['data1'] and x['data']['data1'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )

    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', ]

    context = {
        'orders': orders,
        'highlight_list': highlight_list,
        'data_list': data_list,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today
    }
    return render(request, 'index8.html', context)


def copy_data2(request):
    global new_data, n11, n12
    lst = [-20, -15, -12, -10, -8, -5, -2, 0, 8, 10, 12, 14, 16, 18, 20, 25, 28, 30, 32, 34, 35, 36, 38, 40, 42, 45, 48,
           50, 55, 60]
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    taiwei = request.GET.get('position')
    taiwei_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                      (9, '7-9'),
                      (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                      (17, '8-8'), (18, '8-9'),
                      (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                      (26, '9-8'), (27, '9-9'),
                      ]

    # 在taiwei_choices中查找位置为taiwei的元素
    matched_number = next((number for number, position in taiwei_choices if position == taiwei), None)
    shunxu = "2"
    data_from_1 = initial.objects.filter(todaytime=today, shunxu=shunxu, taiwei=matched_number).first()

    if not data_from_1.lunjing1 or not data_from_1.lunjing2:
        return JsonResponse({"success": False, "reason": "缺少数据！"})

    n1 = data_from_1.chegou1
    n2 = data_from_1.chegou2
    n3 = data_from_1.dianban1
    n4 = data_from_1.dianban2
    n5 = data_from_1.lunjing1
    n6 = data_from_1.lunjing2
    n7 = n3
    n11 = find_nearest(lst, n7)
    n9 = n5 - 8 / 5 * (n1 - 875) + n3 - n7
    if n9 < 796:
        n9 = 796
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)
    if n9 > 845:
        n9 = 845
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)

    n8 = n4
    n12 = find_nearest(lst, n8)
    n10 = n6 - 8 / 5 * (n2 - 875) + n4 - n8
    if n10 < 796:
        n10 = 796
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)
    if n10 > 845:
        n10 = 845
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)

    def adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12):
        while abs(n9 - n10) > 10:
            if n9 > n10:
                n9 -= 3
                n10 += 2
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)
            else:
                n10 -= 3
                n9 += 2
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n9 < 796:
                n9 = 796
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n9 > 845:
                n9 = 845
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n10 < 796:
                n10 = 796
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n10 > 845:
                n10 = 845
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

        return n9, n10, n11, n12

    n9, n10, n11, n12 = adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12)

    new_data = bogie(
        taiwei=data_from_1.taiwei,
        shunxu=data_from_1.shunxu,
        dianban1=n11,
        dianban2=n12,
        lunjing1=n9,
        lunjing2=n10,
        todaytime=today,
    )

    if bogie.objects.filter(todaytime=today, taiwei=matched_number, shunxu=shunxu).exists():
        return JsonResponse({"success": False, "reason": "数据已存在！"})

    new_data.save()
    username = request.session.get("username", "unknown user")
    logger.info(
        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}重新计算了{taiwei}二次入库的数据。')
    return JsonResponse({"success": True})


@allowed_users(['role1', 'role2', 'role3', 'role5', 'role19', 'role20'])
def index3(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "3"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data1.get(pos),
                "data2": position_data2.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
    return render(request, 'index3.html',
                  {'orders': orders, 'data_list': data_list, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def index6(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "3"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data1.get(pos),
                "data2": position_data2.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]
    return render(request, 'index6.html',
                  {'orders': orders, 'data_list': data_list, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role3', 'role6', 'role19', 'role20'])
def index9(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    shunxu = "3"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data2.get(pos),
                "data2": position_data1.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data1'].beizhu, x['position']))
            if x['data']['data1'] and x['data']['data1'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )

    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', ]

    context = {
        'orders': orders,
        'highlight_list': highlight_list,
        'data_list': data_list,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today
    }
    return render(request, 'index9.html', context)


def copy_data3(request):
    global new_data, n11, n12
    lst = [-20, -15, -12, -10, -8, -5, -2, 0, 8, 10, 12, 14, 16, 18, 20, 25, 28, 30, 32, 34, 35, 36, 38, 40, 42, 45, 48,
           50, 55, 60]
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    taiwei = request.GET.get('position')
    taiwei_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                      (9, '7-9'),
                      (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                      (17, '8-8'), (18, '8-9'),
                      (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                      (26, '9-8'), (27, '9-9'),
                      ]

    # 在taiwei_choices中查找位置为taiwei的元素
    matched_number = next((number for number, position in taiwei_choices if position == taiwei), None)
    shunxu = "3"
    data_from_1 = initial.objects.filter(todaytime=today, shunxu=shunxu, taiwei=matched_number).first()

    if not data_from_1.lunjing1 or not data_from_1.lunjing2:
        return JsonResponse({"success": False, "reason": "缺少数据！"})

    n1 = data_from_1.chegou1
    n2 = data_from_1.chegou2
    n3 = data_from_1.dianban1
    n4 = data_from_1.dianban2
    n5 = data_from_1.lunjing1
    n6 = data_from_1.lunjing2
    n7 = n3
    n11 = find_nearest(lst, n7)
    n9 = n5 - 8 / 5 * (n1 - 875) + n3 - n7
    if n9 < 796:
        n9 = 796
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)
    if n9 > 845:
        n9 = 845
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)

    n8 = n4
    n12 = find_nearest(lst, n8)
    n10 = n6 - 8 / 5 * (n2 - 875) + n4 - n8
    if n10 < 796:
        n10 = 796
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)
    if n10 > 845:
        n10 = 845
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)

    def adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12):
        while abs(n9 - n10) > 10:
            if n9 > n10:
                n9 -= 3
                n10 += 2
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)
            else:
                n10 -= 3
                n9 += 2
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n9 < 796:
                n9 = 796
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n9 > 845:
                n9 = 845
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n10 < 796:
                n10 = 796
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n10 > 845:
                n10 = 845
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

        return n9, n10, n11, n12

    n9, n10, n11, n12 = adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12)

    new_data = bogie(
        taiwei=data_from_1.taiwei,
        shunxu=data_from_1.shunxu,
        dianban1=n11,
        dianban2=n12,
        lunjing1=n9,
        lunjing2=n10,
        todaytime=today,
    )

    if bogie.objects.filter(todaytime=today, taiwei=matched_number, shunxu=shunxu).exists():
        return JsonResponse({"success": False, "reason": "数据已存在！"})

    new_data.save()
    username = request.session.get("username", "unknown user")
    logger.info(
        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}重新计算了{taiwei}三次入库的数据。')
    return JsonResponse({"success": True})


class bogieForm(ModelForm):
    class Meta:
        model = models.bogie
        fields = ["lunjing2", "lunjing1", "dianban2", "dianban1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


def copy_data_logic1(taiwei, shunxu, today):
    lst = [-20, -15, -12, -10, -8, -5, -2, 0, 8, 10, 12, 14, 16, 18, 20, 25, 28, 30, 32, 34, 35, 36, 38, 40, 42, 45, 48,
           50, 55, 60]
    taiwei_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                      (9, '7-9'),
                      (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                      (17, '8-8'), (18, '8-9'),
                      (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                      (26, '9-8'), (27, '9-9'),
                      ]

    # 在taiwei_choices中查找位置为taiwei的元素
    matched_number = next((number for number, position in taiwei_choices if position == taiwei), None)
    data_from_1 = initial.objects.filter(todaytime=today, shunxu=shunxu, taiwei=matched_number).first()
    data_from_2 = bogie.objects.filter(todaytime=today, shunxu=shunxu, taiwei=matched_number).first()
    if not data_from_1:
        return JsonResponse({"success": False, "reason": "缺少数据！"})
    n1 = data_from_1.chegou1
    n2 = data_from_1.chegou2
    n3 = data_from_1.dianban1
    n4 = data_from_1.dianban2
    n5 = data_from_1.lunjing1
    n6 = data_from_1.lunjing2
    n9 = data_from_2.lunjing1
    n10 = data_from_2.lunjing2
    n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
    n11 = find_nearest(lst, n7)
    n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
    n12 = find_nearest(lst, n8)

    return {
        'success': True,
        'data': {
            'n11': n11,
            'n12': n12
        }
    }


def user_edit2(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")

    if request.method == "GET":
        row_object = models.bogie.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
        form = bogieForm(instance=row_object)
        context = {'form': form, "today": today}
        return render(request, "user_edit2.html", context)

    row_object = models.bogie.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
    form = bogieForm(data=request.POST, instance=row_object)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.is_updated = True
        taiwei_display = instance.get_taiwei_display()
        shunxu_display = instance.get_shunxu_display()
        shunxu = instance.shunxu
        username = request.session.get("username", "unknown user")

        if 'save_all' in request.POST:
            # 如果点击了 "保存轮径" 按钮，保存所有的变动
            instance.save()
            if form.instance.lunjing1 is None or form.instance.lunjing2 is None:
                messages.info(request, f"新轮径保存成功！但因数据不完整，未计算垫板数据!新轮径2位{instance.lunjing2}、1位{instance.lunjing1}，新垫板2位{instance.dianban2}、1位{instance.dianban1}。")
                logger.info(
                    f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用电脑编辑了配轮数据{taiwei_display}{shunxu_display}的轮径和垫板数据，但因数据不完整，未计算垫板数据!新轮径2位{instance.lunjing2}、1位{instance.lunjing1}，新垫板2位{instance.dianban2}、1位{instance.dianban1}。')
                return render(request, "user_edit2.html", {'form': form, "today": today})
            else:
                res = copy_data_logic1(taiwei_display, shunxu, today)
                instance.dianban1 = res["data"]["n11"]
                instance.dianban2 = res["data"]["n12"]
                instance.save()
                if instance.dianban1 < 0 or instance.dianban2 < 0:
                    messages.info(request,
                                   f"轮径修改成功并已自动计算垫板厚度！但是心盘垫板厚度超限，分别为{instance.dianban2}和{instance.dianban1}，会导致车钩高度过高，请注意！")
                elif instance.dianban1 > 40 or instance.dianban2 > 40:
                    messages.info(request,
                                   f"轮径修改成功并已自动计算垫板厚度！但是心盘垫板厚度超限，分别为{instance.dianban2}和{instance.dianban1}，会导致车钩高度过低，请注意！")
                else:
                    messages.success(request, f"轮径修改成功并已自动计算垫板厚度！新轮径2位{instance.lunjing2}、1位{instance.lunjing1}，新垫板2位{instance.dianban2}、1位{instance.dianban1}。")
                logger.info(
                    f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用电脑编辑了配轮数据{taiwei_display}{shunxu_display}的轮径和垫板数据，新轮径2位{instance.lunjing2}、1位{instance.lunjing1}，新垫板2位{instance.dianban2}、1位{instance.dianban1}。')
        if 'save_dianban_only' in request.POST:
            # 如果点击了 "仅保存垫板" 按钮，只保存垫板相关的数据
            instance.dianban1 = form.cleaned_data['dianban1']
            instance.dianban2 = form.cleaned_data['dianban2']
            instance.save()
            messages.success(request, f"自定义垫板修改成功！2位{instance.dianban2}、1位{instance.dianban1}。")
            logger.info(
                f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用电脑编辑了配轮数据{taiwei_display}{shunxu_display}的自定义垫板数据，2位{instance.dianban2}、1位{instance.dianban1}。')

        return render(request, "user_edit2.html", {'form': form, "today": today})
    return render(request, 'user_edit2.html', {'form': form, "today": today, 'error': form.errors})


def user_edit3(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    if request.method == "GET":
        row_object = models.bogie.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
        form = bogieForm(instance=row_object)
        shunxu_plus_2 = form.instance.shunxu + 3
        context = {'form': form, "today": today, 'shunxu_plus_2': shunxu_plus_2}
        return render(request, "user_edit3.html", context)

    row_object = models.bogie.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
    form = bogieForm(data=request.POST, instance=row_object)
    shunxu_plus_2 = form.instance.shunxu + 3
    if form.is_valid():
        instance = form.save(commit=False)
        instance.is_updated = True
        taiwei_display = instance.get_taiwei_display()
        shunxu_display = instance.get_shunxu_display()
        shunxu = instance.shunxu
        username = request.session.get("username", "unknown user")

        if 'save_all' in request.POST:
            # 如果点击了 "保存轮径" 按钮，保存所有的变动
            instance.save()
            logger.info(
                f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}在架车班手持机页面编辑了配轮数据{taiwei_display}{shunxu_display}的轮径和垫板数据。')
            if form.instance.lunjing1 is None or form.instance.lunjing2 is None or form.instance.dianban1 is None or form.instance.dianban2 is None:
                return render(request, "user_edit3.html", {'form': form, "today": today, 'shunxu_plus_2': shunxu_plus_2,
                                                           'success': "  新轮径保存成功！但因数据不完整，未计算垫板数据。!"})
            else:
                res = copy_data_logic1(taiwei_display, shunxu, today)
                instance.dianban1 = res["data"]["n11"]
                instance.dianban2 = res["data"]["n12"]
                instance.save()

        if 'save_dianban_only' in request.POST:
            # 如果点击了 "仅保存垫板" 按钮，只保存垫板相关的数据
            instance.dianban1 = form.cleaned_data['dianban1']
            instance.dianban2 = form.cleaned_data['dianban2']
            instance.save()
            logger.info(
                f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用手持机编辑了配轮数据{taiwei_display}{shunxu_display}的垫板数据。')
        return render(request, "user_edit3.html", {'form': form, "today": today,
                                                   'shunxu_plus_2': shunxu_plus_2, 'success': "  修改成功!"})
    return render(request, 'user_edit3.html',
                  {'form': form, "today": today, 'shunxu_plus_2': shunxu_plus_2, 'error': form.errors})


class user_edit4Form(ModelForm):
    class Meta:
        model = models.bogie
        fields = ["lunjing2", "lunjing1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


def user_edit4(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    if request.method == "GET":
        row_object = models.bogie.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
        form = user_edit4Form(instance=row_object)
        shunxu_plus_2 = form.instance.shunxu + 6
        context = {'form': form, "today": today, 'shunxu_plus_2': shunxu_plus_2}
        return render(request, "user_edit4.html", context)

    row_object = models.bogie.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
    form = user_edit4Form(data=request.POST, instance=row_object)
    shunxu_plus_2 = form.instance.shunxu + 6

    if form.is_valid():
        instance = form.save(commit=False)
        instance.is_updated = True
        taiwei_display = instance.get_taiwei_display()
        shunxu_display = instance.get_shunxu_display()
        shunxu = instance.shunxu
        username = request.session.get("username", "unknown user")
        instance.save()
        if form.instance.lunjing1 is None or form.instance.lunjing2 is None or form.instance.dianban1 is None or form.instance.dianban2 is None:
            messages.error(request, "新轮径保存成功！但因数据不完整，未计算垫板数据！")
            return render(request, "user_edit4.html",
                          {'form': form, "today": today, 'shunxu_plus_2': shunxu_plus_2})
        else:
            res = copy_data_logic1(taiwei_display, shunxu, today)
            instance.dianban1 = res["data"]["n11"]
            instance.dianban2 = res["data"]["n12"]
            instance.save()
            if instance.dianban1 < 0 or instance.dianban2 < 0:
                messages.info(request,
                                 f"轮径修改成功并已自动计算垫板厚度！但是心盘垫板厚度超限，分别为{instance.dianban2}和{instance.dianban1}，会导致车钩高度过高，请注意！")
            elif instance.dianban1 > 40 or instance.dianban2 > 40:
                messages.info(request,
                                 f"轮径修改成功并已自动计算垫板厚度！但是心盘垫板厚度超限，分别为{instance.dianban2}和{instance.dianban1}，会导致车钩高度过低，请注意！")
            else:
                messages.success(request,f"轮径修改成功并已自动计算垫板厚度！")
        logger.info(
            f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}在轮轴班手持机页面修改了配轮数据{taiwei_display}{shunxu_display}的轮径和垫板数据，修改后的数据：轮径2位{instance.lunjing2}、1位{instance.lunjing1}，心盘垫板厚度2位{instance.dianban2}、1位{instance.dianban1}。')
        return render(request, "user_edit4.html", {'form': form, "today": today,
                                                   'shunxu_plus_2': shunxu_plus_2})
    return render(request, 'user_edit4.html',
                  {'form': form, "today": today, 'shunxu_plus_2': shunxu_plus_2, 'error': form.errors})


@csrf_exempt
def user_delete2(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    instance = get_object_or_404(bogie, taiwei=nid1, shunxu=nid2, todaytime=today)
    if request.method == 'POST':
        instance.delete()
        return JsonResponse({'status': 'ok'})
    return render(request, 'user_delete.html', {'taiwei': nid1, 'shunxu': nid2})


class initialForm(ModelForm):
    class Meta:
        model = models.initial
        fields = ["chegou2", "pangcheng2", "dianban2", "lunjing2", "chegou1", "pangcheng1", "dianban1",
                  "lunjing1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


def is_field_filled(value):
    return value is not None and value != ''


def copy_data_logic(data_from_1, today):
    global new_data, n11, n12
    lst = [-20, -15, -12, -10, -8, -5, -2, 0, 8, 10, 12, 14, 16, 18, 20, 25, 28, 30, 32, 34, 35, 36, 38, 40, 42, 45, 48,
           50, 55, 60]
    n1 = data_from_1.chegou1
    n2 = data_from_1.chegou2
    n3 = data_from_1.dianban1
    n4 = data_from_1.dianban2
    n5 = data_from_1.lunjing1
    n6 = data_from_1.lunjing2
    n7 = n3
    n11 = find_nearest(lst, n7)
    n9 = n5 - 8 / 5 * (n1 - 875) + n3 - n7
    if n9 < 796:
        n9 = 796
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)
    if n9 > 845:
        n9 = 845
        n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
        n11 = find_nearest(lst, n7)

    n8 = n4
    n12 = find_nearest(lst, n8)
    n10 = n6 - 8 / 5 * (n2 - 875) + n4 - n8
    if n10 < 796:
        n10 = 796
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)
    if n10 > 845:
        n10 = 845
        n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
        n12 = find_nearest(lst, n8)

    def adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12):
        while abs(n9 - n10) > 10:
            if n9 > n10:
                n9 -= 3
                n10 += 2
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)
            else:
                n10 -= 3
                n9 += 2
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n9 < 796:
                n9 = 796
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n9 > 845:
                n9 = 845
                n7 = 4 * (875 - n1) / 5 + n3 + (n5 - n9) / 2
                n11 = find_nearest(lst, n7)

            if n10 < 796:
                n10 = 796
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

            if n10 > 845:
                n10 = 845
                n8 = 4 * (875 - n2) / 5 + n4 + (n6 - n10) / 2
                n12 = find_nearest(lst, n8)

        return n9, n10, n11, n12

    n9, n10, n11, n12 = adjust_values(n1, n2, n3, n4, n5, n6, n9, n10, n11, n12)

    return {
        'taiwei': data_from_1.taiwei,
        'shunxu': data_from_1.shunxu,
        'dianban1': n11,
        'dianban2': n12,
        'lunjing1': n9,
        'lunjing2': n10,
        'todaytime': today,
    }


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add1(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(1, 10), shunxu=1, todaytime=today)
    initialFormSet = modelformset_factory(models.initial, form=initialForm, extra=0)
    positions = [f"{7}-{i}" for i in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'),
                         (8, '7-8'), (9, '7-9')]
    if request.method == 'GET':
        formset = initialFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
                   'current_url_name': current_url_name, 'today': today,
                   'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices}
        return render(request, '架车班信息采集界面1.html', context)

    formset = initialFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
            # 检查所有必要字段是否都已经被填写
            required_fields = ['chegou2', 'dianban2', 'lunjing2', 'chegou1', 'dianban1', 'lunjing1']
            if all(is_field_filled(getattr(obj, field)) for field in required_fields):
                new_bogie_data = copy_data_logic(obj, obj.todaytime)
                taiwei_display = obj.get_taiwei_display()
                # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                bogie_obj, created = bogie.objects.update_or_create(
                    taiwei=new_bogie_data['taiwei'],
                    shunxu=new_bogie_data['shunxu'],
                    todaytime=new_bogie_data['todaytime'],
                    defaults=new_bogie_data,
                )
                if not created:  # 只有在更新对象时设置 is_updated
                    bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                    username = request.session.get("username", "unknown user")
                    logger.info(
                        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端重新更新了{taiwei_display}一次入库的配轮数据。')
            messages.success(request, '添加成功！')
        return redirect('user_add1')
    else:
        messages.error(request, '表单不符合要求，请修改后重新提交')
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today, 'choices1': gudao1_choices,
               'choices2': gudao2_choices, 'choices3': gudao3_choices}
    return render(request, '架车班信息采集界面1.html', context)


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add2(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(10, 19), shunxu=1, todaytime=today)
    initialFormSet = modelformset_factory(models.initial, form=initialForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"{8}-{i}" for i in range(1, 10)]
    positions_choices = [(10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9')]
    if request.method == 'GET':
        formset = initialFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'choices1': gudao1_choices,
                   'choices2': gudao2_choices, 'choices3': gudao3_choices,
                   'formset': formset, 'current_url_name': current_url_name, 'today': today}
        return render(request, '架车班信息采集界面2.html', context)

    formset = initialFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
            # 检查所有必要字段是否都已经被填写
            required_fields = ['chegou2', 'dianban2', 'lunjing2', 'chegou1', 'dianban1', 'lunjing1']
            if all(is_field_filled(getattr(obj, field)) for field in required_fields):
                new_bogie_data = copy_data_logic(obj, obj.todaytime)
                taiwei_display = obj.get_taiwei_display()
                # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                bogie_obj, created = bogie.objects.update_or_create(
                    taiwei=new_bogie_data['taiwei'],
                    shunxu=new_bogie_data['shunxu'],
                    todaytime=new_bogie_data['todaytime'],
                    defaults=new_bogie_data,
                )
                if not created:  # 只有在更新对象时设置 is_updated
                    bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                    username = request.session.get("username", "unknown user")
                    logger.info(
                        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端更新了{taiwei_display}一次入库的配轮数据。')
            messages.success(request, '添加成功！')
        return redirect('user_add2')
    else:
        messages.error(request, '表单不符合要求，请修改后重新提交')
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '架车班信息采集界面2.html', context)


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add3(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(19, 28), shunxu=1, todaytime=today)
    initialFormSet = modelformset_factory(models.initial, form=initialForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"{9}-{i}" for i in range(1, 10)]
    positions_choices = [(19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9')]
    if request.method == 'GET':
        formset = initialFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'choices1': gudao1_choices,
                   'choices2': gudao2_choices, 'choices3': gudao3_choices,
                   'formset': formset, 'current_url_name': current_url_name, 'today': today}
        return render(request, '架车班信息采集界面3.html', context)

    formset = initialFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
            # 检查所有必要字段是否都已经被填写
            required_fields = ['chegou2', 'dianban2', 'lunjing2', 'chegou1', 'dianban1', 'lunjing1']
            if all(is_field_filled(getattr(obj, field)) for field in required_fields):
                new_bogie_data = copy_data_logic(obj, obj.todaytime)
                taiwei_display = obj.get_taiwei_display()
                # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                bogie_obj, created = bogie.objects.update_or_create(
                    taiwei=new_bogie_data['taiwei'],
                    shunxu=new_bogie_data['shunxu'],
                    todaytime=new_bogie_data['todaytime'],
                    defaults=new_bogie_data,
                )
                if not created:  # 只有在更新对象时设置 is_updated
                    bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                    username = request.session.get("username", "unknown user")
                    logger.info(
                        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端更新了{taiwei_display}一次入库的配轮数据。')
            messages.success(request, '添加成功！')
        return redirect('user_add3')
    else:
        messages.error(request, '表单不符合要求，请修改后重新提交')
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '架车班信息采集界面3.html', context)


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add4(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(1, 10), shunxu=2, todaytime=today)
    initialFormSet = modelformset_factory(models.initial, form=initialForm, extra=0)
    positions = [f"{7}-{i}" for i in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'),
                         (8, '7-8'), (9, '7-9')]
    if request.method == 'GET':
        formset = initialFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
                   'current_url_name': current_url_name, 'today': today}
        return render(request, '架车班信息采集界面4.html', context)

    formset = initialFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
            # 检查所有必要字段是否都已经被填写
            required_fields = ['chegou2', 'dianban2', 'lunjing2', 'chegou1', 'dianban1', 'lunjing1']
            if all(is_field_filled(getattr(obj, field)) for field in required_fields):
                new_bogie_data = copy_data_logic(obj, obj.todaytime)
                taiwei_display = obj.get_taiwei_display()
                # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                bogie_obj, created = bogie.objects.update_or_create(
                    taiwei=new_bogie_data['taiwei'],
                    shunxu=new_bogie_data['shunxu'],
                    todaytime=new_bogie_data['todaytime'],
                    defaults=new_bogie_data,
                )
                if not created:  # 只有在更新对象时设置 is_updated
                    bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                    username = request.session.get("username", "unknown user")
                    logger.info(
                        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端更新了{taiwei_display}二次入库的配轮数据。')
            messages.success(request, '添加成功！')
        return redirect('user_add4')
    else:
        messages.error(request, '表单不符合要求，请修改后重新提交')
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '架车班信息采集界面4.html', context)


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add5(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(10, 19), shunxu=2, todaytime=today)
    initialFormSet = modelformset_factory(models.initial, form=initialForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"{8}-{i}" for i in range(1, 10)]
    positions_choices = [(10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9')]
    if request.method == 'GET':
        formset = initialFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'choices1': gudao1_choices,
                   'choices2': gudao2_choices, 'choices3': gudao3_choices,
                   'formset': formset, 'current_url_name': current_url_name, 'today': today}
        return render(request, '架车班信息采集界面5.html', context)

    formset = initialFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
            # 检查所有必要字段是否都已经被填写
            required_fields = ['chegou2', 'dianban2', 'lunjing2', 'chegou1', 'dianban1', 'lunjing1']
            if all(is_field_filled(getattr(obj, field)) for field in required_fields):
                new_bogie_data = copy_data_logic(obj, obj.todaytime)
                taiwei_display = obj.get_taiwei_display()
                # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                bogie_obj, created = bogie.objects.update_or_create(
                    taiwei=new_bogie_data['taiwei'],
                    shunxu=new_bogie_data['shunxu'],
                    todaytime=new_bogie_data['todaytime'],
                    defaults=new_bogie_data,
                )
                if not created:  # 只有在更新对象时设置 is_updated
                    bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                    username = request.session.get("username", "unknown user")
                    logger.info(
                        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端更新了{taiwei_display}二次入库的配轮数据。')
            messages.success(request, '添加成功！')
        return redirect('user_add5')
    else:
        messages.error(request, '表单不符合要求，请修改后重新提交')
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '架车班信息采集界面5.html', context)


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add6(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(19, 28), shunxu=2, todaytime=today)
    initialFormSet = modelformset_factory(models.initial, form=initialForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"{9}-{i}" for i in range(1, 10)]
    positions_choices = [(19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9')]
    if request.method == 'GET':
        formset = initialFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'choices1': gudao1_choices,
                   'choices2': gudao2_choices, 'choices3': gudao3_choices,
                   'formset': formset, 'current_url_name': current_url_name, 'today': today}
        return render(request, '架车班信息采集界面6.html', context)

    formset = initialFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
            # 检查所有必要字段是否都已经被填写
            required_fields = ['chegou2', 'dianban2', 'lunjing2', 'chegou1', 'dianban1', 'lunjing1']
            if all(is_field_filled(getattr(obj, field)) for field in required_fields):
                new_bogie_data = copy_data_logic(obj, obj.todaytime)
                taiwei_display = obj.get_taiwei_display()
                # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                bogie_obj, created = bogie.objects.update_or_create(
                    taiwei=new_bogie_data['taiwei'],
                    shunxu=new_bogie_data['shunxu'],
                    todaytime=new_bogie_data['todaytime'],
                    defaults=new_bogie_data,
                )
                if not created:  # 只有在更新对象时设置 is_updated
                    bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                    username = request.session.get("username", "unknown user")
                    logger.info(
                        f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端更新了{taiwei_display}二次入库的配轮数据。')
            messages.success(request, '添加成功！')
        return redirect('user_add6')
    else:
        messages.error(request, '表单不符合要求，请修改后重新提交')
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '架车班信息采集界面6.html', context)


class initialForm2(ModelForm):
    class Meta:
        model = models.initial
        fields = ["taiwei", "chegou2", "pangcheng2", "dianban2", "lunjing2", "chegou1", "pangcheng1", "dianban1",
                  "lunjing1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_add16(request):
    """架车班添加数据"""
    global matched_number
    current_url_name = resolve(request.path_info).url_name
    MyFormSet = formset_factory(initialForm2, extra=9)
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    shunxu = 3
    if request.method == 'GET':
        formset = MyFormSet()
        return render(request, '架车班信息采集界面7.html',
                      {'orders': orders, 'formset': formset, 'current_url_name': current_url_name, "today": today})
    formset = MyFormSet(request.POST or None)
    if formset.is_valid():
        results = []  # 添加这一行来收集每个表单的处理结果
        for i, form in enumerate(formset):
            model_instance = initial()
            model_instance.taiwei = form.cleaned_data.get('taiwei')
            model_instance.shunxu = shunxu
            model_instance.xiucheng = form.cleaned_data.get('xiucheng')
            model_instance.chexing = form.cleaned_data.get('chexing')
            model_instance.chegou1 = form.cleaned_data.get('chegou1')
            model_instance.chegou2 = form.cleaned_data.get('chegou2')
            model_instance.dianban1 = form.cleaned_data.get('dianban1')
            model_instance.dianban2 = form.cleaned_data.get('dianban2')
            model_instance.lunjing1 = form.cleaned_data.get('lunjing1')
            model_instance.lunjing2 = form.cleaned_data.get('lunjing2')
            model_instance.pangcheng1 = form.cleaned_data.get('pangcheng1')
            model_instance.pangcheng2 = form.cleaned_data.get('pangcheng2')
            model_instance.todaytime = today

            if i == 0 and form.cleaned_data.get('taiwei') is None:
                context = {'orders': orders, 'formset': formset, 'current_url_name': current_url_name,
                           'results': results, "today": today,
                           'error': '请填写台位号再保存！'}
                return render(request, '架车班信息采集界面7.html', context)

            existing_records = initial.objects.filter(
                todaytime=model_instance.todaytime,
                shunxu=model_instance.shunxu,
                taiwei=model_instance.taiwei
            )
            if existing_records.exists():
                shunxu_display = model_instance.get_shunxu_display()
                taiwei_display = model_instance.get_taiwei_display()
                results.append(
                    f"{taiwei_display}{shunxu_display}数据已存在，保存失败，请去数据查询页面进行编辑！")
            else:
                model_instance.save()
                if (model_instance.lunjing1 is None or model_instance.lunjing2 is None or model_instance.chegou1 is None
                        or model_instance.chegou2 is None or model_instance.dianban1 is None
                        or model_instance.dianban2 is None):
                    results.append(f"保存成功，但因数据不完整，未进行配轮计算！")
                    return render(request, "架车班信息采集界面7.html",
                                  {'orders': orders, 'formset': formset, 'current_url_name': current_url_name,
                                   'results': results,
                                   "today": today})
                else:
                    new_bogie_data = copy_data_logic(model_instance, model_instance.todaytime)
                    taiwei_display = form.instance.get_taiwei_display()
                    # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
                    bogie_obj, created = bogie.objects.update_or_create(
                        taiwei=new_bogie_data['taiwei'],
                        shunxu=new_bogie_data['shunxu'],
                        todaytime=new_bogie_data['todaytime'],
                        defaults=new_bogie_data,
                    )
                    if not created:  # 只有在更新对象时设置 is_updated
                        bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                        username = request.session.get("username", "unknown user")
                        logger.info(
                            f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用PC端重新录入了{taiwei_display}一次入库的数据。')
                    results.append("添加成功!")
            context = {'orders': orders, 'formset': formset, 'current_url_name': current_url_name, "today": today,
                       'results': results}
            return render(request, '架车班信息采集界面7.html', context)
    else:
        context = {'orders': orders, 'formset': formset, 'current_url_name': current_url_name, "today": today,
                   'error': '无法保存，请检查数据是否符合要求！'}
        return render(request, '架车班信息采集界面7.html', context)


class initialForm1(ModelForm):
    class Meta:
        model = models.initial
        fields = ["taiwei", "chegou2", "pangcheng2", "dianban2", "lunjing2", "chegou1", "pangcheng1", "dianban1",
                  "lunjing1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_add14(request):
    today = datetime.now().strftime("%Y-%m-%d")
    current_url_name = resolve(request.path_info).url_name
    orders = order.objects.filter(todaytime__date=today)
    if request.method == 'GET':
        form = initialForm1()
        return render(request, "架车班信息手持机采集界面.html",
                      {"form": form, 'orders': orders, 'current_url_name': current_url_name, "today": today})

    form = initialForm1(data=request.POST)
    if form.is_valid():
        shunxu = 3
        taiwei = form.cleaned_data['taiwei']
        existing_record = initial.objects.filter(taiwei=taiwei, shunxu=shunxu).first()
        existing_records = initial.objects.filter(todaytime=today, shunxu=shunxu, taiwei=taiwei)
        if existing_record and existing_records.exists():
            taiwei_display = existing_record.get_taiwei_display()
            shunxu_display = existing_record.get_shunxu_display()
            messages.error(request, f"{taiwei_display}{shunxu_display}数据已存在，保存失败，请去数据查询页面进行编辑！")
        else:
            form.instance.todaytime = datetime.now().strftime("%Y-%m-%d")
            form.instance.shunxu = 3
            form.save()
            if not form.instance.lunjing1 or not form.instance.lunjing2:
                messages.success(request, "添加成功!")
                return redirect(reverse('user_add14'))
            new_bogie_data = copy_data_logic(form.instance, form.instance.todaytime)
            taiwei_display = form.instance.get_taiwei_display()
            # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
            bogie_obj, created = bogie.objects.get_or_create(
                taiwei=new_bogie_data['taiwei'],
                shunxu=new_bogie_data['shunxu'],
                todaytime=new_bogie_data['todaytime'],
                defaults=new_bogie_data,
            )

            if not created:  # 只有在更新对象时设置 is_updated
                bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
                username = request.session.get("username", "unknown user")
                logger.info(
                    f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}用手持机重新录入了{taiwei_display}一次入库的数据。')
            messages.success(request, "添加成功!")
            return redirect(reverse('user_add14'))
    else:
        messages.error(request, "表单验证失败，请检查数据是否符合要求。")
    return render(request, "架车班信息手持机采集界面.html",
                  {"form": form, 'orders': orders, 'current_url_name': current_url_name, "today": today})


class user_editForm(ModelForm):
    class Meta:
        model = models.initial
        fields = ["chegou2", "pangcheng2", "dianban2", "lunjing2",
                  "chegou1", "pangcheng1", "dianban1", "lunjing1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


def user_edit(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    current_url_name = resolve(request.path_info).url_name
    if request.method == "GET":
        row_object = models.initial.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
        form = user_editForm(instance=row_object)
        context = {'form': form, "today": today}
        return render(request, "user_edit.html", context)

    row_object = models.initial.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
    form = user_editForm(data=request.POST, instance=row_object)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.is_updated = True
        instance.save()
        if form.instance.lunjing1 is None or form.instance.lunjing2 is None or form.instance.chegou1 is None or form.instance.chegou2 is None or form.instance.dianban1 is None or form.instance.dianban2 is None:
            messages.error(request, "保存成功，但因数据不完整，未进行配轮计算！")
            return render(request, "user_edit.html",
                          {'form': form, 'current_url_name': current_url_name, "today": today})
        else:
            new_bogie_data = copy_data_logic(form.instance, form.instance.todaytime)
            # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
            bogie_obj, created = bogie.objects.update_or_create(
                taiwei=new_bogie_data['taiwei'],
                shunxu=new_bogie_data['shunxu'],
                todaytime=new_bogie_data['todaytime'],
                defaults=new_bogie_data,
            )
            messages.success(request, "添加成功!")
            return render(request, "user_edit.html",
                          {'form': form, 'current_url_name': current_url_name, "today": today})
    return render(request, "user_edit0.html", {'form': form, 'current_url_name': current_url_name, "today": today})


def get_n(form):
    if form.instance.shunxu == 1:
        if 1 <= form.instance.taiwei <= 9:
            return 1
        elif 10 <= form.instance.taiwei <= 18:
            return 2
        elif 19 <= form.instance.taiwei <= 27:
            return 3
    elif form.instance.shunxu == 2:
        if 1 <= form.instance.taiwei <= 9:
            return 4
        elif 10 <= form.instance.taiwei <= 18:
            return 5
        elif 19 <= form.instance.taiwei <= 27:
            return 6
    else:
        return 7


def user_edit0(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    current_url_name = resolve(request.path_info).url_name
    if request.method == "GET":
        row_object = models.initial.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
        form = user_editForm(instance=row_object)
        n = get_n(form)
        context = {'form': form, "today": today, "n": n}
        return render(request, "user_edit0.html", context)

    row_object = models.initial.objects.filter(taiwei=nid1, shunxu=nid2, todaytime=today).first()
    form = user_editForm(data=request.POST, instance=row_object)
    n = get_n(form)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.is_updated = True
        instance.save()
        if form.instance.lunjing1 is None or form.instance.lunjing2 is None or form.instance.chegou1 is None or form.instance.chegou2 is None or form.instance.dianban1 is None or form.instance.dianban2 is None:
            messages.error(request, "保存成功，但因数据不完整，未进行配轮计算！")
            if form.instance.shunxu == 1 and (1 <= form.instance.taiwei <= 9):
                return redirect('user_list4')
            elif form.instance.shunxu == 1 and (10 <= form.instance.taiwei <= 18):
                return redirect('user_list5')
            elif form.instance.shunxu == 1 and (19 <= form.instance.taiwei <= 27):
                return redirect('user_list6')
            elif form.instance.shunxu == 2 and (1 <= form.instance.taiwei <= 9):
                return redirect('user_list7')
            elif form.instance.shunxu == 2 and (10 <= form.instance.taiwei <= 18):
                return redirect('user_list8')
            elif form.instance.shunxu == 2 and (19 <= form.instance.taiwei <= 27):
                return redirect('user_list9')
            else:
                return redirect('user_list20')
        else:
            new_bogie_data = copy_data_logic(form.instance, form.instance.todaytime)
            # 查找是否我们已经有了一个同样的 bogie 对象，如果有，更新它；否则创建新的
            bogie_obj, created = bogie.objects.update_or_create(
                taiwei=new_bogie_data['taiwei'],
                shunxu=new_bogie_data['shunxu'],
                todaytime=new_bogie_data['todaytime'],
                defaults=new_bogie_data,
            )
            messages.success(request, "添加成功!")
            if form.instance.shunxu == 1 and (1 <= form.instance.taiwei <= 9):
                return redirect('user_list4')
            elif form.instance.shunxu == 1 and (10 <= form.instance.taiwei <= 18):
                return redirect('user_list5')
            elif form.instance.shunxu == 1 and (19 <= form.instance.taiwei <= 27):
                return redirect('user_list6')
            elif form.instance.shunxu == 2 and (1 <= form.instance.taiwei <= 9):
                return redirect('user_list7')
            elif form.instance.shunxu == 2 and (10 <= form.instance.taiwei <= 18):
                return redirect('user_list8')
            elif form.instance.shunxu == 2 and (19 <= form.instance.taiwei <= 27):
                return redirect('user_list9')
            else:
                return redirect('user_list20')
    return render(request, "user_edit0.html",
                  {'form': form, 'current_url_name': current_url_name, "today": today, n: 'n'})


@csrf_exempt
def user_delete(request, nid1, nid2):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    instance1 = get_object_or_404(initial, taiwei=nid1, shunxu=nid2, todaytime=today)
    taiwei_display = instance1.get_taiwei_display()
    shunxu_display = instance1.get_shunxu_display()

    try:
        instance2 = bogie.objects.get(taiwei=nid1, shunxu=nid2, todaytime=today)
        instance2.delete()
    except ObjectDoesNotExist:
        pass  # instance2 不存在，所以什么也不做

    if request.method == 'POST':
        instance1.delete()
        # 记录用户的保存操作。假设用户已经登录，用户名已经保存在session中
        username = request.session.get("username", "unknown user")
        logger.info(
            f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}删除了{taiwei_display}{shunxu_display}的数据')
        return JsonResponse({'status': 'ok'})
    return render(request, 'user_delete.html', {'taiwei': nid1, 'shunxu': nid2})


class processedForm(ModelForm):
    class Meta:
        model = models.initial
        fields = ['xiucheng', 'chexing', 'nianxian', "beizhu"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


class processedForm1(ModelForm):
    class Meta:
        model = models.initial
        fields = ["beizhu"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


def shunxu(request):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    if request.method == 'POST':
        try:
            model_instance = order.objects.get(todaytime=today)
        except ObjectDoesNotExist:
            model_instance = order()
        line1 = request.POST.get('line1')
        line2 = request.POST.get('line2')
        line3 = request.POST.get('line3')
        # 检查是否有重复的值
        if len({line1, line2, line3}) != 3:
            return HttpResponse("保存失败：第一线, 第二线, 和 第三线 不能有重复的值")
        model_instance.gudao1 = request.POST.get('line1')
        model_instance.gudao2 = request.POST.get('line2')
        model_instance.gudao3 = request.POST.get('line3')
        model_instance.todaytime = today
        model_instance.save()
        messages.success(request, '修改成功！')
        username = request.session.get("username", "unknown user")
        logger.info(
            f'{username}{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}在架车班录入界面编辑了出车顺序。')
        return HttpResponseRedirect(reverse('user_add1'))
    else:
        return HttpResponseRedirect(reverse('user_add1'))


def shunxu1(request):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    if request.method == 'POST':
        try:
            model_instance = order.objects.get(todaytime=today)
        except ObjectDoesNotExist:
            model_instance = order()
        line1 = request.POST.get('line1')
        line2 = request.POST.get('line2')
        line3 = request.POST.get('line3')
        # 检查是否有重复的值
        if len({line1, line2, line3}) != 3:
            return HttpResponse("保存失败：第一线, 第二线, 和 第三线 不能有重复的值")
        model_instance.gudao1 = request.POST.get('line1')
        model_instance.gudao2 = request.POST.get('line2')
        model_instance.gudao3 = request.POST.get('line3')
        model_instance.todaytime = today
        model_instance.save()
        messages.success(request, '修改成功！')
        username = request.session.get("username", "unknown user")
        logger.info(
            f'{username}{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}在手持机录入界面编辑了出车顺序。')
        return HttpResponseRedirect(reverse('user_list4'))
    else:
        return HttpResponseRedirect(reverse('user_list4'))


def shunxu2(request):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    if request.method == 'POST':
        try:
            model_instance = order.objects.get(todaytime=today)
        except ObjectDoesNotExist:
            model_instance = order()
        line1 = request.POST.get('line1')
        line2 = request.POST.get('line2')
        line3 = request.POST.get('line3')
        # 检查是否有重复的值
        if len({line1, line2, line3}) != 3:
            return HttpResponse("保存失败：第一线, 第二线, 和 第三线 不能有重复的值")
        model_instance.gudao1 = request.POST.get('line1')
        model_instance.gudao2 = request.POST.get('line2')
        model_instance.gudao3 = request.POST.get('line3')
        model_instance.todaytime = today
        model_instance.save()
        messages.success(request, '修改成功！')
        username = request.session.get("username", "unknown user")
        logger.info(
            f'{username}{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}在轮轴班录入界面编辑了出车顺序。')
        return HttpResponseRedirect(reverse('user_add7'))
    else:
        return HttpResponseRedirect(reverse('user_add7'))


def shunxu3(request):
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    if request.method == 'POST':
        try:
            model_instance = order.objects.get(todaytime=today)
        except ObjectDoesNotExist:
            model_instance = order()
        line1 = request.POST.get('line1')
        line2 = request.POST.get('line2')
        line3 = request.POST.get('line3')
        # 检查是否有重复的值
        if len({line1, line2, line3}) != 3:
            return HttpResponse("保存失败：第一线, 第二线, 和 第三线 不能有重复的值")
        model_instance.gudao1 = request.POST.get('line1')
        model_instance.gudao2 = request.POST.get('line2')
        model_instance.gudao3 = request.POST.get('line3')
        model_instance.todaytime = today
        model_instance.save()
        messages.success(request, '修改成功！')
        username = request.session.get("username", "unknown user")
        logger.info(
            f'{username}{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}在台车班顺序修改界面编辑了出车顺序。')
        return HttpResponseRedirect(reverse('user_list10'))
    else:
        return HttpResponseRedirect(reverse('user_list10'))
    

@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add7(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(1, 10), shunxu=1, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    positions = [f"1-7-{i}" for i in range(1, 10)]
    positions_choices = [(i, f'1-7-{i}') for i in range(1, 10)]
    if request.method == 'GET':
        # 获取API车号数据
        car_number_map = {}
        car_r_type_map = {}
        car_type_map = {}
        try:
            resp = requests.get("http://127.0.0.1:10002/yxxxgx/api/car_type/")
            api_data = resp.json()
            for item in api_data:
                pos = item.get("position")
                car_num = item.get("car_number")
                car_r_type = item.get("car_r_type")
                car_type = item.get("car_type")
                if pos and car_num:
                    car_number_map[pos] = car_num
                    car_r_type_map[pos] = car_r_type
                    car_type_map[pos] = car_type
        except Exception as e:
            print("API获取异常：", e)

        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        # 按照positions顺序生成车号列表，对应每行
        car_numbers = [car_number_map.get(pos, '') for pos in positions]
        car_r_types = [car_r_type_map.get(pos, '') for pos in positions]
        car_types = [car_type_map.get(pos, '') for pos in positions]

        context = {
            'zipped_data': zipped_data,
            'car_numbers': car_numbers,
            'car_r_types': car_r_types,
            'car_types': car_types,
            'orders': orders,
            'formset': formset,
            'current_url_name': current_url_name,
            'today': today,
            'choices1': gudao1_choices,
            'choices2': gudao2_choices,
            'choices3': gudao3_choices
        }
        return render(request, '轮轴班信息采集界面1.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add7')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today,
               'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices}
    return render(request, '轮轴班信息采集界面1.html', context)


@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add8(request):
    """..."""
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(10, 19), shunxu=1, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"1-8-{i}" for i in range(1, 10)]
    positions_choices = [(num, f"1-8-{i}") for num, i in zip(range(10, 19), range(1, 10))]
    if request.method == 'GET':
        # 获取API车号数据
        car_number_map = {}
        car_r_type_map = {}
        car_type_map = {}
        try:
            resp = requests.get("http://127.0.0.1:10002/yxxxgx/api/car_type/")
            api_data = resp.json()
            for item in api_data:
                pos = item.get("position")
                car_num = item.get("car_number")
                car_r_type = item.get("car_r_type")
                car_type = item.get("car_type")
                if pos and car_num:
                    car_number_map[pos] = car_num
                    car_r_type_map[pos] = car_r_type
                    car_type_map[pos] = car_type
        except Exception as e:
            print("API获取异常：", e)

        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        # 按照positions顺序生成车号列表，对应每行
        car_numbers = [car_number_map.get(pos, '') for pos in positions]
        car_r_types = [car_r_type_map.get(pos, '') for pos in positions]
        car_types = [car_type_map.get(pos, '') for pos in positions]

        context = {
            'zipped_data': zipped_data,
            'car_numbers': car_numbers,
            'car_r_types': car_r_types,
            'car_types': car_types,
            'orders': orders,
            'formset': formset,
            'current_url_name': current_url_name,
            'today': today,
            'choices1': gudao1_choices,
            'choices2': gudao2_choices,
            'choices3': gudao3_choices
        }
        return render(request, '轮轴班信息采集界面2.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add8')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '轮轴班信息采集界面2.html', context)


@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add9(request):
    """..."""
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(19, 28), shunxu=1, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"1-9-{i}" for i in range(1, 10)]
    positions_choices = [(num, f"1-9-{i}") for num, i in zip(range(19, 28), range(1, 10))]
    if request.method == 'GET':
        # 获取API车号数据
        car_number_map = {}
        car_r_type_map = {}
        car_type_map = {}
        try:
            resp = requests.get("http://127.0.0.1:10002/yxxxgx/api/car_type/")
            api_data = resp.json()
            for item in api_data:
                pos = item.get("position")
                car_num = item.get("car_number")
                car_r_type = item.get("car_r_type")
                car_type = item.get("car_type")
                if pos and car_num:
                    car_number_map[pos] = car_num
                    car_r_type_map[pos] = car_r_type
                    car_type_map[pos] = car_type
        except Exception as e:
            print("API获取异常：", e)

        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        # 按照positions顺序生成车号列表，对应每行
        car_numbers = [car_number_map.get(pos, '') for pos in positions]
        car_r_types = [car_r_type_map.get(pos, '') for pos in positions]
        car_types = [car_type_map.get(pos, '') for pos in positions]

        context = {
            'zipped_data': zipped_data,
            'car_numbers': car_numbers,
            'car_r_types': car_r_types,
            'car_types': car_types,
            'orders': orders,
            'formset': formset,
            'current_url_name': current_url_name,
            'today': today,
            'choices1': gudao1_choices,
            'choices2': gudao2_choices,
            'choices3': gudao3_choices
        }
        return render(request, '轮轴班信息采集界面3.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add9')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '轮轴班信息采集界面3.html', context)


@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add10(request):
    """轮轴班添加数据"""
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(1, 10), shunxu=2, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"2-7-{i}" for i in range(1, 10)]
    positions_choices = [(num, f"2-7-{i}") for num, i in zip(range(1, 10), range(1, 10))]
    if request.method == 'GET':
        # 获取API车号数据
        car_number_map = {}
        car_r_type_map = {}
        car_type_map = {}
        try:
            resp = requests.get("http://127.0.0.1:10002/yxxxgx/api/car_type/")
            api_data = resp.json()
            for item in api_data:
                pos = item.get("position")
                car_num = item.get("car_number")
                car_r_type = item.get("car_r_type")
                car_type = item.get("car_type")
                if pos and car_num:
                    car_number_map[pos] = car_num
                    car_r_type_map[pos] = car_r_type
                    car_type_map[pos] = car_type
        except Exception as e:
            print("API获取异常：", e)

        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        # 按照positions顺序生成车号列表，对应每行
        car_numbers = [car_number_map.get(pos, '') for pos in positions]
        car_r_types = [car_r_type_map.get(pos, '') for pos in positions]
        car_types = [car_type_map.get(pos, '') for pos in positions]

        context = {
            'zipped_data': zipped_data,
            'car_numbers': car_numbers,
            'car_r_types': car_r_types,
            'car_types': car_types,
            'orders': orders,
            'formset': formset,
            'current_url_name': current_url_name,
            'today': today,
            'choices1': gudao1_choices,
            'choices2': gudao2_choices,
            'choices3': gudao3_choices
        }
        return render(request, '轮轴班信息采集界面4.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add10')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '轮轴班信息采集界面4.html', context)


@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add11(request):
    """轮轴班添加数据"""
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(10, 19), shunxu=2, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"2-8-{i}" for i in range(1, 10)]
    positions_choices = [(num, f"2-8-{i}") for num, i in zip(range(10, 19), range(1, 10))]
    if request.method == 'GET':
        # 获取API车号数据
        car_number_map = {}
        car_r_type_map = {}
        car_type_map = {}
        try:
            resp = requests.get("http://127.0.0.1:10002/yxxxgx/api/car_type/")
            api_data = resp.json()
            for item in api_data:
                pos = item.get("position")
                car_num = item.get("car_number")
                car_r_type = item.get("car_r_type")
                car_type = item.get("car_type")
                if pos and car_num:
                    car_number_map[pos] = car_num
                    car_r_type_map[pos] = car_r_type
                    car_type_map[pos] = car_type
        except Exception as e:
            print("API获取异常：", e)

        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        # 按照positions顺序生成车号列表，对应每行
        car_numbers = [car_number_map.get(pos, '') for pos in positions]
        car_r_types = [car_r_type_map.get(pos, '') for pos in positions]
        car_types = [car_type_map.get(pos, '') for pos in positions]

        context = {
            'zipped_data': zipped_data,
            'car_numbers': car_numbers,
            'car_r_types': car_r_types,
            'car_types': car_types,
            'orders': orders,
            'formset': formset,
            'current_url_name': current_url_name,
            'today': today,
            'choices1': gudao1_choices,
            'choices2': gudao2_choices,
            'choices3': gudao3_choices
        }
        return render(request, '轮轴班信息采集界面5.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add11')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '轮轴班信息采集界面5.html', context)


@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add12(request):
    """轮轴班添加数据"""
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(taiwei__in=range(19, 28), shunxu=2, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"2-9-{i}" for i in range(1, 10)]
    positions_choices = [(num, f"2-9-{i}") for num, i in zip(range(19, 28), range(1, 10))]
    if request.method == 'GET':
        # 获取API车号数据
        car_number_map = {}
        car_r_type_map = {}
        car_type_map = {}
        try:
            resp = requests.get("http://127.0.0.1:10002/yxxxgx/api/car_type/")
            api_data = resp.json()
            for item in api_data:
                pos = item.get("position")
                car_num = item.get("car_number")
                car_r_type = item.get("car_r_type")
                car_type = item.get("car_type")
                if pos and car_num:
                    car_number_map[pos] = car_num
                    car_r_type_map[pos] = car_r_type
                    car_type_map[pos] = car_type
        except Exception as e:
            print("API获取异常：", e)

        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        # 按照positions顺序生成车号列表，对应每行
        car_numbers = [car_number_map.get(pos, '') for pos in positions]
        car_r_types = [car_r_type_map.get(pos, '') for pos in positions]
        car_types = [car_type_map.get(pos, '') for pos in positions]

        context = {
            'zipped_data': zipped_data,
            'car_numbers': car_numbers,
            'car_r_types': car_r_types,
            'car_types': car_types,
            'orders': orders,
            'formset': formset,
            'current_url_name': current_url_name,
            'today': today,
            'choices1': gudao1_choices,
            'choices2': gudao2_choices,
            'choices3': gudao3_choices
        }
        return render(request, '轮轴班信息采集界面6.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add12')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '轮轴班信息采集界面6.html', context)


def user_add15(request):
    """..."""
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(shunxu=3, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm, extra=0)
    if request.method == 'GET':
        formset = ProcessedFormSet(queryset=rows)
        context = {'orders': orders,
                   'formset': formset, 'current_url_name': current_url_name, 'today': today}
        return render(request, '轮轴班信息采集界面8.html', context)
    formset = ProcessedFormSet(request.POST or None)
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_add15')
    else:
        print(formset.errors)
    context = {'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '轮轴班信息采集界面8.html', context)


class linxiuForm(ModelForm):
    class Meta:
        model = models.initial
        fields = ["taiwei", 'shunxu', 'chexing', 'nianxian', "lunjing1", "lunjing2", "lunjing3", "lunjing4"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


@allowed_users(['role1', 'role3', 'role19', 'role20'])
def user_add13(request):
    today = datetime.now().strftime("%Y-%m-%d")
    current_url_name = resolve(request.path_info).url_name
    orders = order.objects.filter(todaytime__date=today)
    if request.method == 'GET':
        form = linxiuForm()
        return render(request, "轮轴班信息采集界面7.html",
                      {"form": form, 'orders': orders, 'current_url_name': current_url_name, "today": today})

    form = linxiuForm(data=request.POST)
    if form.is_valid():
        taiwei = form.cleaned_data['taiwei']
        shunxu = form.cleaned_data['shunxu']

        # 为 initial 模型定义表单数据
        initial_data = {
            'taiwei': form.cleaned_data['taiwei'],
            'shunxu': form.cleaned_data['shunxu'],
            "xiucheng": 3,
            'chexing': form.cleaned_data['chexing'],
            'nianxian': form.cleaned_data['nianxian'],
            'lunjing1': form.cleaned_data['lunjing1'],
            'lunjing2': form.cleaned_data['lunjing2'],
            'lunjing3': form.cleaned_data['lunjing3'],
            'lunjing4': form.cleaned_data['lunjing4'],
            "todaytime": datetime.now().strftime("%Y-%m-%d"),
        }

        # 使用 update_or_create 更新 initial 的现有记录或创建新记录
        initial_obj, created = initial.objects.update_or_create(
            taiwei=taiwei, shunxu=shunxu, todaytime=today, defaults=initial_data
        )

        # 为 bogie 模型定义表单数据
        new_bogie_data = {
            'taiwei': form.cleaned_data['taiwei'],
            'shunxu': form.cleaned_data['shunxu'],
            'lunjing1': form.cleaned_data['lunjing1'],
            'lunjing2': form.cleaned_data['lunjing2'],
            'lunjing3': form.cleaned_data['lunjing3'],
            'lunjing4': form.cleaned_data['lunjing4'],
            'todaytime': datetime.now().strftime("%Y-%m-%d"),
        }
        #
        # # 使用 update_or_create 更新 bogie 的现有记录或创建新记录
        bogie_obj, created = bogie.objects.update_or_create(
            taiwei=new_bogie_data['taiwei'],
            shunxu=new_bogie_data['shunxu'],
            todaytime=new_bogie_data['todaytime'],
            defaults=new_bogie_data,
        )

        if not created:  # 只有在更新对象时设置 is_updated
            bogie.objects.filter(id=bogie_obj.id).update(**new_bogie_data, is_updated=True)
        username = request.session.get("username", "unknown user")
        taiwei_display = form.instance.get_taiwei_display()
        shunxu_display = form.instance.get_shunxu_display()
        logger.info(
            f'{username}在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}重新录入了{taiwei_display}{shunxu_display}的临修数据。')
        messages.success(request, "添加成功!")
        return redirect(reverse('user_add13'))
    else:
        messages.error(request, "表单验证失败，请检查数据是否符合要求。")
    return render(request, "轮轴班信息采集界面7.html",
                  {"form": form, 'orders': orders, 'current_url_name': current_url_name, "today": today})


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_list1(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "1"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)

    return render(request, '架车班信息查看界面1.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_list2(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "2"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)

    return render(request, '架车班信息查看界面2.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role2', 'role19', 'role20'])
def user_list3(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "3"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)

    return render(request, '架车班信息查看界面3.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list4(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         ]
    shunxu = "1"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)
    return render(request, '架车班信息手持机查看界面1.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today, 'orders': orders,
                   'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list5(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         ]
    shunxu = "1"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)

    return render(request, '架车班信息手持机查看界面2.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today,
                   'orders': orders, })


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list6(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "1"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)
    return render(request, '架车班信息手持机查看界面3.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today, 'orders': orders,
                   'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list7(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         ]
    shunxu = "2"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)
    return render(request, '架车班信息手持机查看界面4.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today, 'orders': orders,
                   'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list8(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         ]
    shunxu = "2"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)

    return render(request, '架车班信息手持机查看界面5.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today,
                   'orders': orders, })


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list9(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "2"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)
    return render(request, '架车班信息手持机查看界面6.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today, 'orders': orders,
                   'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices})


@allowed_users(['role1', 'role2', 'role5', 'role19', 'role20'])
def user_list20(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    orders = order.objects.filter(todaytime__date=today)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    shunxu = "3"
    position_data = {}
    for pos in positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data[pos] = get_data_for_position2(matched_number, today, shunxu)
    return render(request, '架车班信息手持机查看界面7.html',
                  {'positions': position_data, 'current_url_name': current_url_name, 'today': today, 'orders': orders,
                   'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices})


@allowed_users(['role1', 'role3', 'role4', 'role19', 'role20'])
def user_list10(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(shunxu=1, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm1, extra=0)
    gudao1_choices = order._meta.get_field('gudao1').choices
    gudao2_choices = order._meta.get_field('gudao2').choices
    gudao3_choices = order._meta.get_field('gudao3').choices
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    if request.method == 'GET':
        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
                   'current_url_name': current_url_name, 'today': today,
               'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices}
        return render(request, '台车班顺序编辑1.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_list10')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today,
               'choices1': gudao1_choices, 'choices2': gudao2_choices, 'choices3': gudao3_choices}
    return render(request, '台车班顺序编辑1.html', context)


@allowed_users(['role1', 'role3', 'role4', 'role19', 'role20'])
def user_list11(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(shunxu=2, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm1, extra=0)
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    if request.method == 'GET':
        formset = ProcessedFormSet(queryset=rows)
        form_dict = {str(form.instance.taiwei): form for form in formset}
        sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
        zipped_data = list(zip(positions, sorted_forms))
        context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
                   'current_url_name': current_url_name, 'today': today}
        return render(request, '台车班顺序编辑2.html', context)

    formset = ProcessedFormSet(request.POST or None)
    form_dict = {str(form.instance.taiwei): form for form in formset}
    sorted_forms = [form_dict.get(str(choice[0]), None) for choice in positions_choices]
    zipped_data = list(zip(positions, sorted_forms))
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_list11')
    else:
        print(formset.errors)
    context = {'zipped_data': zipped_data, 'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '台车班顺序编辑2.html', context)


@allowed_users(['role1', 'role3', 'role4', 'role19', 'role20'])
def user_list12(request):
    current_url_name = resolve(request.path_info).url_name
    Datetime = datetime.now()
    today = Datetime.strftime("%Y-%m-%d")
    orders = order.objects.filter(todaytime__date=today)
    rows = models.initial.objects.filter(shunxu=3, todaytime=today)
    ProcessedFormSet = modelformset_factory(models.initial, form=processedForm1, extra=0)
    if request.method == 'GET':
        formset = ProcessedFormSet(queryset=rows)
        context = {'orders': orders,
                   'formset': formset, 'current_url_name': current_url_name, 'today': today}
        return render(request, '台车班顺序编辑3.html', context)
    formset = ProcessedFormSet(request.POST or None)
    if formset.is_valid():
        instances = formset.save(commit=False)
        for obj in instances:
            obj.save()
        messages.success(request, '添加成功！')
        return redirect('user_list12')
    else:
        print(formset.errors)
    context = {'orders': orders, 'formset': formset,
               'current_url_name': current_url_name, 'today': today}
    return render(request, '台车班顺序编辑3.html', context)


def user_list13(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    shunxu = "1"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data2.get(pos),
                "data2": position_data1.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data1'].beizhu, x['position']))
            if x['data']['data1'] and x['data']['data1'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )

    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']

    context = {
        'highlight_list': highlight_list,
        'data_list': data_list,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today,
        'today1': today1,
    }
    return render(request, '轮轴班一次出库信息展示界面.html', context)


def user_list14(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    shunxu = "2"
    position_data1 = {}
    position_data2 = {}
    combined_positions = {}
    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, shunxu)
            position_data2[pos] = get_data_for_position2(matched_number, today, shunxu)
            combined_positions[pos] = {
                "data1": position_data2.get(pos),
                "data2": position_data1.get(pos)
            }
    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data1'].beizhu, x['position']))
            if x['data']['data1'] and x['data']['data1'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )
    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']

    context = {
        'highlight_list': highlight_list,
        'data_list': data_list,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today,
        'today1': today1,
    }
    return render(request, '轮轴班二次出库信息展示界面.html', context)


def user_list19(request):
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    data = models.initial.objects.filter(shunxu=3, todaytime=today)
    data1 = models.bogie.objects.filter(todaytime=today)
    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']

    combined_data = []
    for d in data:
        d1 = data1.filter(taiwei=d.taiwei,
                          shunxu=d.shunxu).first()  # Assuming taiwei and shunxu are the matching fields
        combined_data.append({'initial': d, 'bogie': d1})

    context = {
        'highlight_list': highlight_list,
        'combined_data': combined_data,
        'today': today,
        'today1': today1,
    }
    return render(request, '轮轴班三次出库信息展示界面.html', context)


def user_list15(request):
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    data = models.initial.objects.filter(xiucheng=3, todaytime=today)
    data1 = models.bogie.objects.filter(todaytime=today)
    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']

    combined_data = []
    for d in data:
        d1 = data1.filter(taiwei=d.taiwei,
                          shunxu=d.shunxu).first()  # Assuming taiwei and shunxu are the matching fields
        combined_data.append({'initial': d, 'bogie': d1})

    context = {
        'highlight_list': highlight_list,
        'combined_data': combined_data,
        'today': today,
        'today1': today1,
    }
    return render(request, '轮轴班临修信息展示界面.html', context)


def user_list16(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    position_data1 = {}
    position_data2 = {}
    position_data3 = {}
    position_data4 = {}

    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, "1")
            position_data2[pos] = get_data_for_position2(matched_number, today, "1")
            position_data3[pos] = get_data_for_position1(matched_number, today, "2")
            position_data4[pos] = get_data_for_position2(matched_number, today, "2")

    combined_positions = {}
    for pos in ordered_positions:
        combined_positions[pos] = {
            "data1": position_data1.get(pos),
            "data2": position_data2.get(pos),
            "data3": position_data3.get(pos),
            "data4": position_data4.get(pos)
        }

    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list1 = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data2'].beizhu, x['position']))
            if x['data']['data2'] and x['data']['data2'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )
    data_list2 = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data4'].beizhu, x['position']))
            if x['data']['data4'] and x['data']['data4'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )
    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']

    context = {
        'data_list1': data_list1,
        'data_list2': data_list2,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today,
        'today1': today1,
        'highlight_list': highlight_list,
    }
    return render(request, '台车班一次出库信息展示界面.html', context)


def user_list17(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    position_data1 = {}
    position_data2 = {}
    position_data3 = {}
    position_data4 = {}

    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, "1")
            position_data2[pos] = get_data_for_position2(matched_number, today, "1")
            position_data3[pos] = get_data_for_position1(matched_number, today, "2")
            position_data4[pos] = get_data_for_position2(matched_number, today, "2")

    combined_positions = {}
    for pos in ordered_positions:
        combined_positions[pos] = {
            "data1": position_data1.get(pos),
            "data2": position_data2.get(pos),
            "data3": position_data3.get(pos),
            "data4": position_data4.get(pos)
        }

    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list1 = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data2'].beizhu, x['position']))
            if x['data']['data2'] and x['data']['data2'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )
    data_list2 = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data4'].beizhu, x['position']))
            if x['data']['data4'] and x['data']['data4'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )
    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']
    context = {
        'data_list1': data_list1,
        'data_list2': data_list2,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today,
        'today1': today1,
        'highlight_list': highlight_list,
    }
    return render(request, '台车班二次出库信息展示界面.html', context)


def user_list18(request):
    current_url_name = resolve(request.path_info).url_name
    today = datetime.now().strftime("%Y-%m-%d")
    today1 = datetime.now().strftime("%Y年%m月%d日%H:%M")
    positions = [f"{i}-{j}" for i in range(7, 10) for j in range(1, 10)]
    positions_choices = [(1, '7-1'), (2, '7-2'), (3, '7-3'), (4, '7-4'), (5, '7-5'), (6, '7-6'), (7, '7-7'), (8, '7-8'),
                         (9, '7-9'),
                         (10, '8-1'), (11, '8-2'), (12, '8-3'), (13, '8-4'), (14, '8-5'), (15, '8-6'), (16, '8-7'),
                         (17, '8-8'), (18, '8-9'),
                         (19, '9-1'), (20, '9-2'), (21, '9-3'), (22, '9-4'), (23, '9-5'), (24, '9-6'), (25, '9-7'),
                         (26, '9-8'), (27, '9-9'),
                         ]
    try:
        order_object = order.objects.get(todaytime=today)
    except order.DoesNotExist:
        order_object = order(todaytime=today, gudao1="9", gudao2="7", gudao3="8")
        order_object.save()
    gudao1 = str(order_object.gudao1)
    gudao2 = str(order_object.gudao2)
    gudao3 = str(order_object.gudao3)
    gudao_order = [gudao1, gudao2, gudao3]
    ordered_positions = sorted(positions, key=lambda x: (gudao_order.index(x.split("-")[0]), x))
    position_data1 = {}
    position_data2 = {}
    for pos in ordered_positions:
        matched_number = next((number for number, position in positions_choices if position == pos), None)
        if matched_number is not None:
            position_data1[pos] = get_data_for_position1(matched_number, today, "3")
            position_data2[pos] = get_data_for_position2(matched_number, today, "3")

    combined_positions = {}
    for pos in ordered_positions:
        combined_positions[pos] = {
            "data1": position_data1.get(pos),
            "data2": position_data2.get(pos),
        }

    data_list = [{'position': position, 'data': data} for position, data in combined_positions.items()]

    order_map = {
        1: '7-0',
        2: '7-1.5',
        3: '7-2.5',
        4: '7-3.5',
        5: '7-4.5',
        6: '7-5.5',
        7: '7-6.5',
        8: '7-7.5',
        9: '7-8.5',
        10: '7-9.5',
        11: '8-0',
        12: '8-1.5',
        13: '8-2.5',
        14: '8-3.5',
        15: '8-4.5',
        16: '8-5.5',
        17: '8-6.5',
        18: '8-7.5',
        19: '8-8.5',
        20: '8-9.5',
        21: '9-0',
        22: '9-1.5',
        23: '9-2.5',
        24: '9-3.5',
        25: '9-4.5',
        26: '9-5.5',
        27: '9-6.5',
        28: '9-7.5',
        29: '9-8.5',
        30: '9-9.5',
    }
    order_list = [f"{gudao}-{float(j / 2):.1f}".rstrip('0').rstrip('.') for gudao in gudao_order for j in range(0, 20)]
    data_list1 = sorted(
        data_list,
        key=lambda x: (
            order_list.index(order_map.get(x['data']['data2'].beizhu, x['position']))
            if x['data']['data2'] and x['data']['data2'].beizhu is not None
            else order_list.index(x['position']),
            x['position']
        )
    )
    highlight_list = ['P70', 'C70', 'C70E', 'C70EH', 'C70H', 'GL70', 'GQ70', 'GQ70A', 'GW70', 'NX70', 'NX70A', 'NX70AF',
                      'NX70H', 'NX70F', 'X70', 'KZ70', 'JSQ6', 'NX70-F']
    context = {
        'data_list1': data_list1,
        'ordered_positions': ordered_positions,
        'current_url_name': current_url_name,
        'today': today,
        'today1': today1,
        'highlight_list': highlight_list,
    }
    return render(request, '台车班三次出库信息展示界面.html', context)


def check_if_user_is_logged_in(request):
    return "username" in request.session


class tasksForm(ModelForm):
    class Meta:
        model = models.tasks
        fields = ["guotie1", "guotie4", "guotie7", "guotie8", "pengche1", "pengche3", "changche1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


class tasksForm1(ModelForm):
    class Meta:
        model = models.tasks
        fields = ["duanxiu1", "duanxiu2", "duanxiu3", "duanxiu4", "duanxiu5", "duanxiu6", "changxiu1", "changxiu2",
                  "changxiu3", "changxiu4", "heji1", "heji2", "diban1", "diban2", "TgaiK", "linxiu"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # if name == "datatime":
            #     continue
            if field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs = {
                    'class': 'form-control'
                }


def ddd(request):
    get_and_save_data(request)
    global laodong
    logged_in = check_if_user_is_logged_in(request)
    if logged_in:
        admin = request.session['info']['id']
        role = request.session['info']['role']
        chejian = request.session['info']['chejian']
        banzu = request.session['info']['banzu']

        # 获取事务数据
        if chejian == 0:
            transactions = Transactions.objects.all().order_by("-id")[:20]
        else:
            transactions = Transactions.objects.filter(chejian=chejian).order_by("-id")[:20]

        # 获取传阅数据
        if banzu == 13:
            if chejian == 0:
                circulates = Circulates.objects.filter(status=0).distinct().order_by('-create_time')[:20]
            else:
                # 根据车间确定班组
                if chejian == 1:
                    banzu_list = [2, 3, 6, 7, 12]  # 修配车间
                elif chejian == 2:
                    banzu_list = [1, 4, 5, 8, 9, 10]  # 修车车间
                else:
                    banzu_list = []  # 其他情况
                circulates = Circulates.objects.filter(status=0, circulatereads__user__banzu__in=banzu_list
                                                       ).distinct().order_by('-create_time')[:20]
        else:
            current_banzu_users = TeamUser.objects.filter(banzu=banzu, retire=1)
            circulates = Circulates.objects.filter(
                status=0,
                circulatereads__user__in=current_banzu_users
            ).distinct().order_by('-create_time')[:20]

        # 组合事务和传阅数据
        combined_data = []
        for trans in transactions:
            combined_data.append({
                'type': 'transaction',
                'data': trans,
                'time': trans.todaytime,
                'unread': not TransactionReads.objects.filter(transaction=trans, admin=admin, read=True).exists(),
                'attachment': TransactionAttachment.objects.filter(transaction=trans).exists()
            })

        # 获取当前班组的所有成员
        if banzu == 13:
            if chejian == 0:
                current_banzu_users = TeamUser.objects.filter(retire=1)
            else:
                # 根据车间确定班组
                if chejian == 1:
                    banzu_list = [2, 3, 6, 7, 12]  # 修配车间
                elif chejian == 2:
                    banzu_list = [1, 4, 5, 8, 9, 10]  # 修车车间
                else:
                    banzu_list = []  # 其他情况
                current_banzu_users = TeamUser.objects.filter(banzu__in=banzu_list, retire=1)
        else:
            current_banzu_users = TeamUser.objects.filter(banzu=banzu, retire=1)

        # 添加传阅的未读人数统计
        circulate_stats = {}
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
            circulate_stats[circulate.id] = {
                'total_reads': total_reads,
                'unread_count': unread_count
            }

        # 添加传阅数据到combined_data
        for circ in circulates:
            stats = circulate_stats[circ.id]
            combined_data.append({
                'type': 'circulate',
                'data': circ,
                'time': circ.create_time,
                'unread': stats['unread_count'] > 0,
                'attachment': circ.attachments.exists(),
                'total_reads': stats['total_reads'],
                'unread_count': stats['unread_count']
            })

        # 按时间排序
        combined_data.sort(key=lambda x: x['time'], reverse=True)

        # 获取未检查人员名单
        # today = date.today()
        # unchecked_people_names = []
        # p_list = JkrqList.objects.filter(time__year=datetime.now().year, people_type='JKWH')
        # o_list = JkrqList.objects.filter(time__year=datetime.now().year - 1, people_type='XNXGJB')
        #
        # if banzu == 13:
        #     if chejian == 1:
        #         p_list = p_list.filter(banzu__in=[2, 3, 6, 7, 11, 12])
        #         o_list = o_list.filter(banzu__in=[2, 3, 6, 7, 11, 12])
        #     elif chejian == 2:
        #         p_list = p_list.filter(banzu__in=[1, 4, 5, 8, 9, 10])
        #         o_list = o_list.filter(banzu__in=[1, 4, 5, 8, 9, 10])
        #     else:
        #         p_list = JkrqList.objects.none()
        #         o_list = JkrqList.objects.none()
        # else:
        #     p_list = p_list.filter(banzu=banzu)
        #     o_list = o_list.filter(banzu=banzu)
        #
        # for jkrqList in p_list | o_list:
        #     if jkrqList.people_check_method == 'DAYLY':
        #         q_object = Q(people=jkrqList, check_date=today)
        #     elif jkrqList.people_check_method == 'WEEKLY':
        #         start_week = today - timedelta(days=today.weekday())
        #         end_week = start_week + timedelta(days=6)
        #         q_object = Q(people=jkrqList, check_date__range=[start_week, end_week])
        #     elif jkrqList.people_check_method == 'MONTHLY':
        #         q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)
        #     elif jkrqList.people_check_method == 'QUARTER':
        #         current_month = today.month
        #         if current_month in [1, 2, 3]:
        #             quarter_start = date(today.year, 1, 1)
        #             quarter_end = date(today.year, 3, 31)
        #         elif current_month in [4, 5, 6]:
        #             quarter_start = date(today.year, 4, 1)
        #             quarter_end = date(today.year, 6, 30)
        #         elif current_month in [7, 8, 9]:
        #             quarter_start = date(today.year, 7, 1)
        #             quarter_end = date(today.year, 9, 30)
        #         else:  # 10,11,12
        #             quarter_start = date(today.year, 10, 1)
        #             quarter_end = date(today.year, 12, 31)
        #         q_object = Q(people=jkrqList, check_date__range=[quarter_start, quarter_end])
        #     else:
        #         q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)
        #
        #     logs = JkrqList1Log.objects.filter(q_object)
        #
        #     if not logs.exists():
        #         unchecked_people_names.append(jkrqList.name)
    else:
        combined_data = []
        unchecked_people_names = []

    # 获取最新事务或传阅的时间
    latest_time = None
    if combined_data:
        latest_time = combined_data[0]['time']  # 已经按时间排序，取第一个就是最新的
    else:
        latest_time = datetime.now()

    first_task = tasks.objects.first()
    form = tasksForm(instance=first_task)
    form1 = tasksForm1(instance=first_task)

    date_string1 = first_task.time1.strftime("%Y-%m-%d")
    start_date1 = datetime.strptime(date_string1, "%Y-%m-%d")
    date_string2 = first_task.time2.strftime("%Y-%m-%d")
    start_date2 = datetime.strptime(date_string2, "%Y-%m-%d")
    date_string3 = first_task.time3.strftime("%Y-%m-%d")
    start_date3 = datetime.strptime(date_string3, "%Y-%m-%d")
    now = datetime.today()
    logged_in = check_if_user_is_logged_in(request)
    days1 = (now - start_date1).days
    days2 = (now - start_date2).days
    days3 = (now - start_date3).days
    laodong = days1
    xingche = days2
    guzhang = days3

    if request.method == "GET":
        data = tasks.objects.first()
        shengyu1 = data.guotie1 - data.guotie2
        shengyu2 = data.guotie4 - data.guotie5
        shengyu3 = data.pengche1 - data.pengche2
        shengyu4 = data.pengche3 - data.pengche4
        shengyu5 = data.changche1 - data.changche2
        shengyu6 = data.changxiu1 - data.changxiu2
        shengyu7 = data.duanxiu1 - data.duanxiu2

        bili1 = 100 if data.guotie1 == 0 else data.guotie2 / data.guotie1 * 100
        bili2 = 100 - bili1
        bili3 = 100 if data.guotie4 == 0 else data.guotie5 / data.guotie4 * 100
        bili4 = 100 - bili3
        bili5 = 100 if data.pengche1 == 0 else data.pengche2 / data.pengche1 * 100
        bili6 = 100 - bili5
        bili7 = 100 if data.pengche3 == 0 else data.pengche4 / data.pengche3 * 100
        bili8 = 100 - bili7
        bili9 = 100 if data.changche1 == 0 else data.changche2 / data.changche1 * 100
        bili10 = 100 - bili9

        context = {
            'first_task': first_task,
            "latest_year": latest_time.year,
            "latest_month": latest_time.month,
            'form': form,
            'form1': form1,
            'combined_data': combined_data,
            'logged_in': logged_in,
            'laodong': laodong,
            'xingche': xingche,
            'guzhang': guzhang,
            'data': data,
            'shengyu1': shengyu1,
            'shengyu2': shengyu2,
            'shengyu3': shengyu3,
            'shengyu4': shengyu4,
            'shengyu5': shengyu5,
            'shengyu6': shengyu6,
            'shengyu7': shengyu7,
            'bili1': bili1,
            'bili2': bili2,
            'bili3': bili3,
            'bili4': bili4,
            'bili5': bili5,
            'bili6': bili6,
            'bili7': bili7,
            'bili8': bili8,
            'bili9': bili9,
            'bili10': bili10,
            # 'unchecked_people_names': unchecked_people_names,
        }
        return render(request, "1.html", context)


def shijian(request):
    if request.method == 'POST':
        model_instance = tasks.objects.get(id=1)  # 获取已存在的任务对象
        model_instance.time1 = request.POST.get('newLaodong')
        model_instance.time2 = request.POST.get('newXingche')
        model_instance.time3 = request.POST.get('newGuzhang')
        model_instance.save()  # 保存更改
        # messages.success(request, '修改成功！')
        return HttpResponseRedirect(reverse('1'))
    else:
        return HttpResponseRedirect(reverse('1'))


def jihua(request):
    first_task = tasks.objects.get(id=1)
    if request.method == 'POST':
        form = tasksForm(request.POST, instance=first_task)
        if form.is_valid():
            form.save()
            url = 'http://127.0.0.1:10004/get_plandata/'
            params = {'key1': 'value1', 'key2': 'value2'}  # 可选参数

            response = requests.get(url, params=params)

            if response.status_code == 200:
                print("请求成功！")
                print("响应内容：", response.text)
            else:
                print("请求失败，状态码：", response.status_code)
            return HttpResponseRedirect(reverse('1'))
    else:
        form = tasksForm(instance=first_task)
    return render(request, '1.html', {'form': form})


def jihua1(request):
    first_task = tasks.objects.get(id=1)
    if request.method == 'POST':
        form = tasksForm1(request.POST, instance=first_task)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('1'))
    else:
        form = tasksForm1(instance=first_task)
    return render(request, '1.html', {'form': form})


def shiwu(request):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    if request.method == 'POST':
        shiwubiaoti = request.POST.get('shiwubiaoti')
        user = request.POST.get('user')
        chejian = request.POST.get('chejian')
        shiwuneirong = request.POST.get('shiwuneirong')
        Transactions.objects.create(shiwubiaoti=shiwubiaoti, user=user, chejian=chejian, shiwuneirong=shiwuneirong,
                                    todaytime=today)
        return HttpResponseRedirect(reverse('1'))
    else:
        return HttpResponseRedirect(reverse('1'))


def get_transaction(request, id):
    transaction = get_object_or_404(Transactions, id=id)
    transactions = Transactions.objects.order_by('-todaytime')
    years_months = []
    for year, year_transactions in groupby(transactions, key=attrgetter('todaytime.year')):
        year_transactions = list(year_transactions)
        months = []
        for month, month_transactions in groupby(year_transactions, key=attrgetter('todaytime.month')):
            months.append({
                'month': month,
                'transactions': list(month_transactions)
            })
        years_months.append({
            'year': year,
            'months': months,
        })
    context = {
        'years_months': years_months,
        'transaction': transaction,
        'year': transaction.todaytime.year,
        'month': transaction.todaytime.month,
    }
    return context


def transaction_detail(request, id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)

    admin_id = request.session['info']['id']
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    admin = Admin.objects.get(id=admin_id)
    transaction = get_object_or_404(Transactions, id=id)
    attachments = TransactionAttachment.objects.filter(transaction=transaction)

    if admin.role in (role_choice[0] for role_choice in Admin.ROLE_CHOICES):
        try:
            transaction_reads = TransactionReads.objects.get(transaction=transaction, admin=admin)
        except ObjectDoesNotExist:
            TransactionReads.objects.create(transaction=transaction, admin=admin, read=True)
        else:
            transaction_reads.read = True
            transaction_reads.save()

    # 获取所有事务数据用于导航栏
    all_transactions = Transactions.objects.filter(chejian=chejian).order_by('-todaytime')
    all_circulates = Circulates.objects.all().distinct().order_by('-create_time')
    if chejian != 0:
        all_circulates = all_circulates.filter(chejian=chejian)

    # 获取当前年月
    current_year = transaction.todaytime.year
    current_month = transaction.todaytime.month

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

    # 获取事务的阅读状态
    all_admins = Admin.objects.exclude(
        Q(username='admin') | Q(username='jiache') | Q(username='lunzhou') | Q(username='taiche') |
        Q(username='shouchiji') | Q(username='LZSCJ') | Q(username='xpcj') | Q(username='zjb') |
        Q(username='xccj')).filter(chejian=chejian)
    admins_read = []
    admins_not_read = []
    admin_reads = []
    for admin in all_admins:
        try:
            transaction_read = TransactionReads.objects.get(transaction=transaction, admin=admin)
            if transaction_read.read:
                admins_read.append(admin.get_role_display())
            else:
                display = admin.get_role_display() or admin.username  # 或者用 admin.role
                admins_not_read.append(str(display))
            admin_reads.append({'admin': admin.get_role_display(), 'read': transaction_read.read})
        except ObjectDoesNotExist:
            display = admin.get_role_display() or admin.username  # 或者用 admin.role
            admins_not_read.append(str(display))
            admin_reads.append({'admin': admin.get_role_display(), 'read': False})

    context = {
        'transaction': transaction,
        'attachments': attachments,
        'year': current_year,
        'month': current_month,
        'admin_reads': admin_reads,
        'admins_read': ', '.join(admins_read),
        'admins_not_read': ', '.join(admins_not_read),
        'role': role,
        'banzu': banzu,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'combined_years': combined_years  # 添加导航栏数据
    }
    return render(request, 'transaction_detail.html', context)


@csrf_exempt
def delete_transaction(request, id):
    instance = get_object_or_404(Transactions, id=id)
    if request.method == 'POST':
        TransactionReads.objects.filter(transaction=instance).delete()
        instance.delete()
        return JsonResponse({'status': 'ok'})
    return render(request, 'Transactions.html')


class TransactionsForm(ModelForm):
    class Meta:
        model = models.Transactions
        fields = ['shiwubiaoti', 'user', 'shiwuneirong']
        widgets = {
            'shiwuneirong': CKEditorUploadingWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ["shiwubiaoti", "user"]:
                field.widget = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def add_transaction(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)
    role = request.session['info']['role']
    chejian = request.session['info']['chejian']
    if request.method == 'POST':
        form = TransactionsForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.chejian = chejian
            transaction.todaytime = datetime.now()
            transaction.save()

            for file in request.FILES.getlist('attachments'):
                TransactionAttachment.objects.create(transaction=transaction, file=file)

            messages.success(request, '添加成功')
            return redirect('transaction_detail', id=transaction.id)  # redirect to the list of transactions
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:  # request.method == 'GET'
        form = TransactionsForm()
    return render(request, 'transaction_add.html', {'form': form, 'role': role, "admin": ADMIN,
                                                    "xiuche": XIUCHE,
                                                    "xiupei": XIUPEI, })


@csrf_exempt
def edit_transaction(request, id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)
    role = request.session['info']['role']
    chejian = request.session['info']['chejian']
    context = get_transaction(request, id)
    transaction = get_object_or_404(Transactions, id=id)
    attachments = TransactionAttachment.objects.filter(transaction=transaction)
    transactions = Transactions.objects.order_by('-todaytime')
    years_months = []
    for year, year_transactions in groupby(transactions, key=attrgetter('todaytime.year')):
        year_transactions = list(year_transactions)
        months = []
        for month, month_transactions in groupby(year_transactions, key=attrgetter('todaytime.month')):
            months.append({
                'month': month,
                'transactions': list(month_transactions)
            })
        years_months.append({
            'year': year,
            'months': months,
        })
    if request.method == 'POST':
        form = TransactionsForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.chejian = chejian
            transaction.save()
            attachments_to_delete = request.POST.getlist('attachments_to_delete')
            TransactionAttachment.objects.filter(id__in=attachments_to_delete).delete()
            messages.success(request, '修改成功')
            for file in request.FILES.getlist('attachments'):
                TransactionAttachment.objects.create(transaction=transaction, file=file)
            return redirect('/transaction/{}'.format(transaction.pk))
    else:
        form = TransactionsForm(instance=transaction)

    return render(request, 'transaction_edit.html', {'form': form, 'id': id, 'attachments': attachments,
                                                     'years_months': years_months, 'context': context, 'role': role,
                                                     "admin": ADMIN,
                                                     "xiuche": XIUCHE,
                                                     "xiupei": XIUPEI, })


def transactions(request, year, month):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)

    role = request.session['info']['role']
    admin_id = request.session['info']['id']
    chejian = request.session['info']['chejian']
    banzu = request.session['info']['banzu']

    admin = Admin.objects.get(id=admin_id)
    read_transactions = TransactionReads.objects.filter(admin=admin, read=True).values_list('transaction', flat=True)

    # 获取所有事务数据
    all_transactions = Transactions.objects.filter(chejian=chejian).order_by('-todaytime')

    # 获取传阅数据
    current_banzu_users = TeamUser.objects.filter(retire=1)
    if banzu != 13:
        current_banzu_users = current_banzu_users.filter(banzu=banzu)

    # 获取所有传阅数据
    if banzu == 13:
        all_circulates = Circulates.objects.all().distinct().order_by('-create_time')
        if chejian != 0:
            all_circulates = all_circulates.filter(chejian=chejian)
    else:
        all_circulates = Circulates.objects.filter(circulatereads__user__in=current_banzu_users).distinct().order_by(
            '-create_time')

    # 获取当前年月的数据
    current_transactions = all_transactions.filter(
        todaytime__year=year,
        todaytime__month=month
    )
    current_circulates = all_circulates.filter(
        create_time__year=year,
        create_time__month=month
    )

    # 添加未读人数统计
    circulate_stats = {}
    for circulate in all_circulates:
        total_reads = CirculateReads.objects.filter(
            circulate=circulate,
            user__in=current_banzu_users
        ).count()
        unread_count = CirculateReads.objects.filter(
            circulate=circulate,
            read=False,
            user__in=current_banzu_users
        ).count()
        circulate_stats[circulate.id] = {
            'total_reads': total_reads,
            'unread_count': unread_count
        }

    # 将所有数据合并用于导航栏
    all_combined_data = []
    for trans in all_transactions:
        all_combined_data.append({
            'type': 'transaction',
            'data': trans,
            'time': trans.todaytime,
            'unread': not trans.id in read_transactions,
            'attachment': TransactionAttachment.objects.filter(transaction=trans).exists()
        })
    for circ in all_circulates:
        stats = circulate_stats[circ.id]
        all_combined_data.append({
            'type': 'circulate',
            'data': circ,
            'time': circ.create_time,
            'unread': stats['unread_count'] > 0,
            'attachment': circ.attachments.exists(),
            'total_reads': stats['total_reads'],
            'unread_count': stats['unread_count']
        })
    all_combined_data.sort(key=lambda x: x['time'], reverse=True)

    # 将当前年月的数据合并用于页面显示
    combined_data = []
    for trans in current_transactions:
        combined_data.append({
            'type': 'transaction',
            'data': trans,
            'time': trans.todaytime,
            'unread': not trans.id in read_transactions,
            'attachment': TransactionAttachment.objects.filter(transaction=trans).exists()
        })
    for circ in current_circulates:
        stats = circulate_stats[circ.id]
        combined_data.append({
            'type': 'circulate',
            'data': circ,
            'time': circ.create_time,
            'unread': stats['unread_count'] > 0,
            'attachment': circ.attachments.exists(),
            'total_reads': stats['total_reads'],
            'unread_count': stats['unread_count']
        })
    combined_data.sort(key=lambda x: x['time'], reverse=True)

    # 按年月分组所有数据用于导航栏
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

    # 按月份分组显示当前年月的数据
    month_data = []
    current_month = None
    current_month_items = []
    for item in combined_data:
        item_month = item['time'].month
        if item_month != current_month:
            if current_month_items:
                month_data.append({
                    'month': current_month,
                    'items': current_month_items
                })
            current_month = item_month
            current_month_items = []
        current_month_items.append(item)
    if current_month_items:
        month_data.append({
            'month': current_month,
            'items': current_month_items
        })

    context = {
        'year': year,
        'month': month,
        'role': role,
        'banzu': banzu,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'month_data': month_data,
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'combined_years': combined_years,
        'xiuche_banzu': XIUCHE_BANZU,
        'xiupei_banzu': XIUPEI_BANZU,
        'banzu_choices': TeamUser.banzu_choices,
        'classification_choices': Circulates.classification_choices,
    }
    return render(request, "Transactions.html", context)


def procedures(request):
    return render(request, "procedures.html")


@csrf_exempt
def upload_files(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '作业指导书')
        rel_path = request.POST.get('current_path', '')
        target_dir = os.path.join(base_dir, rel_path)

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                # 检查文件类型
                if not file.name.lower().endswith(('.pdf', '.mp4')):
                    failed_files.append({
                        'name': file.name,
                        'error': '文件类型不支持'
                    })
                    continue

                # 检查文件大小
                if file.size > 104857600:  # 100MB
                    failed_files.append({
                        'name': file.name,
                        'error': '文件大小超过限制'
                    })
                    continue

                # 保存文件
                file_path = os.path.join(target_dir, file.name)

                # 检查文件是否已存在
                if os.path.exists(file_path):
                    failed_files.append({
                        'name': file.name,
                        'error': '文件已存在'
                    })
                    continue

                with open(file_path, 'wb') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                uploaded_files.append(file.name)
            except Exception as e:
                failed_files.append({
                    'name': file.name,
                    'error': str(e)
                })

        # 返回详细的状态信息
        return JsonResponse({
            'status': 'success' if not failed_files else 'partial',
            'uploaded': uploaded_files,
            'failed': failed_files,
            'target_dir': target_dir
        })


@csrf_exempt
def create_folder(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        folder_name = data.get('folder_name', '')
        base_dir = r'.\作业指导书'
        current_path = data.get('current_path', '')
        target_dir = os.path.join(base_dir, current_path, folder_name)

        try:
            if not folder_name:
                return JsonResponse({'status': 'error', 'message': '文件夹名称不能为空'})

            if os.path.exists(target_dir):
                return JsonResponse({'status': 'error', 'message': '文件夹已存在'})

            os.makedirs(target_dir)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def rename_item(request):
    # 权限校验
    info = request.session.get("info")
    if not info or str(info.get('banzu')) != "13":
        return JsonResponse({
            'status': 'error',
            'message': '您没有操作权限，请登录管理员帐号后再尝试修改。'
        }, status=403)

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        old_path = data.get('old_path', '')
        new_name = data.get('new_name', '')
        base_dir = r'.\作业指导书'
        try:
            if not new_name:
                return JsonResponse({'status': 'error', 'message': '新名称不能为空'})
            old_full_path = os.path.join(base_dir, old_path)
            new_full_path = os.path.join(os.path.dirname(old_full_path), new_name)
            if not os.path.exists(old_full_path):
                return JsonResponse({'status': 'error', 'message': '原文件/文件夹不存在'})
            if os.path.exists(new_full_path):
                return JsonResponse({'status': 'error', 'message': '新名称已存在'})
            os.rename(old_full_path, new_full_path)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def delete_files(request):
    # 权限校验
    info = request.session.get("info")
    if not info or str(info.get('banzu')) != "13":
        return JsonResponse({
            'status': 'error',
            'message': '您没有操作权限，请登录管理员帐号后再尝试修改。'
        }, status=403)

    if request.method == 'POST':
        data = request.body.decode('utf-8')
        try:
            files = json.loads(data).get('files', [])
            base_dir = r'.\作业指导书'
            for rel_path in files:
                abs_path = os.path.join(base_dir, rel_path)
                if not os.path.exists(abs_path):
                    continue
                try:
                    if os.path.isdir(abs_path):
                        shutil.rmtree(abs_path)
                    else:
                        os.remove(abs_path)
                except Exception as e:
                    print(f"Error deleting {abs_path}: {str(e)}")
                    continue
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error processing delete request: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def preview_pdf(request, rel_path):
    base_dir = r'.\作业指导书'  # 你的PDF根目录
    abs_path = os.path.join(base_dir, rel_path)
    if not os.path.exists(abs_path) or not abs_path.lower().endswith('.pdf'):
        raise Http404("PDF not found")
    response = FileResponse(open(abs_path, 'rb'), content_type='application/pdf')
    # 关键：设置为 inline
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(abs_path)}"'
    return response


def preview_video(request, rel_path):
    base_dir = r'.\作业指导书'
    abs_path = os.path.join(base_dir, rel_path)
    if not os.path.exists(abs_path) or not abs_path.lower().endswith('.mp4'):
        raise Http404("Video not found")
    response = FileResponse(open(abs_path, 'rb'), content_type='video/mp4')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(abs_path)}"'
    return response


def get_file_info(path, base_dir):
    items = []
    for entry in os.scandir(path):
        stat = entry.stat()
        rel_path = os.path.relpath(entry.path, base_dir).replace("\\", "/")
        items.append({
            'name': entry.name,
            'is_dir': entry.is_dir(),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'type': '文件夹' if entry.is_dir() else '文件',
            'size': '' if entry.is_dir() else stat.st_size,
            'path': entry.path,
            'rel_path': rel_path,  # 新增
        })
    items.sort(key=lambda x: (not x['is_dir'], x['name']))
    return items


def file_explorer(request, rel_path=''):
    base_dir = '.\\作业指导书'
    abs_path = os.path.join(base_dir, rel_path)
    files = get_file_info(abs_path, base_dir)
    # 生成面包屑导航
    breadcrumbs = []
    parts = rel_path.split('/') if rel_path else []
    for i in range(len(parts) + 1):
        breadcrumbs.append({
            'name': parts[i - 1] if i else '首页',
            'path': '/'.join(parts[:i])
        })
    return render(request, 'file_explorer.html', {
        'files': files,
        'breadcrumbs': breadcrumbs,
        'current_path': rel_path,
    })


def list_all_manuals(scan_dir, base_dir):
    result = []
    for root, dirs, files in os.walk(scan_dir):
        for d in dirs:
            abs_path = os.path.join(root, d)
            rel_path = os.path.relpath(abs_path, base_dir)   # 一定是base_dir，不是scan_dir！
            result.append({'type':'dir', 'name':d, 'rel_path':rel_path.replace("\\", "/")})
        for f in files:
            if f.lower().endswith('.pdf'):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, base_dir)
                result.append({'type':'pdf', 'name':f, 'rel_path':rel_path.replace("\\", "/")})
    return result


def clean_name(name):
    # 只返回连续2-6个汉字字符串（可以根据实际调整，确保能拿到像“渗透探伤”这样的词）
    match = re.search(r'([\u4e00-\u9fa5]{2,20})', name)
    return match.group(1) if match else name


def find_best_match_v2(keyword, base_dir):
    import os, re, difflib
    from pypinyin import lazy_pinyin

    NOISE_WORDS = ["打开", "查看", "帮我", "一下", "请", "的", "作业指导书", "指导书", "作业书", "指导数", "指导说", "知道说", "知道书", "直到书", "直到说"]
    def extract_core_kw(kw):
        # 去除括号及噪音词
        kw = re.sub(r'[（(].*?[）)]', '', kw)
        for nw in NOISE_WORDS:
            kw = kw.replace(nw, '')
        kw = kw.strip()
        # 提取连续2字及以上汉字词
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', kw)
        return ''.join(words) if words else kw

    pat = r'^(厂修|段修|临修)[/\\\s]?(.+)$'
    m = re.match(pat, keyword)
    type_dir = None
    search_kw = keyword
    if m:
        type_map = {'厂修': '厂修作业指导书', '段修': '段修作业指导书', '临修': '临修作业指导书'}
        type_key = m.group(1)
        type_dir = type_map.get(type_key) or type_key
        search_kw = m.group(2).strip()
        if not search_kw:
            return {'type': 'dir', 'name': type_dir, 'rel_path': type_dir}
    scan_dir = os.path.join(base_dir, type_dir) if type_dir else base_dir

    manuals = list_all_manuals(scan_dir, base_dir)

    search_core = extract_core_kw(search_kw)
    if not search_core or len(search_core) < 2:
        return None
    # 直接包含
    contains = [
        item for item in manuals
        if search_core in extract_core_kw(clean_name(item['name']))
    ]
    if len(contains) == 1:
        return contains[0]
    if len(contains) > 1:
        return contains[:20]  # 限制条数
    # 拼音模糊+分数限制
    kw_py = ''.join(lazy_pinyin(search_core))
    matches = []
    for item in manuals:
        clean_core = extract_core_kw(clean_name(item['name']))
        name_py = ''.join(lazy_pinyin(clean_core))
        score = difflib.SequenceMatcher(None, kw_py, name_py).ratio()
        if score > 0.7:  # 阈值可调整
            matches.append((score, item))
    matches.sort(key=lambda x: x[0], reverse=True)
    res = [item for score, item in matches][:20]  # 最多20条
    if len(res) > 0:
        return res
    # 兜底
    for item in manuals:
        clean_core = extract_core_kw(clean_name(item['name']))
        if search_core in clean_core or clean_core in search_core:
            return item
    return None


from django.views.decorators.http import require_GET


@require_GET
def search_manual(request):
    keyword = request.GET.get('q', '').strip()
    if not keyword:
        return JsonResponse({'error':'未提供关键字'}, status=400)
    base_dir = './作业指导书'
    res = find_best_match_v2(keyword, base_dir)
    if isinstance(res, dict):
        return JsonResponse({'type':res['type'], 'rel_path':res['rel_path'], 'name':res['name']})
    elif isinstance(res, list):
        return JsonResponse({'choices': [{'type':i['type'], 'rel_path':i['rel_path'],'name':i['name']} for i in res]})
    else:
        return JsonResponse({'error':'未找到相关作业指导书'}, status=404)


def find_best_match_web(user_text, manuals, base_dir):
    user_text_lower = user_text.lower()
    matches = []

    # 遍历所有文件和文件夹
    for item in manuals:
        clean = clean_name(item['name'])
        name_lower = clean.lower()

        # 如果文件名包含搜索词
        if user_text_lower in name_lower:
            # 如果是文件夹，给匹配度加权
            weight = 1.0 if item['type'] == 'dir' else 1.5
            matches.append((weight, item))

    # 按匹配度排序（文件优先）
    matches.sort(key=lambda x: x[0], reverse=True)

    if len(matches) > 0:
        # 返回所有匹配结果
        return [item for weight, item in matches]
    else:
        return None


@csrf_exempt
def search_manual_web(request):
    keyword = request.GET.get('q', '')
    base_dir = './作业指导书'
    manuals = list_all_manuals(base_dir, base_dir)
    result = find_best_match_web(keyword, manuals, base_dir)
    if isinstance(result, dict):
        return JsonResponse({'type': result['type'], 'rel_path': result['rel_path'], 'name': result['name']})
    elif isinstance(result, list):
        # 多个高分项
        return JsonResponse({'choices': [
            {'type': item['type'], 'rel_path': item['rel_path'], 'name': item['name']} for item in result
        ]})
    else:
        return JsonResponse({'error': '未找到相关作业指导书'}, status=404)


def wlgl(request):
    return render(request, "物料系统选择中间页.html")
import logging
from datetime import datetime

from django.urls import reverse
from django.utils import timezone

from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.db.models import Q
from django import forms
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ModelForm
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from itertools import groupby
from operator import attrgetter

from app01 import models
from bzrz.models import TeamUser
from wjcy.models import Circulates, CirculateReads
from app01.models import Admin
from .models import Anquantianshu
from .forms import AnquantianshuForm  # 需要新建表单
from django import template
from datetime import date


ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]
XIUCHE_BANZU = [1, 4, 5, 8, 9, 10, 16]
XIUPEI_BANZU = [2, 3, 6, 7, 12, 15]

today = date.today()
logger = logging.getLogger(__name__)
register = template.Library()


def check_if_user_is_logged_in(request):
    # 检查传统的session方式或Django内置认证
    has_username_session = "username" in request.session
    
    # 检查Django认证session键
    has_django_auth_session = (
        '_auth_user_id' in request.session and 
        '_auth_user_backend' in request.session and 
        '_auth_user_hash' in request.session
    )
    
    # 检查request.user属性（在真实请求中有中间件处理）
    has_django_auth_attr = hasattr(request, 'user') and request.user.is_authenticated
    
    return has_username_session or has_django_auth_session or has_django_auth_attr


def anquantianshu_list(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    form = AnquantianshuForm()
    fenlei = request.GET.get('fenlei')
    if fenlei:
        items = Anquantianshu.objects.filter(anquanfenlei=fenlei)
    else:
        items = Anquantianshu.objects.all().order_by('-todaytime')

    context = {
        'role': role,
        'banzu': banzu,
        'form': form,
        'items': items,
        "fenlei": fenlei,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'xiuche_banzu': XIUCHE_BANZU,
        'xiupei_banzu': XIUPEI_BANZU,
        'banzu_choices': TeamUser.banzu_choices,
        'classification_choices': Circulates.classification_choices,
    }
    return render(request, "anquantianshu_list.html", context)


def anquantianshu_detail(request, id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    item = get_object_or_404(Anquantianshu, id=id)

    context = {
        'role': role,
        'banzu': banzu,
        'item': item,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'xiuche_banzu': XIUCHE_BANZU,
        'xiupei_banzu': XIUPEI_BANZU,
        'banzu_choices': TeamUser.banzu_choices,
        'classification_choices': Circulates.classification_choices,
    }
    return render(request, 'anquantianshu_detail.html', context)


def add_anquantianshu(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)
    chejian = request.session['info']['chejian']
    if request.method == "POST":
        # 可选方案1：用隐藏域传递fenlei（更通用）
        fenlei_post = request.POST.get('anquanfenlei')
        form = AnquantianshuForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.chejian = chejian
            instance.anquanfenlei = fenlei_post  # 自动填分类
            instance.save()
            messages.success(request, '添加成功')
            # 跳转回带分类参数的列表页
            redirect_url = reverse('aqts:anquantianshu_list')
            if fenlei_post:
                redirect_url += f'?fenlei={fenlei_post}'
            return redirect(redirect_url)
        else:
            print(form.errors)
    else:
        form = AnquantianshuForm()
    return render(request, 'anquantianshu_list.html', {
        'form': form,
        'items': Anquantianshu.objects.all().order_by('-todaytime'),
    })


def edit_anquantianshu(request, id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        login_url = f"/login1/?next={request.path}"
        return redirect(login_url)
    chejian = request.session['info']['chejian']
    item = get_object_or_404(Anquantianshu, id=id)

    if request.method == 'POST':
        fenlei_post = request.POST.get('anquanfenlei')
        form = AnquantianshuForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.chejian = chejian

            # 检查是否勾选了删除附件
            delete_requested = request.POST.get('delete_file') == '1'
            if delete_requested and instance.file:
                instance.file.delete(save=False)  # 物理删除
                instance.file = None              # 字段置空

            instance.save()
            messages.success(request, '修改成功')
            redirect_url = reverse('aqts:anquantianshu_list')
            if fenlei_post:
                redirect_url += f'?fenlei={fenlei_post}'
            return redirect(redirect_url)
    else:
        # GET请求通常不用表单，弹窗内容靠JS填
        form = AnquantianshuForm(instance=item)

    return render(request, 'anquantianshu_list.html', {
        'form': form,
        'items': Anquantianshu.objects.all().order_by('-todaytime')
    })


def delete_anquantianshu(request, id):
    fenlei = request.GET.get('fenlei', '')
    item = get_object_or_404(Anquantianshu, id=id)
    if request.method == "POST":
        item.delete()
        messages.success(request, '删除成功')
        redirect_url = reverse('aqts:anquantianshu_list')
        if fenlei:
            redirect_url += f'?fenlei={fenlei}'
        return redirect(redirect_url)
    return render(request, 'anquantianshu_list.html', {'item': item, 'fenlei': fenlei})



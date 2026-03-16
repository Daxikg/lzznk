import os
import time
from datetime import datetime
from django import forms
from django.contrib import messages
from django.forms import ModelForm
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login

from app01.views import LoginForm, logger
from app01.models import Admin
from . import models
from .models import TeamLog, TeamUser, Certificate


ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]


def check_if_user_is_logged_in(request):
    return "username" in request.session


def login2(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "login2.html", {"form": form})
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
                admin_object = Admin.objects.get(username=user.username)
                username = admin_object.username
                logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了班组日志。')
                
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
                return redirect("/bzrz/teamlog0/")
            except Admin.DoesNotExist:
                form.add_error("password", "用户信息不存在！")
                return render(request, "login2.html", {"form": form})
        else:
            form.add_error("password", "账号或密码错误！")
            return render(request, "login2.html", {"form": form})
    return redirect("/bzrz/login2/")


def register2(request):
    request.session.clear()
    return redirect('/bzrz/login2/')


def get_user_banzu_choices(user_info):
    """
    根据 session['info'] 返回该用户能看的班组 choices
    """
    banzu = user_info.get('banzu')
    role = user_info.get('role')
    all_choices = TeamUser.banzu_choices
    if role == "总管理员" :  # 管理员账号
            return all_choices
    elif role == '修车管理员':
        allowed = [1, 4, 5, 8, 9, 10, 16, 18]
        return [c for c in all_choices if c[0] in allowed]
    elif role == '修配管理员':
        allowed = [2, 3, 6, 7, 11, 12, 15, 17]
        return [c for c in all_choices if c[0] in allowed]
    elif role == 'Guest':
        return all_choices
    else:
        # 普通班组账号
        return [c for c in all_choices if c[0] == int(banzu)]


def make_banzu_years(teamlog_model, banzu_choices, banzu_code=None):
    banzu_years_list = []
    # 保证banzu_code为int, 否则等值判断失效
    if banzu_code is not None:
        try:
            banzu_code = int(banzu_code)
        except Exception:
            pass
    group_choices = banzu_choices if banzu_code is None else [c for c in banzu_choices if c[0] == banzu_code]
    for banzu_choice in group_choices:
        code = banzu_choice[0]
        logs = teamlog_model.objects.filter(banzu=code)
        years_set = sorted({log.shijian.year for log in logs}, reverse=True)
        years = [
            {
                'year': year,
                'logs': logs.filter(shijian__year=year).order_by('shijian')
            }
            for year in years_set
        ]
        banzu_years_list.append({
            'banzu': banzu_choice,
            'years': years,
        })
    return banzu_years_list


def teamlog0(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/bzrz/login2/')

    user_info = request.session['info']
    role = user_info.get('role')
    banzu_choices = get_user_banzu_choices(user_info)
    banzu_years_list = make_banzu_years(TeamLog, banzu_choices)

    context = {
        'role': role,
        'banzu_years_list': banzu_years_list,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI
    }
    return render(request, "TeamLog0.html", context)


class teamuserForm(ModelForm):
    class Meta:
        model = models.TeamUser
        fields = ['name', 'banzu', 'jineng', 'certificate', 'dengji', 'gender', 'marriage', 'number', 'birth', 'wenhua',
                  'jiguan', 'mianmao', 'didian', 'leibie', 'award', 'beizhu', 'retire']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ['name', 'number', 'didian']:
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif name in ['beizhu', 'award']:
                field.widget = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def teamlog1(request, banzu):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/bzrz/login2/')

    form = teamuserForm
    banzu_choices = TeamUser.banzu_choices
    banzu_display_dict = dict(banzu_choices)
    banzu_display = banzu_display_dict.get(banzu, 'Unknown banzu')
    teamlogs = TeamLog.objects.filter(banzu=banzu)
    teamusers = TeamUser.objects.filter(banzu=banzu, retire=1)

    user_info = request.session['info']
    role = user_info.get('role')
    banzu_choices = get_user_banzu_choices(user_info)
    banzu_years_list = make_banzu_years(TeamLog, banzu_choices)

    context = {
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'form': form,
        'teamlogs': teamlogs,
        'teamusers': teamusers,
        'banzu': banzu,
        'banzu_choices': banzu_choices,
        'banzu_display': banzu_display,
        'selected_banzu': banzu,
        'banzu_years_list': banzu_years_list,
    }
    return render(request, "TeamLog1.html", context)


def getNewName(file_type, user_name, cert):
    cert = "".join(x for x in cert if x.isalnum())
    time_str = time.strftime("%Y-%m-%d", time.localtime())
    new_name = f"{file_type}-{user_name}-{cert}-{time_str}.jpg"
    return new_name


def getNewName1(file_type, banzu, id):
    banzu_text = dict(TeamLog.banzu_choices)[banzu]
    new_name = f"{file_type}-{banzu_text}-{id}.jpg"
    return new_name


def license(request, banzu, id):
    user = TeamUser.objects.filter(id=id).first()
    certs = user.certificate.splitlines()
    cert_pics = {cert: Certificate.objects.filter(user=user, type=cert).first() for cert in certs}
    user_info = request.session['info']

    role = user_info.get('role')
    banzu_choices = get_user_banzu_choices(user_info)
    banzu_years_list = make_banzu_years(TeamLog, banzu_choices)
    context = {
        'user': user,
        'banzu': banzu,
        'id': id,
        'cert_pics': cert_pics,
        'certs': certs,
        'banzu_years_list': banzu_years_list,
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
    }
    if request.method == "POST" and not request.FILES:
        messages.warning(request, f'未添加任何照片，无法上传，请添加照片后重试！')
        return redirect(request.path_info)
    elif request.method == "POST" and request.FILES:
        user = TeamUser.objects.filter(id=id).first()
        # 获取用户的证书类型列表
        certs = user.certificate.splitlines()

        for idx, cert in enumerate(certs, start=1):
            file_field_name = 'pic' + str(idx)

            if file_field_name in request.FILES:
                file = request.FILES[file_field_name]

                # 获取新的文件名
                new_name = getNewName(file_field_name, user.name, cert)
                # 将要保存的地址和文件名称
                dir_name = os.path.join('E:\\credential', 'users')
                # 如果文件夹不存在，则创建文件夹
                os.makedirs(dir_name, exist_ok=True)
                file_path = os.path.join(dir_name, new_name)
                # 分块保存image
                content = file.chunks()
                with open(file_path, 'wb') as f:
                    for i in content:
                        f.write(i)
                # 尝试获取已有的同类型证书记录，如果没有则创建一个新的
                cert_obj, created = Certificate.objects.get_or_create(user=user, type=cert)
                # 将证书的图片路径更新为新上传的图片路径
                cert_obj.pic = new_name
                cert_obj.save()
                messages.success(request, f'图片上传成功！')
        return redirect(request.path_info)
    return render(request, 'license.html', context)


def license1(request, banzu, id):
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic' not in request.FILES:
            messages.warning(request, f'未添加任何照片，无法上传，请添加照片后重试！')
            return redirect(request.path_info)
        file = request.FILES['pic']
        log = TeamLog.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName1('pic', log.banzu, log.id)  # 确保 banzu 和 id 是可用的
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'meeting')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        TeamLog.objects.filter(id=id).update(pic=new_name)
        messages.success(request, f'图片上传成功！')
        return redirect(request.path_info)
    return HttpResponseRedirect(previous_page)


def license2(request, banzu, id):
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic1' not in request.FILES:
            messages.warning(request, f'未添加任何照片，无法上传，请添加照片后重试！')
            return redirect(request.path_info)
        file = request.FILES['pic1']
        log = TeamLog.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName1('pic1', log.banzu, log.id)  # 确保 banzu 和 id 是可用的
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'meeting')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        TeamLog.objects.filter(id=id).update(pic1=new_name)
        messages.success(request, f'图片上传成功！')
        return redirect(request.path_info)
    return HttpResponseRedirect(previous_page)


class TeamLogForm(ModelForm):
    class Meta:
        model = models.TeamLog
        fields = ["shijian", "didian", "zhuchiren", "renyuan1", "renyuan2", "renyuan3", "neirong"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ['didian', 'zhuchiren', 'renyuan3']:
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif name in ['renyuan1', 'renyuan2']:
                field.widget = forms.NumberInput(attrs={'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


@csrf_exempt
def add_teamuser(request, banzu):
    new_log = TeamUser(banzu=banzu, name="新人员")
    try:
        new_log.save()
        messages.success(request, f'新人员添加成功！')
    except Exception as e:
        # 返回一个包含错误描述的响应
        return HttpResponse(f"Error occurred: {e}")
    # 如果没有错误发生，重定向到指定的url
    redirect_url = reverse('bzrz:teamlog1', args=[banzu])
    return HttpResponseRedirect(redirect_url)


@csrf_exempt
def edit_teamuser(request):
    if request.method == 'POST':
        log_id = request.POST.get('logid')
        log = TeamUser.objects.filter(id=log_id)
        log = log.first()

        log.name = request.POST.get('name') or None
        log.banzu = request.POST.get('banzu') or None
        # 这里需要先处理带日期的字段，将空字符串转化为None，再进行保存
        birth = request.POST.get('birth')
        log.birth = datetime.strptime(birth, '%Y-%m-%d').date() if birth else None

        log.wenhua = int(request.POST.get('wenhua')) if request.POST.get('wenhua') else None
        log.gender = int(request.POST.get('gender')) if request.POST.get('gender') else None
        log.marriage = int(request.POST.get('marriage')) if request.POST.get('marriage') else None
        log.retire = int(request.POST.get('retire')) if request.POST.get('retire') else None
        log.jineng = int(request.POST.get('jineng')) if request.POST.get('jineng') else None
        cert = request.POST.getlist('certificate')
        log.certificate = "\n".join(cert) if cert else None
        log.dengji = int(request.POST.get('dengji')) if request.POST.get('dengji') else None
        log.number = request.POST.get('number') or None
        log.mianmao = int(request.POST.get('mianmao')) if request.POST.get('mianmao') else None
        log.didian = request.POST.get('didian') or None
        log.leibie = int(request.POST.get('leibie')) if request.POST.get('leibie') else None
        log.award = request.POST.get('award') or None
        log.beizhu = request.POST.get('beizhu') or None
        log.save()
        messages.success(request, f'{log.name}信息修改成功！')
        return JsonResponse({
            'message': f'The log with id {log_id} was successfully updated.',
        })
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def teamlog(request, banzu, year, log_id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/bzrz/login2/')

    role = request.session['info']['role']
    teamlogs = TeamLog.objects.filter(banzu=banzu, shijian__year=year)

    log = get_object_or_404(TeamLog, pk=log_id)
    form = TeamLogForm(instance=log)

    all_banzu_years = make_banzu_years(TeamLog, TeamUser.banzu_choices)

    # 判定权限
    if role in ('管理员', 'Guest'):
        # 展示所有班组
        banzu_years_list = make_banzu_years(TeamLog, TeamUser.banzu_choices)
    else:
        # 普通用户只看自己的班组
        banzu_years_list = make_banzu_years(TeamLog, TeamUser.banzu_choices, banzu_code=banzu)

    context = {
        'banzu': banzu,
        'id': log_id,
        'log_id': log_id,
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'teamlogs': teamlogs,
        'selected_banzu': banzu,
        'selected_year': year,
        'log': log,
        'form': form,
        'all_banzu_years': all_banzu_years,
        'banzu_years_list': banzu_years_list,
    }
    return render(request, "TeamLog.html", context)


def create_teamlog(request, banzu):
    new_log = TeamLog(banzu=banzu, didian="班组", shijian=datetime.now())
    try:
        new_log.save()
        messages.success(request, f'新活动记录创建成功！')
        redirect_url = reverse('bzrz:teamlog', args=[banzu, new_log.shijian.year, new_log.id])
        return HttpResponseRedirect(redirect_url)
    except Exception as e:
        # TODO: handle exception here, like showing error page
        pass


@csrf_exempt
def edit_teamlog(request):
    if request.method == 'POST':
        log_id = request.POST.get('log_id')
        # 检查是否存在具有给定 ID 的 TeamLog 对象
        log = TeamLog.objects.get(id=log_id)
        log.shijian = request.POST.get('shijian')
        log.didian = request.POST.get('didian') or None
        log.zhuchiren = request.POST.get('zhuchiren') or None
        log.renyuan1 = request.POST.get('renyuan1') or None
        log.renyuan2 = request.POST.get('renyuan2') or None
        log.renyuan3 = request.POST.get('renyuan3') or None
        log.neirong = request.POST.get('neirong') or None
        log.save()
        messages.success(request, f'活动记录保存成功！')
        return JsonResponse({
            'message': f'The log with id {log_id} was successfully updated.',
        })
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def delete_teamlog(request, log_id):
    instance = get_object_or_404(TeamLog, id=log_id)
    if request.method == 'POST':
        instance.delete()
        messages.info(request, f'活动记录已被删除！')
        return JsonResponse({'status': 'ok'})
    return render(request, 'user_delete.html')

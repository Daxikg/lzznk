import datetime
import hashlib
import os
import time
from decimal import Decimal
from datetime import datetime, timedelta, date

from django import forms
from django.contrib import messages
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from app01 import models
from app01.views import check_if_user_is_logged_in, LoginForm, logger
from djangoProject import settings
from jkrq import models
from jkrq.models import JkrqList, JkrqList1Log
from django.contrib.auth import authenticate, login as auth_login

ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]
XIUCHE_BANZU = [1, 4, 5, 8, 9, 10]
XIUPEI_BANZU = [2, 3, 6, 7, 12]


def md5(data_string):
    obj = hashlib.md5(settings.SECRET_KEY.encode("utf-8"))
    obj.update(data_string.encode("utf-8"))
    return obj.hexdigest()


def jkrq_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "jkrq_login.html", {"form": form})
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
                logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了健康管理。')
                
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
                return redirect('jkrq:jkrq_list1')
            except models.Admin.DoesNotExist:
                form.add_error("password", "用户信息不存在！")
                return render(request, "jkrq_login.html", {"form": form})
        else:
            form.add_error("password", "账号或密码错误！")
            return render(request, "jkrq_login.html", {"form": form})
    return render(request, "jkrq_login.html", {"form": form})


def logout(request):
    request.session.clear()
    return redirect('jkrq:jkrq_login')


def jkrq_index(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/jkrq/jkrq_login/')
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']
    today = date.today()
    year = today.year
    data = []
    this_year = datetime.now().year
    last_year = this_year - 1

    # 获取去年所有的JKWH的人
    jkrq_list_last_year = JkrqList.objects.filter(
        Q(people_type='JKWH') &
        Q(time__year=last_year)
    )

    # 获取今年所有的JKWH的人
    jkrq_list_this_year_dict = {obj.name: obj for obj in JkrqList.objects.filter(
        Q(people_type='JKWH') &
        Q(time__year=this_year)
    )}

    user_list = []  # 存储符合条件的人
    for obj in jkrq_list_last_year:
        user_dict = {'person': obj, 'last_year_level': obj.get_people_level_display}  # 保存去年的信息
        # 获取今年的记录
        obj_this_year = jkrq_list_this_year_dict.get(obj.name)

        # 如果去年有但是今年没有，则加入名单
        if obj_this_year is None:
            user_list.append(user_dict)
            continue

        user_dict['this_year_level'] = obj_this_year.get_people_level_display  # 保存今年的等级

        # 等级由lv3或lv4变为lv1
        if (obj.people_level in ['lv3', 'lv4']) and obj_this_year.people_level == 'lv1':
            user_list.append(user_dict)

        # 等级由lv4变为lv3
        if (obj.people_level == 'lv4') and obj_this_year.people_level == 'lv3':
            user_list.append(user_dict)

    if banzu == 13:
        if chejian == 1:
            user_list = [user for user in user_list if user['person'].banzu in XIUPEI_BANZU]
        elif chejian == 2:
            user_list = [user for user in user_list if user['person'].banzu in XIUCHE_BANZU]
        else:
            pass
    else:
        user_list = [user for user in user_list if user['person'].banzu == banzu]

    for user_dict in user_list:
        null = ''
        last_log = JkrqList1Log.objects.filter(people=user_dict['person'].id).order_by(
            '-check_date').first()  # fetch the latest log
        if last_log is None:
            null = '暂无记录'
        data.append({
            'jkrqList1': user_dict,
            'last_log': last_log,  # return the last log
            'null': null,
            'role': role,
            "admin": ADMIN,
            "xiuche": XIUCHE,
            "xiupei": XIUPEI,
        })

    return render(request, "jkrq_index.html", {"data": data,
                                               'now': today,
                                               'role': role,
                                               "admin": ADMIN,
                                               "xiuche": XIUCHE,
                                               "xiupei": XIUPEI,
                                               'year': year,
                                               'last_year': year - 1})


class JkrqListForm(ModelForm):
    class Meta:
        model = models.JkrqList
        fields = ['name', 'banzu', 'people_type', 'people_level', 'people_height', 'people_weight',
                  'people_check_method', 'people_smoke', 'people_blood_fat', 'people_blood_candy']

    def __init__(self, *args, **kwargs):
        # 新增一个role参数
        banzu = kwargs.pop('banzu', None)
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # 姓名
            if name == 'name':
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}

        # 如果非管理员，设置部分字段只读/禁用
        if banzu != 13:
            # 允许编辑的字段
            editable = ['name', 'banzu', 'people_height', 'people_weight']
            for fname in self.fields:
                if fname not in editable:
                    self.fields[fname].widget.attrs['readonly'] = True  # 可防止修改，也可用 'disabled': True
                    self.fields[fname].widget.attrs['disabled'] = True  # 前端样式同步禁用


def jkrq_list1(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/jkrq/jkrq_login/')
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    today = date.today()
    year = today.year
    form = JkrqListForm(banzu=banzu)  # 传role
    data = []
    data1 = []
    data2 = []
    unchecked_people_names = []
    p_list = JkrqList.objects.filter(time__year=datetime.now().year, people_type='JKWH')
    o_list = JkrqList.objects.filter(time__year=datetime.now().year - 1, people_type='JKWH')

    if banzu == 13:
        if chejian == 1:
            p_list = p_list.filter(banzu__in=[2, 3, 6, 7, 12])
            o_list = o_list.filter(banzu__in=[2, 3, 6, 7, 12])
        elif chejian == 2:
            p_list = p_list.filter(banzu__in=[1, 4, 5, 8, 9, 10])
            o_list = o_list.filter(banzu__in=[1, 4, 5, 8, 9, 10])
        else:
            pass
    else:
        p_list = p_list.filter(banzu=banzu)
        o_list = o_list.filter(banzu=banzu)

    for jkrqList in p_list:
        null = ''
        if jkrqList.people_check_method == 'DAYLY':
            q_object = Q(people=jkrqList, check_date=today)
        elif jkrqList.people_check_method == 'WEEKLY':
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            q_object = Q(people=jkrqList, check_date__range=[start_week, end_week])
        elif jkrqList.people_check_method == 'MONTHLY':
            q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)
        elif jkrqList.people_check_method == 'QUARTER':
            current_month = today.month
            if current_month in [1, 2, 3]:
                quarter_start = date(today.year, 1, 1)
                quarter_end = date(today.year, 3, 31)
            elif current_month in [4, 5, 6]:
                quarter_start = date(today.year, 4, 1)
                quarter_end = date(today.year, 6, 30)
            elif current_month in [7, 8, 9]:
                quarter_start = date(today.year, 7, 1)
                quarter_end = date(today.year, 9, 30)
            else:  # 10,11,12
                quarter_start = date(today.year, 10, 1)
                quarter_end = date(today.year, 12, 31)
            q_object = Q(people=jkrqList, check_date__range=[quarter_start, quarter_end])
        else:
            q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)

        logs = JkrqList1Log.objects.filter(q_object)

        if logs.exists():
            continue  # 已有记录则跳过

        # 如果这个人需要检查，把他的名字添加到名字列表中
        unchecked_people_names.append(jkrqList.name)

        last_log = JkrqList1Log.objects.filter(people=jkrqList).order_by('-check_date').first()  # 获取最新的日志
        if last_log is None:
            null = '暂无记录'
        data.append({
            'jkrqList1': jkrqList,
            'last_log': last_log,  # 返回最后的日志
            'null': null
        })
    # 获取需要检查的人员的ID列表
    check_people_ids = [item['jkrqList1'].id for item in data]

    for people in p_list:
        null = ''
        last_log = JkrqList1Log.objects.filter(people=people).order_by('-check_date').first()  # 取得最新的记录
        if last_log is None:
            null = '暂无记录'
        data1.append({
            'jkrqList1': people,
            'last_log': last_log,  # 返回最后一个记录
            'null': null,
            'needs_check': people.id in check_people_ids  # 检查此人是否需要进行检查
        })
    for people in o_list:
        null = ''
        last_log = JkrqList1Log.objects.filter(people=people).order_by('-check_date').first()  # 取得最新的记录
        if last_log is None:
            null = '暂无记录'
        data2.append({
            'jkrqList1': people,
            'last_log': last_log,
            'null': null,
        })
    needs_check = any(item['needs_check'] for item in data1)
    return render(request, "jkrq_list1.html", {
        "form": form,
        "data": data,
        "data1": data1,
        "data2": data2,
        'now': today,
        'role': role,
        'banzu': banzu,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
        'year': year,
        'last_year': year - 1,
        'unchecked_people_names': unchecked_people_names,
        'needs_check': needs_check
    })


def getNewName3(file_type, log):
    time_str = time.strftime("%Y-%m-%d", time.localtime())
    new_name = f"{file_type}-{log.people}-{log.id}-{time_str}.jpg"
    return new_name


def license3(request, id):
    role = request.session['info']['role']
    log = JkrqList1Log.objects.get(id=id)
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic' not in request.FILES:
            return HttpResponse('<script>alert("未添加任何照片，无法上传，请添加照片后重试!"); history.back();</script>')
        file = request.FILES['pic']
        log = JkrqList1Log.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName3('pic', log)
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'blood')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        JkrqList1Log.objects.filter(id=id).update(pic=new_name)
        return redirect(request.path_info)
    return render(request, 'license3.html', {'log': log, 'role': role,
                                             "admin": ADMIN,
                                             "xiuche": XIUCHE,
                                             "xiupei": XIUPEI, })


def license4(request, id):
    role = request.session['info']['role']
    log = JkrqList1Log.objects.get(id=id)
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic' not in request.FILES:
            return HttpResponse('<script>alert("未添加任何照片，无法上传，请添加照片后重试!"); history.back();</script>')
        file = request.FILES['pic']
        log = JkrqList1Log.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName3('pic', log)
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'blood')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        JkrqList1Log.objects.filter(id=id).update(pic=new_name)
        return redirect(request.path_info)
    return render(request, 'license4.html', {'log': log, 'role': role,
                                             "admin": ADMIN,
                                             "xiuche": XIUCHE,
                                             "xiupei": XIUPEI, })


def license5(request, id):
    role = request.session['info']['role']
    log = JkrqList1Log.objects.get(id=id)
    log1 = JkrqList.objects.get(id=log.people.id)
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic' not in request.FILES:
            return HttpResponse('<script>alert("未添加任何照片，无法上传，请添加照片后重试!"); history.back();</script>')
        file = request.FILES['pic']
        log = JkrqList1Log.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName3('pic', log)
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'blood')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        JkrqList1Log.objects.filter(id=id).update(pic=new_name)
        return redirect(request.path_info)
    return render(request, 'license5.html', {'log': log, 'log1': log1, 'role': role,
                                             "admin": ADMIN,
                                             "xiuche": XIUCHE,
                                             "xiupei": XIUPEI, })


def license6(request, id):
    role = request.session['info']['role']
    log = JkrqList1Log.objects.get(id=id)
    log1 = JkrqList.objects.get(id=log.people.id)
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic' not in request.FILES:
            return HttpResponse('<script>alert("未添加任何照片，无法上传，请添加照片后重试!"); history.back();</script>')
        file = request.FILES['pic']
        log = JkrqList1Log.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName3('pic', log)
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'blood')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        JkrqList1Log.objects.filter(id=id).update(pic=new_name)
        return redirect(request.path_info)
    return render(request, 'license6.html', {'log': log, 'log1': log1, 'role': role,
                                             "admin": ADMIN,
                                             "xiuche": XIUCHE,
                                             "xiupei": XIUPEI, })


def license7(request, id):
    role = request.session['info']['role']
    log = JkrqList1Log.objects.get(id=id)
    log1 = JkrqList.objects.get(id=log.people.id)
    return render(request, 'license7.html', {'log': log, 'log1': log1, 'role': role,
                                             "admin": ADMIN,
                                             "xiuche": XIUCHE,
                                             "xiupei": XIUPEI, })


@csrf_exempt
def add_jkrq1(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        banzu = request.POST.get('banzu')
        people_type = 'JKWH'
        people_level = request.POST.get('people_level')
        people_height = float(request.POST.get('people_height'))
        people_weight = float(request.POST.get('people_weight'))
        people_bmi = people_weight / (people_height ** 2)
        people_check_method = request.POST.get('people_check_method')

        new_log = JkrqList(
            people_type=people_type,
            name=name,
            banzu=banzu,
            people_level=people_level,
            people_height=people_height,
            people_weight=people_weight,
            people_bmi=people_bmi,
            people_check_method=people_check_method,
            time=datetime.now().date()
        )
        try:
            new_log.save()
            messages.info(request, f'{name}：人员新增成功！')
        except Exception as e:
            # 返回一个包含错误描述的响应
            return HttpResponse(f"Error occurred: {e}")

        # 如果没有错误发生，重定向到指定的url
        redirect_url = reverse('jkrq:jkrq_list1')
        return HttpResponseRedirect(redirect_url)
    else:
        form = JkrqListForm()
        return render(request, 'jkrq_list1.html', {'form': form})


@csrf_exempt
def add_jkrq2(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        banzu = request.POST.get('banzu')
        people_type = 'XNXGJB'
        people_level = request.POST.get('people_level')
        people_height = float(request.POST.get('people_height'))
        people_weight = float(request.POST.get('people_weight'))
        people_bmi = people_weight / (people_height ** 2)
        people_smoke = request.POST.get('people_smoke') or None
        people_blood_fat = request.POST.get('people_blood_fat') or None
        people_blood_candy = request.POST.get('people_blood_candy') or None
        people_check_method = request.POST.get('people_check_method')
        new_log = JkrqList(
            people_type=people_type,
            name=name,
            banzu=banzu,
            people_level=people_level,
            people_height=people_height,
            people_weight=people_weight,
            people_bmi=people_bmi,
            people_smoke=people_smoke,
            people_blood_fat=people_blood_fat,
            people_blood_candy=people_blood_candy,
            people_check_method=people_check_method,
            time=datetime.now().date()
        )
        try:
            new_log.save()
            messages.info(request, f'{name}：人员新增成功！')
        except Exception as e:
            # 返回一个包含错误描述的响应
            return HttpResponse(f"Error occurred: {e}")

        # 如果没有错误发生，重定向到指定的url
        redirect_url = reverse('jkrq:jkrq_list2')
        return HttpResponseRedirect(redirect_url)
    else:
        form = JkrqListForm()
        return render(request, 'jkrq_list2.html', {'form': form})


@csrf_exempt
def edit_jkrq(request):
    if request.method == 'POST':
        # 获取当前登录用户的角色
        role = request.session['info']['role']

        log_id = request.POST.get('logid')
        log = JkrqList.objects.filter(id=log_id).first()

        if not log:
            return JsonResponse({'error': '记录不存在'}, status=404)

        # 公共字段
        log.name = request.POST.get('name')
        log.banzu = request.POST.get('banzu')
        # 保护类型转换
        try:
            log.people_height = Decimal(request.POST.get('people_height'))
            log.people_weight = Decimal(request.POST.get('people_weight'))
            if log.people_height > 0:
                log.people_bmi = log.people_weight / (log.people_height ** 2)
            else:
                log.people_bmi = None
        except Exception:
            return JsonResponse({'error': '身高或体重格式错误!'}, status=400)

        # 管理员能修改全部字段
        if role == '总管理员' or role == '修车管理员' or role == '修配管理员':
            log.people_type = request.POST.get('people_type')
            log.people_level = request.POST.get('people_level')
            log.people_check_method = request.POST.get('people_check_method') or None
        # 非管理员不能修改以上字段，保留原值

        log.save()
        messages.info(request, f'{log.name}信息修改成功！')
        return JsonResponse({
            'message': f'人员 {log.name} 信息修改成功。',
        })
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def jkrq_list2(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/jkrq/jkrq_login/')
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']
    today = date.today()
    year = today.year
    form = JkrqListForm(banzu=banzu)
    data = []
    data1 = []
    data2 = []
    unchecked_people_names = []
    p_list = JkrqList.objects.filter(time__year=datetime.now().year, people_type='XNXGJB', )
    o_list = JkrqList.objects.filter(time__year=datetime.now().year - 1, people_type='XNXGJB', )

    if banzu == 13:
        if chejian == 1:
            p_list = p_list.filter(banzu__in=[2, 3, 6, 7, 12])
            o_list = o_list.filter(banzu__in=[2, 3, 6, 7, 12])
        elif chejian == 2:
            p_list = p_list.filter(banzu__in=[1, 4, 5, 8, 9, 10])
            o_list = o_list.filter(banzu__in=[1, 4, 5, 8, 9, 10])
        else:
            pass
    else:
        p_list = p_list.filter(banzu=banzu)
        o_list = o_list.filter(banzu=banzu)

    for jkrqList in p_list:
        null = ''
        if jkrqList.people_check_method == 'DAYLY':
            q_object = Q(people=jkrqList, check_date=today)
        elif jkrqList.people_check_method == 'WEEKLY':
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            q_object = Q(people=jkrqList, check_date__range=[start_week, end_week])
        elif jkrqList.people_check_method == 'MONTHLY':
            q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)
        elif jkrqList.people_check_method == 'QUARTER':
            current_month = today.month
            if current_month in [1, 2, 3]:
                quarter_start = date(today.year, 1, 1)
                quarter_end = date(today.year, 3, 31)
            elif current_month in [4, 5, 6]:
                quarter_start = date(today.year, 4, 1)
                quarter_end = date(today.year, 6, 30)
            elif current_month in [7, 8, 9]:
                quarter_start = date(today.year, 7, 1)
                quarter_end = date(today.year, 9, 30)
            else:  # 10,11,12
                quarter_start = date(today.year, 10, 1)
                quarter_end = date(today.year, 12, 31)
            q_object = Q(people=jkrqList, check_date__range=[quarter_start, quarter_end])
        else:
            q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)

        logs = JkrqList1Log.objects.filter(q_object)

        if logs.exists():  # if there are logs matched the filter
            continue  # skip this item and continue to next iteration

        # 如果这个人需要检查，把他的名字添加到名字列表中
        unchecked_people_names.append(jkrqList.name)

        last_log = JkrqList1Log.objects.filter(people=jkrqList).order_by('-check_date').first()  # fetch the latest log
        if last_log is None:
            null = '暂无记录'
        data.append({
            'jkrqList1': jkrqList,
            'last_log': last_log,  # return the last log
            'null': null,
        })
    for jkrqList in o_list:
        null = ''
        if jkrqList.people_check_method == 'DAYLY':
            q_object = Q(people=jkrqList, check_date=today)
        elif jkrqList.people_check_method == 'WEEKLY':
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            q_object = Q(people=jkrqList, check_date__range=[start_week, end_week])
        elif jkrqList.people_check_method == 'MONTHLY':
            q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)
        elif jkrqList.people_check_method == 'QUARTER':
            current_month = today.month
            if current_month in [1, 2, 3]:
                quarter_start = date(today.year, 1, 1)
                quarter_end = date(today.year, 3, 31)
            elif current_month in [4, 5, 6]:
                quarter_start = date(today.year, 4, 1)
                quarter_end = date(today.year, 6, 30)
            elif current_month in [7, 8, 9]:
                quarter_start = date(today.year, 7, 1)
                quarter_end = date(today.year, 9, 30)
            else:  # 10,11,12
                quarter_start = date(today.year, 10, 1)
                quarter_end = date(today.year, 12, 31)
            q_object = Q(people=jkrqList, check_date__range=[quarter_start, quarter_end])
        else:
            q_object = Q(people=jkrqList, check_date__year=today.year, check_date__month=today.month)

        logs = JkrqList1Log.objects.filter(q_object)

        if logs.exists():  # if there are logs matched the filter
            continue  # skip this item and continue to next iteration

        # 如果这个人需要检查，把他的名字添加到名字列表中
        unchecked_people_names.append(jkrqList.name)

        last_log = JkrqList1Log.objects.filter(people=jkrqList).order_by('-check_date').first()  # fetch the latest log
        if last_log is None:
            null = '暂无记录'
        data.append({
            'jkrqList1': jkrqList,
            'last_log': last_log,  # return the last log
            'null': null
        })
    # 获取需要检查的人员的ID列表
    check_people_ids = [item['jkrqList1'].id for item in data]
    for people in p_list:
        null = ''
        last_log = JkrqList1Log.objects.filter(people=people).order_by('-check_date').first()  # fetch the latest log
        if last_log is None:
            null = '暂无记录'
        data1.append({
            'jkrqList1': people,
            'last_log': last_log,  # return the last log
            'null': null,
            'needs_check': people.id in check_people_ids  # 检查此人是否需要进行检查
        })
    for people in o_list:
        null = ''
        last_log = JkrqList1Log.objects.filter(people=people).order_by('-check_date').first()  # fetch the latest log
        if last_log is None:
            null = '暂无记录'
        data2.append({
            'jkrqList1': people,
            'last_log': last_log,  # return the last log
            'null': null,
            'needs_check': people.id in check_people_ids  # 检查此人是否需要进行检查
        })
    needs_check = any(item['needs_check'] for item in data1) or any(item['needs_check'] for item in data2)
    return render(request, "jkrq_list2.html", {
        "data": data, "data1": data1, "data2": data2, "form": form, 'now': today, 'role': role, 'banzu': banzu,
        "admin": ADMIN, "xiuche": XIUCHE, "xiupei": XIUPEI, 'year': year, 'last_year': year - 1,
        'unchecked_people_names': unchecked_people_names, 'needs_check': needs_check,
    })


def jkrq_log(request):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/jkrq/jkrq_login/')
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']
    logs = JkrqList1Log.objects.all().order_by('-check_date')

    if banzu == 13:
        if chejian == 1:
            logs = logs.filter(banzu__in=XIUPEI_BANZU)
        elif chejian == 2:
            logs = logs.filter(banzu__in=XIUCHE_BANZU)
        else:
            pass
    else:
        logs = logs.filter(banzu=banzu)

    return render(request, "jkrq_log.html", {
        'logs': logs,
        'role': role,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
    })


def update_jkrq1(request):
    pid = request.POST.get('pid')
    people_blood_high = request.POST.get('people_blood_high')
    people_blood_low = request.POST.get('people_blood_low')
    people_weight = Decimal(request.POST.get('people_weight'))
    people_blood_candy = Decimal(request.POST.get('people_blood_candy')) if request.POST.get(
        'people_blood_candy') else None
    people = JkrqList.objects.get(id=pid)
    banzu = people.banzu
    people_height = people.people_height
    people_bmi = people_weight / (people_height ** 2)
    JkrqList1Log.objects.create(people_id=pid, banzu=banzu, people_blood_high=people_blood_high,
                                people_blood_low=people_blood_low, people_weight=people_weight,
                                people_bmi=people_bmi, people_blood_candy=people_blood_candy)
    people.people_weight = people_weight
    people.people_blood_candy = people_blood_candy
    people.people_blood_high = people_blood_high
    people.people_blood_low = people_blood_low
    people.people_bmi = people_bmi
    people.banzu = banzu
    people.save()
    messages.success(request, f'{people.name}已完成今日检测，舒张压为{people.people_blood_high}，'
                              f'收缩压为{people.people_blood_low}，最新体重指数为{round(people.people_bmi, 2)}。')
    return redirect('jkrq:jkrq_list1')


def update_jkrq2(request):
    pid = request.POST.get('pid')
    people_blood_high = request.POST.get('people_blood_high')
    people_blood_low = request.POST.get('people_blood_low')
    people_weight = Decimal(request.POST.get('people_weight'))
    people_blood_candy = Decimal(request.POST.get('people_blood_candy')) if request.POST.get(
        'people_blood_candy') else None
    people = JkrqList.objects.get(id=pid)
    banzu = people.banzu
    people_height = people.people_height
    people_bmi = people_weight / (people_height ** 2)
    JkrqList1Log.objects.create(people_id=pid, banzu=banzu, people_blood_high=people_blood_high,
                                people_blood_low=people_blood_low, people_weight=people_weight,
                                people_bmi=people_bmi, people_blood_candy=people_blood_candy)
    people.people_weight = people_weight
    people.people_blood_candy = people_blood_candy
    people.people_blood_high = people_blood_high
    people.people_blood_low = people_blood_low
    people.people_bmi = people_bmi
    people.banzu = banzu
    people.save()
    messages.success(request, f'{people.name}已完成今日检测，舒张压为{people.people_blood_high}，'
                              f'收缩压为{people.people_blood_low}，最新体重指数为{round(people.people_bmi, 2)}。')
    return redirect('jkrq:jkrq_list2')


def logcheck_jkrq(request, list_id):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/jkrq/jkrq_login/')
    role = request.session['info']['role']
    people = JkrqList.objects.get(id=list_id)
    logs = JkrqList1Log.objects.filter(people=people).order_by('-check_date')
    return render(request, "logcheck_jkrq.html", {'people': people, 'logs': logs, 'role': role,
                                                  "admin": ADMIN,
                                                  "xiuche": XIUCHE,
                                                  "xiupei": XIUPEI, })


def people_change_jkrq(request):
    messages.success(request, f'暂未开放')
    return redirect('jkrq:jkrq_list2')

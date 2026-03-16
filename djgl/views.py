import os
import datetime
from collections import defaultdict
from datetime import datetime, timedelta, date
from django.contrib import messages
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login as auth_login

from app01.views import allowed_users, LoginForm, logger
from app01.models import Admin
from . import models
from .models import dangyuan, dangyuanjifen, dangyuanindex, dangyuancgjq, dangjiantext
from django.forms import ModelForm, formset_factory
from django.db.models import Q, Count
from bzrz.models import TeamUser
from django.template.loader import render_to_string


def calculate_workshop_stats():
    # 修车车间班组
    xiu_che_banzu = [1, 4, 5, 8, 9, 10, 16]
    # 修配车间班组
    xiu_pei_banzu = [2, 3, 6, 7, 12, 15]

    # 获取修车车间人数
    xiu_che_total = TeamUser.objects.filter(banzu__in=xiu_che_banzu, retire=1).count()
    # 获取修配车间人数
    xiu_pei_total = TeamUser.objects.filter(banzu__in=xiu_pei_banzu, retire=1).count()

    # 计算总人数
    total = xiu_che_total + xiu_pei_total

    # 计算政治面貌
    xiu_che_mianmao = dangyuan.objects.filter(banzu__in=xiu_che_banzu, retire=1).count()
    xiu_pei_mianmao = dangyuan.objects.filter(banzu__in=xiu_pei_banzu, retire=1).count()

    mianmao = dangyuan.objects.filter(retire=1).count()

    return {
        'total': total,
        'xiu_che_total': xiu_che_total,
        'xiu_pei_total': xiu_pei_total,
        'mianmao': mianmao,
        'xiu_che_mianmao': xiu_che_mianmao,
        'xiu_pei_mianmao': xiu_pei_mianmao,
    }


def get_allowed_banzu(role):
    if role == 'role1':  # 总管理员
        return None  # 可以查看所有班组
    elif role == 'role19':  # 修配管理员
        return [2, 3, 6, 7, 11, 12]  # 只能查看这些班组
    elif role == 'role20':  # 修车管理员
        return [1, 4, 5, 8, 9, 10]  # 只能查看这些班组
    else:
        return None  # 其他角色保持不变


def check_if_user_is_logged_in(request):
    from app01.auth_system import get_user_info
    return get_user_info(request) is not None


def djgl_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "djgl_login.html", {"form": form})
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
                logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了党建管理。')
                
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
                return redirect("/djgl/dangjianguanli0/")
            except Admin.DoesNotExist:
                form.add_error("password", "用户信息不存在！")
                return render(request, "djgl_login.html", {"form": form})
        else:
            form.add_error("password", "账号或密码错误！")
            return render(request, "djgl_login.html", {"form": form})
    return redirect("/djgl/djgl_login/")


def djgl_register(request):
    request.session.clear()
    return redirect('/djgl/dangjianguanli0/')


def search(request):
    query = request.GET.get('q', '')
    if query:
        results = dangyuan.objects.filter(
            Q(name__icontains=query, retire=1) |
            Q(position__icontains=query, retire=1) |
            Q(zerengang__icontains=query, retire=1) |
            Q(zerenqu__icontains=query, retire=1)
        )[:10]
    else:
        results = []
    return render(request, 'search_results.html', {'results': results})


def get_dangyuan_info(request, dangyuan_id):
    dangyuan_obj = get_object_or_404(dangyuan, id=dangyuan_id)
    return render(request, 'dangyuan_tooltip.html', {'dangyuan': dangyuan_obj})


def get_age_distribution(request):
    now_init = datetime.now()
    now = now_init.replace(tzinfo=None)

    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    if banzu == 13:
        if chejian == 1:
            data = dangyuan.objects.filter(banzu__in=[2, 3, 6, 7, 11, 12], retire=1)
        elif chejian == 2:
            data = dangyuan.objects.filter(banzu__in=[1, 4, 5, 8, 9, 10], retire=1)
        else:
            data = dangyuan.objects.filter(banzu=banzu, retire=1)
    elif banzu in [2, 3, 6, 7, 11, 12]:
        data = dangyuan.objects.filter(banzu__in=[2, 3, 6, 7, 11, 12], retire=1)
    elif banzu in [1, 4, 5, 8, 9, 10]:
        data = dangyuan.objects.filter(banzu__in=[1, 4, 5, 8, 9, 10], retire=1)
    else:
        data = dangyuan.objects.filter(banzu=banzu, retire=1)

    age_distribution = {
        'age': 0,
        'age1': 0,
        'age2': 0,
        'age3': 0,
        'age4': 0,
        'age5': 0,
    }

    for row in data:
        birth = row.birth
        if birth:
            delta = relativedelta(now, birth)
            age = delta.years
            if age < 20:
                age_distribution['age'] += 1
            elif 20 <= age < 30:
                age_distribution['age1'] += 1
            elif 30 <= age < 40:
                age_distribution['age2'] += 1
            elif 40 <= age < 50:
                age_distribution['age3'] += 1
            elif 50 <= age < 60:
                age_distribution['age4'] += 1
            else:
                age_distribution['age5'] += 1
    return age_distribution


def dangjianguanli0(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/djgl/djgl_login/')  # 重定向到登录页面

        # 获取登录信息
    info = request.session.get('info', {})
    banzu_logged_in = info.get('banzu', 0)
    chejian = info.get('chejian', 0)
    role = info.get('role_code', None)

    # 年份选择处理
    this_year = date.today().year
    years = [this_year - 2, this_year - 1, this_year]
    selected_year = int(request.GET.get('year', this_year))

    # 定义职位优先级（按顺序）
    priority_positions = ['党总支书记', '车间主任', '纪律检查委员', '群工委员', '组织委员']
    # 根据角色和班组确定标题
    title = "检修党员年龄分布"
    zhibu = "修车修配"
    text = dangjiantext.objects.filter(banzu=15).first()
    text1 = dangjiantext.objects.filter(banzu=16).first()
    if banzu_logged_in == 13:
        dangyuanindex_list = dangyuanindex.objects.filter(Q(year=datetime.now().year, chejian=1) |Q(year=datetime.now().year, chejian=2))
        all_people = dangyuan.objects.filter(retire=1)
        if chejian == 1:  # 修配车间
            title = "修配车间党员年龄分布"
            zhibu = "修配车间"
            dangyuanindex_list = dangyuanindex.objects.filter(year=datetime.now().year, chejian=1)
            # 获取所有可能的相关人员
            all_people = dangyuan.objects.filter(banzu__in=[2, 3, 6, 7, 11, 12], retire=1)
        elif chejian == 2:  # 修车车间
            title = "修车车间党员年龄分布"
            zhibu = "修车车间"
            text = dangjiantext.objects.filter(banzu=16).first()
            dangyuanindex_list = dangyuanindex.objects.filter(year=datetime.now().year, chejian=2)
            # 获取所有可能的相关人员
            all_people = dangyuan.objects.filter(banzu__in=[1, 4, 5, 8, 9, 10], retire=1)
    elif banzu_logged_in in [2, 3, 6, 7, 11, 12]:
        title = "修配车间党员年龄分布"
        zhibu = "修配车间"
        dangyuanindex_list = dangyuanindex.objects.filter(year=datetime.now().year, chejian=1)
        # 获取所有可能的相关人员
        all_people = dangyuan.objects.filter(banzu__in=[2, 3, 6, 7, 11, 12], retire=1)
    elif banzu_logged_in in [1, 4, 5, 8, 9, 10]:
        title = "修车车间党员年龄分布"
        zhibu = "修车车间"
        text = dangjiantext.objects.filter(banzu=16).first()
        dangyuanindex_list = dangyuanindex.objects.filter(year=datetime.now().year, chejian=2)
        # 获取所有可能的相关人员
        all_people = dangyuan.objects.filter(banzu__in=[1, 4, 5, 8, 9, 10], retire=1)

    # 获取用户可以访问的班组列表
    allowed_banzu = get_allowed_banzu(role)
    if allowed_banzu is not None:
        # 如果有特定权限，只显示这些班组的数据
        users = dangyuan.objects.filter(banzu__in=allowed_banzu, retire=1)
    else:
        # 否则按原来的逻辑显示
        users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)

    if users:  # ensure that query set is not empty
        user_sample = users[0]
        banzu_display = user_sample.get_banzu_display()
    else:
        banzu_display = "Unknown banzu"

    # 定义一个匹配函数，判断人员是否匹配我们的优先级职位
    def get_priority(person):
        for idx, position in enumerate(priority_positions):
            if position in person.position:
                return idx
        return len(priority_positions)  # 不匹配的放在最后

    # 筛选并排序
    people = sorted(
        [p for p in all_people if p.position and any(pos in p.position for pos in priority_positions)],
        key=get_priority
    )

    quarter_data = {
        i: {'hongqiqu': [], 'dabiaoqu': [], 'jingshiqu': [], 'xianfenggang': [], 'dabiaogang': [], 'jingshigang': []
            , 'siyoudangyuan': [], 'anquanzhixing': []}
        for i in range(1, 5)}

    for dangyuan_object in dangyuanindex_list:
        quarter = dangyuan_object.quarter
        if dangyuan_object.hongqiqu:
            quarter_data[quarter]['hongqiqu'].append(dangyuan_object.hongqiqu)
        if dangyuan_object.dabiaoqu:
            quarter_data[quarter]['dabiaoqu'].append(dangyuan_object.dabiaoqu)
        if dangyuan_object.jingshiqu:
            quarter_data[quarter]['jingshiqu'].append(dangyuan_object.jingshiqu)
        if dangyuan_object.xianfenggang:
            quarter_data[quarter]['xianfenggang'].append(dangyuan_object.xianfenggang)
        if dangyuan_object.dabiaogang:
            quarter_data[quarter]['dabiaogang'].append(dangyuan_object.dabiaogang)
        if dangyuan_object.jingshigang:
            quarter_data[quarter]['jingshigang'].append(dangyuan_object.jingshigang)
        if dangyuan_object.siyoudangyuan:
            quarter_data[quarter]['siyoudangyuan'].append(dangyuan_object.siyoudangyuan)
        if dangyuan_object.siyoudangyuan:
            quarter_data[quarter]['anquanzhixing'].append(dangyuan_object.anquanzhixing)

    context = {
        'banzu_logged_in': banzu_logged_in,
        'chejian': chejian,
        'banzu_display': banzu_display,
        'people': people,
        'role': role,
        'zhibu': zhibu,
        'years': years,
        'selected_year': selected_year,
        'text': text,
        'text1': text1,
        'quarter_data': quarter_data,
        'age_distribution': get_age_distribution(request),
        'chart_title': title,  # 添加标题变量
        'chart_zhibu': zhibu,  # 添加标题变量
    }
    # 添加统计信息到上下文
    stats = calculate_workshop_stats()
    context.update(stats)

    return render(request, "dangjianguanli0.html", context)


def get_quarter_data(year, chejian, banzu_logged_in, role):
    """
    返回四个季度的数据字典，每季度以下字段都是list[str]:
      - hongqiqu
      - dabiaoqu
      - jingshiqu
      - xianfenggang
      - dabiaogang
      - jingshigang
      - siyoudangyuan
      - anquanzhixing
    """
    # =============================== 确定查询范围 ===============================
    # 如果你需要考虑所有权限的情况（和dangjianguanli0一致）
    # 管理员/支部可看所有
    # chejian/banzu限制所属

    # 下面同你现有的dangjianguanli0方式
    # 修配车间包含 [2,3,6,7,11,12]
    # 修车车间包含 [1,4,5,8,9,10]
    # banzu_logged_in==13为总支/管理员
    if banzu_logged_in == 13:
        # 总支，则要区分chejian
        if chejian == 1:
            qset = dangyuanindex.objects.filter(year=year, chejian=1)
        elif chejian == 2:
            qset = dangyuanindex.objects.filter(year=year, chejian=2)
        else:
            # 若为总支且未选具体车间，则查当年两车间全部
            qset = dangyuanindex.objects.filter(
                Q(year=year, chejian=1) | Q(year=year, chejian=2)
            )
    elif banzu_logged_in in [2, 3, 6, 7, 11, 12]:
        # 修配车间
        qset = dangyuanindex.objects.filter(year=year, chejian=1)
    elif banzu_logged_in in [1, 4, 5, 8, 9, 10]:
        # 修车车间
        qset = dangyuanindex.objects.filter(year=year, chejian=2)
    else:
        # 兜底，为个人所属班组
        qset = dangyuanindex.objects.filter(year=year)

    # =============================== 组织数据结构 ===============================
    # quarter_data: {1: {...}, 2: {...}, 3: {...}, 4: {...}}
    quarter_data = {
        i: {'hongqiqu': [], 'dabiaoqu': [], 'jingshiqu': [], 'xianfenggang': [], 'dabiaogang': [],
            'jingshigang': [], 'siyoudangyuan': [], 'anquanzhixing': []}
        for i in range(1, 5)
    }

    # =============================== 填充数据 ===============================
    for obj in qset:
        q = obj.quarter
        # 防止数据库有问题导致数据不在1-4范围
        if q not in quarter_data:
            continue
        if obj.hongqiqu:
            quarter_data[q]['hongqiqu'].append(obj.hongqiqu)
        if obj.dabiaoqu:
            quarter_data[q]['dabiaoqu'].append(obj.dabiaoqu)
        if obj.jingshiqu:
            quarter_data[q]['jingshiqu'].append(obj.jingshiqu)
        if obj.xianfenggang:
            quarter_data[q]['xianfenggang'].append(obj.xianfenggang)
        if obj.dabiaogang:
            quarter_data[q]['dabiaogang'].append(obj.dabiaogang)
        if obj.jingshigang:
            quarter_data[q]['jingshigang'].append(obj.jingshigang)
        if obj.siyoudangyuan:
            quarter_data[q]['siyoudangyuan'].append(obj.siyoudangyuan)
        if obj.anquanzhixing:
            quarter_data[q]['anquanzhixing'].append(obj.anquanzhixing)

    return quarter_data


def six_area_partial_ajax(request):
    year = int(request.GET.get('year', datetime.now().year))
    this_year = date.today().year
    info = request.session.get('info', {})
    banzu_logged_in = info.get('banzu', 0)
    chejian = info.get('chejian', 0)
    role = info.get('role_code', None)
    quarter_data = get_quarter_data(year, chejian, banzu_logged_in, role)
    return JsonResponse({'html': render_to_string('six_area_partial.html', {
        'quarter_data': quarter_data, 'banzu_logged_in': banzu_logged_in, 'role': role, 'this_year': this_year,
        'year': year,
    }, request=request)})


def siyou_anquan_partial_ajax(request):
    year = int(request.GET.get('year', datetime.now().year))
    info = request.session.get('info', {})
    banzu_logged_in = info.get('banzu', 0)
    chejian = info.get('chejian', 0)
    role = info.get('role_code', None)
    quarter_data = get_quarter_data(year, chejian, banzu_logged_in, role)
    return JsonResponse({'html': render_to_string('siyou_anquan_partial.html', {
        'quarter_data': quarter_data,
    }, request=request)})


@allowed_users(['role19', 'role20'])
def dangjianguanli0_edit(request, quarter):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/djgl/login3/')
    banzu_logged_in = request.session['info']['banzu']
    role = request.session['info']['role_code']
    chejian = request.session['info']['chejian']
    year = datetime.now().year
    users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)

    if users:  # ensure that query set is not empty
        user_sample = users[0]
        banzu_display = user_sample.get_banzu_display()
    else:
        banzu_display = "Unknown banzu"
    dangyuan_list = []
    existing_entry = []
    if role == 'role19':  # 修配车间
        dangyuan_list = dangyuan.objects.filter(banzu__in=[2, 3, 6, 7, 11, 12], retire=1)
        existing_entry = dangyuanindex.objects.filter(year=year, quarter=quarter, chejian=1).first()
    elif role == 'role20':  # 修车车间
        dangyuan_list = dangyuan.objects.filter(banzu__in=[1, 4, 5, 8, 9, 10], retire=1)
        existing_entry = dangyuanindex.objects.filter(year=year, quarter=quarter, chejian=2).first()
    if request.method == "POST":
        try:
            if role == 'role19':  # 修配车间
                dangyuanindex.objects.filter(year=year, quarter=quarter, chejian=1).delete()
            elif role == 'role20':  # 修配车间
                dangyuanindex.objects.filter(year=year, quarter=quarter, chejian=2).delete()
        except dangyuanindex.DoesNotExist:
            pass
        hongqiqu_ids = request.POST.getlist('hongqiqu')
        hongqiqu_names = "\n".join([dangyuan.objects.get(id=id).name for id in hongqiqu_ids])
        dabiaoqu_ids = request.POST.getlist('dabiaoqu')
        dabiaoqu_names = "\n".join([dangyuan.objects.get(id=id).name for id in dabiaoqu_ids])
        jingshiqu_ids = request.POST.getlist('jingshiqu')
        jingshiqu_names = "\n".join([dangyuan.objects.get(id=id).name for id in jingshiqu_ids])
        xianfenggang_ids = request.POST.getlist('xianfenggang')
        xianfenggang_names = "\n".join([dangyuan.objects.get(id=id).name for id in xianfenggang_ids])
        dabiaogang_ids = request.POST.getlist('dabiaogang')
        dabiaogang_names = "\n".join([dangyuan.objects.get(id=id).name for id in dabiaogang_ids])
        jingshigang_ids = request.POST.getlist('jingshigang')
        jingshigang_names = "\n".join([dangyuan.objects.get(id=id).name for id in jingshigang_ids])
        siyoudangyuan_ids = request.POST.getlist('siyoudangyuan')
        siyoudangyuan_names = "\n".join([dangyuan.objects.get(id=id).name for id in siyoudangyuan_ids])
        anquanzhixing_ids = request.POST.getlist('anquanzhixing')
        anquanzhixing_names = "\n".join([dangyuan.objects.get(id=id).name for id in anquanzhixing_ids])

        all_ids = hongqiqu_ids + dabiaoqu_ids + jingshiqu_ids + xianfenggang_ids + dabiaogang_ids + jingshigang_ids + siyoudangyuan_ids + anquanzhixing_ids
        if all_ids:
            user_id = all_ids[0]
            # Save data
            dangyuanindex.objects.create(
                user=dangyuan.objects.get(id=user_id),
                year=year,
                quarter=quarter,
                hongqiqu=hongqiqu_names,
                dabiaoqu=dabiaoqu_names,
                jingshiqu=jingshiqu_names,
                xianfenggang=xianfenggang_names,
                dabiaogang=dabiaogang_names,
                jingshigang=jingshigang_names,
                siyoudangyuan=siyoudangyuan_names,
                anquanzhixing=anquanzhixing_names,
                chejian=chejian,
            )
            messages.success(request, f'修改成功！')
        return redirect('djgl:dangjianguanli0')

    else:
        if existing_entry:
            # 将四优党员也包含进来
            hongqiqu_selected = existing_entry.hongqiqu.split('\n') if existing_entry.hongqiqu else []
            dabiaoqu_selected = existing_entry.dabiaoqu.split('\n') if existing_entry.dabiaoqu else []
            jingshiqu_selected = existing_entry.jingshiqu.split('\n') if existing_entry.jingshiqu else []
            xianfenggang_selected = existing_entry.xianfenggang.split('\n') if existing_entry.xianfenggang else []
            dabiaogang_selected = existing_entry.dabiaogang.split('\n') if existing_entry.dabiaogang else []
            jingshigang_selected = existing_entry.jingshigang.split('\n') if existing_entry.jingshigang else []
            siyoudangyuan_selected = existing_entry.siyoudangyuan.split('\n') if existing_entry.siyoudangyuan else []
            anquanzhixing_selected = existing_entry.anquanzhixing.split('\n') if existing_entry.anquanzhixing else []
        else:
            hongqiqu_selected = []
            dabiaoqu_selected = []
            jingshiqu_selected = []
            xianfenggang_selected = []
            dabiaogang_selected = []
            jingshigang_selected = []
            siyoudangyuan_selected = []
            anquanzhixing_selected = []
    context = {
        'role': role,
        'chejian': chejian,
        'banzu_logged_in': banzu_logged_in,
        'dangyuan_list': dangyuan_list,
        'months': range(1, 13),
        'quarter': quarter,
        'banzu_display': banzu_display,
        'hongqiqu_selected': hongqiqu_selected,
        'dabiaoqu_selected': dabiaoqu_selected,
        'jingshiqu_selected': jingshiqu_selected,
        'xianfenggang_selected': xianfenggang_selected,
        'dabiaogang_selected': dabiaogang_selected,
        'jingshigang_selected': jingshigang_selected,
        'siyoudangyuan_selected': siyoudangyuan_selected,
        'anquanzhixing_selected': anquanzhixing_selected,
    }
    return render(request, "dangjianguanli0_edit.html", context)


class dangyuanForm(ModelForm):
    class Meta:
        model = models.dangyuan
        fields = ['name', 'banzu', 'gender', 'birth', 'join', 'position', 'number', 'zerengang', 'zerenqu',
                  'jiangcheng', 'nationality', 'time', 'retire']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ["name", "birth", "join", "position", 'number', "nationality", "time", 'zerengang']:
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif name == 'zerenqu':
                field.widget = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
            elif name == "jiangcheng":
                field.widget = forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def dangjianguanli(request, banzu):
    # 1. 登录状态与权限校验
    if not check_if_user_is_logged_in(request):
        return HttpResponseRedirect('/djgl/login3/')
    role = request.session['info']['role_code']
    chejian = request.session['info']['chejian']
    allowed_banzu = get_allowed_banzu(role)
    if allowed_banzu is not None and banzu not in allowed_banzu:
        return HttpResponse("您没有权限访问该班组的数据")
    banzu_logged_in = request.session['info']['banzu']

    # 2. 年份选择处理
    this_year = date.today().year
    years = [this_year - 2, this_year - 1, this_year]
    selected_year = int(request.GET.get('year', this_year))

    form = dangyuanForm()
    if banzu_logged_in == 13:
        users = dangyuan.objects.filter(banzu=banzu, retire=1)
        text = dangjiantext.objects.filter(banzu=banzu).first()
    else:
        users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)
        text = dangjiantext.objects.filter(banzu=banzu_logged_in).first()
    if users:
        user_sample = users[0]
        banzu_display = user_sample.get_banzu_display()
    else:
        banzu_display = "Unknown banzu"

    user_ids = [u.id for u in users] if users else []

    # 3. 积分、细项、季度责任岗批量查询
    # 月积分
    jifen_recs = dangyuanjifen.objects.filter(
        user_id__in=user_ids, time__year=selected_year
    )
    jifen_map = defaultdict(lambda: defaultdict(list))  # user_id => 月份 => [rec,...]
    for rec in jifen_recs:
        jifen_map[rec.user_id][rec.time.month].append(rec)

    # 季度责任岗
    cgjq_recs = dangyuancgjq.objects.filter(
        user_id__in=user_ids, year=selected_year
    )
    cgjq_zrgang = defaultdict(dict)  # user_id => quarter => display
    cgjq_zrqu = defaultdict(dict)
    for rec in cgjq_recs:
        cgjq_zrgang[rec.user_id][rec.quarter] = rec.get_zerengang_display()
        cgjq_zrqu[rec.user_id][rec.quarter] = rec.get_zerenqu_display()

    # 4. 组装结果
    for user in users:
        user.jifen = {}
        user.jifen_popover = {}
        for month in range(1,13):
            month_recs = jifen_map[user.id][month]
            user.jifen[month] = sum([r.jifen or 0 for r in month_recs])
            content = ""
            for kind, prefix in [
                ('zzsz',  '政治素质'),
                ('ywjn',  '业务技能'),
                ('gzyj',  '工作业绩'),
                ('lxqz',  '联系群众'),
                ('jfxd',  '加分项点')
            ]:
                items = [getattr(r, kind) for r in month_recs if getattr(r, kind)]
                if items:
                    content += f"<b>{prefix}：</b><br>" + "<br>".join(items) + "<br>"
            user.jifen_popover[month] = content or "暂无详细内容"
        user.quarter_zerengang = cgjq_zrgang.get(user.id, {})
        user.quarter_zerenqu = cgjq_zrqu.get(user.id, {})

    # 5. 渲染
    context = {
        'banzu_logged_in': banzu_logged_in,
        'users': users,
        'banzu': banzu,
        'chejian': chejian,
        'role': role,
        'text': text,
        'form': form,
        'years': years,
        'selected_year': selected_year,
        'banzu_display': banzu_display,
    }
    return render(request, "dangjianguanli.html", context)

def dangyuanjifen_ajax(request):
    year = int(request.GET.get('year', date.today().year))
    banzu = int(request.GET.get('banzu'))
    if not check_if_user_is_logged_in(request):
        return JsonResponse({'error': 'not_logged_in'}, status=401)
    role = request.session['info']['role_code']
    allowed_banzu = get_allowed_banzu(role)
    if allowed_banzu is not None and banzu not in allowed_banzu:
        return JsonResponse({'error': 'no_permission'}, status=403)
    banzu_logged_in = request.session['info']['banzu']
    if banzu_logged_in == 13:
        users = dangyuan.objects.filter(banzu=banzu, retire=1)
    else:
        users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)

    user_ids = [u.id for u in users] if users else []

    jifen_recs = dangyuanjifen.objects.filter(
        user_id__in=user_ids, time__year=year
    )
    jifen_map = defaultdict(lambda: defaultdict(list))
    for rec in jifen_recs:
        jifen_map[rec.user_id][rec.time.month].append(rec)
    cgjq_recs = dangyuancgjq.objects.filter(user_id__in=user_ids, year=year)
    cgjq_zrgang = defaultdict(dict)
    cgjq_zrqu = defaultdict(dict)
    for rec in cgjq_recs:
        cgjq_zrgang[rec.user_id][rec.quarter] = rec.get_zerengang_display()
        cgjq_zrqu[rec.user_id][rec.quarter] = rec.get_zerenqu_display()

    for user in users:
        user.jifen = {}
        user.jifen_popover = {}
        for month in range(1, 13):
            month_recs = jifen_map[user.id][month]
            user.jifen[month] = sum([r.jifen or 0 for r in month_recs])
            content = ""
            for kind, prefix in [
                ('zzsz',  '政治素质'),
                ('ywjn',  '业务技能'),
                ('gzyj',  '工作业绩'),
                ('lxqz',  '联系群众'),
                ('jfxd',  '加分项点')
            ]:
                items = [getattr(r, kind) for r in month_recs if getattr(r, kind)]
                if items:
                    content += f"<b>{prefix}：</b><br>" + "<br>".join(items) + "<br>"
            user.jifen_popover[month] = content or "暂无详细内容"
        user.quarter_zerengang = cgjq_zrgang.get(user.id, {})
        user.quarter_zerenqu = cgjq_zrqu.get(user.id, {})

    table_html = render_to_string('jifen_table_partial.html', {
        'users': users,
        'banzu': banzu,
        'selected_year': year,  # 注意是year参数
    })
    return JsonResponse({'table_html': table_html})


def dangyuancgjq_ajax(request):
    year = int(request.GET.get('year', date.today().year))
    banzu = int(request.GET.get('banzu'))
    if not check_if_user_is_logged_in(request):
        return JsonResponse({'error': 'not_logged_in'}, status=401)
    role = request.session['info']['role_code']
    allowed_banzu = get_allowed_banzu(role)
    if allowed_banzu is not None and banzu not in allowed_banzu:
        return JsonResponse({'error': 'no_permission'}, status=403)
    banzu_logged_in = request.session['info']['banzu']
    if banzu_logged_in == 13:
        users = dangyuan.objects.filter(banzu=banzu, retire=1)
    else:
        users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)

    user_ids = [u.id for u in users] if users else []

    cgjq_recs = dangyuancgjq.objects.filter(user_id__in=user_ids, year=year)
    cgjq_zrgang = defaultdict(dict)
    cgjq_zrqu = defaultdict(dict)
    for rec in cgjq_recs:
        cgjq_zrgang[rec.user_id][rec.quarter] = rec.get_zerengang_display()
        cgjq_zrqu[rec.user_id][rec.quarter] = rec.get_zerenqu_display()
    for user in users:
        user.quarter_zerengang = cgjq_zrgang.get(user.id, {})
        user.quarter_zerenqu = cgjq_zrqu.get(user.id, {})

    cgjq_html = render_to_string('cgjq_table_partial.html', {
        'users': users,
        'banzu': banzu,
        'selected_year': year,
    })
    return JsonResponse({'cgjq_html': cgjq_html})


class dangyuancgjqForm(ModelForm):
    class Meta:
        model = models.dangyuancgjq
        fields = ['zerengang', 'zerenqu']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs = {'class': 'form-control'}


def dangyuancgjq_edit(request, banzu, quarter):
    current_year = date.today().year
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/djgl/login3/')
    banzu_logged_in = request.session['info']['banzu']
    role = request.session['info']['role_code']
    chejian = request.session['info']['chejian']
    if banzu_logged_in == 13:
        users = dangyuan.objects.filter(banzu=banzu, retire=1)
    else:
        users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)
    if users:  # ensure that query set is not empty
        user_sample = users[0]
        banzu_display = user_sample.get_banzu_display()
    else:
        banzu_display = "Unknown banzu"

    dangyuancgjqFormSet = formset_factory(dangyuancgjqForm, extra=0)

    if request.method == 'POST':
        formset = dangyuancgjqFormSet(request.POST)
        if formset.is_valid():
            messages.success(request, f'修改成功！')
            for index, form in enumerate(formset):
                user = users[index]
                user_cgjq_record = dangyuancgjq.objects.filter(user=user, quarter=quarter, year=current_year).first()
                if user_cgjq_record:
                    user_cgjq_record.zerengang = form.cleaned_data.get('zerengang')
                    user_cgjq_record.zerenqu = form.cleaned_data.get('zerenqu')
                    user_cgjq_record.save()
            return redirect('djgl:dangjianguanli', banzu=banzu)

    else:
        initial_data = []
        for user in users:
            user_cgjq_record = dangyuancgjq.objects.filter(user=user, quarter=quarter, year=current_year).first()
            if not user_cgjq_record:
                user_cgjq_record = dangyuancgjq(user=user, banzu=user.banzu, quarter=quarter, year=current_year)
                user_cgjq_record.save()
            initial_data.append({
                'zerengang': user_cgjq_record.zerengang,
                'zerenqu': user_cgjq_record.zerenqu,
            })
        formset = dangyuancgjqFormSet(initial=initial_data)
    user_and_forms = list(zip(users, formset))
    quarter = quarter
    context = {
        'banzu_logged_in': banzu_logged_in,
        'users': users,
        'formset': formset,
        'banzu': banzu,
        'chejian': chejian,
        'role': role,
        'quarter': quarter,
        'banzu_display': banzu_display,
        'user_and_forms': user_and_forms,
    }
    return render(request, "dangyuancgjq_edit.html", context)


def getNewName4(file_type, log):
    new_name = f"{file_type}-{log.name}-{log.id}.jpg"
    return new_name


def license8(request, id):
    log = dangyuan.objects.get(id=id)
    previous_page = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        if 'pic' not in request.FILES:
            messages.warning(request, f'未添加任何照片，无法上传，请添加照片后重试！')
            return redirect('djgl:dangjianguanli', banzu=log.banzu)
        file = request.FILES['pic']
        log = dangyuan.objects.filter(id=id).first()
        # 根据user.name和jineng生成新的文件名
        new_name = getNewName4('pic', log)
        # 将要保存的地址和文件名称
        dir_name = os.path.join('E:\\credential', 'dangyuan')
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(dir_name, exist_ok=True)
        file_path = os.path.join(dir_name, new_name)
        # 分块保存image
        content = file.chunks()
        with open(file_path, 'wb') as f:
            for i in content:
                f.write(i)
        # 更新数据库中的字段
        dangyuan.objects.filter(id=id).update(pic=new_name)
        messages.success(request, f'图片上传成功！')
        return redirect('djgl:dangjianguanli', banzu=log.banzu)
    return render(request, 'license8.html', {'log': log})


@csrf_exempt
def add_dangyuan(request, banzu):
    new_log = dangyuan(banzu=banzu, name="新党员", gender=1, retire=1)
    try:
        new_log.save()
        messages.success(request, f'新增成功，已添加一位新党员！')
        redirect_url = reverse('djgl:dangjianguanli', args=[banzu])
        return HttpResponseRedirect(redirect_url)
    except Exception as e:
        # TODO: handle exception here, like showing error page
        pass


@csrf_exempt
def edit_dangyuan(request):
    if request.method == 'POST':
        log_id = request.POST.get('logid')
        # 检查是否存在具有给定 ID 的 TeamLog 对象
        log = dangyuan.objects.filter(id=log_id)
        log = log.first()
        log.name = request.POST.get('name')
        log.banzu = request.POST.get('banzu')
        log.gender = request.POST.get('gender')
        log.retire = request.POST.get('retire')
        birth = request.POST.get('birth')
        log.birth = datetime.strptime(birth, '%Y-%m-%d').date() if birth else None
        join = request.POST.get('join')
        log.join = datetime.strptime(join, '%Y-%m-%d').date() if join else None
        log.position = request.POST.get('position')
        log.number = request.POST.get('number')
        log.jiangcheng = request.POST.get('jiangcheng')
        log.zerengang = request.POST.get('zerengang')
        log.zerenqu = request.POST.get('zerenqu')
        log.nationality = request.POST.get('nationality')
        time = request.POST.get('time')
        log.time = datetime.strptime(time, '%Y-%m-%d').date() if time else None
        log.save()
        messages.success(request, f'{log.name}党员信息修改成功！')
        return JsonResponse({
            'message': f'The log with id {log_id} was successfully updated.',
        })
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


class dangyuanjifenForm(ModelForm):
    class Meta:
        model = models.dangyuanjifen
        fields = ['jifen', 'zzsz', 'ywjn', 'gzyj', 'lxqz', 'jfxd']
        # widgets = {
        #     'jifen': forms.TextInput(attrs={'style': 'background-color: #e4b9b9;'}),
        #     'zzsz': forms.Textarea(attrs={'style': 'background-color: #e4b9b9;'}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == ['jifen', 'zzsz', 'ywjn', 'gzyj', 'lxqz', 'jfxd']:
                field.widget.attrs.update({'rows': 3, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def dangyuanjifen_edit(request, banzu, month):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/djgl/login3/')

    role = request.session['info']['role_code']
    chejian = request.session['info']['chejian']
    allowed_banzu = get_allowed_banzu(role)

    # 检查是否有权限编辑该班组
    if allowed_banzu is not None:
        if banzu not in allowed_banzu:
            return HttpResponse("您没有权限编辑该班组的数据")
    banzu_logged_in = request.session['info']['banzu']
    if banzu_logged_in == 13:
        users = dangyuan.objects.filter(banzu=banzu, retire=1)
    else:
        users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)
    if users:  # ensure that query set is not empty
        user_sample = users[0]
        banzu_display = user_sample.get_banzu_display()
    else:
        banzu_display = "Unknown banzu"

    start_date = datetime(datetime.now().year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1)

    dangyuanjifenFormSet = formset_factory(dangyuanjifenForm, extra=0)

    if request.method == 'POST':
        formset = dangyuanjifenFormSet(request.POST)
        if formset.is_valid():
            messages.success(request, f'修改成功！')
            for index, form in enumerate(formset):  # 注意这里修改为enumerate
                data1 = request.POST.getlist(f'form-{index}-multiple_select_1')
                data2 = request.POST.getlist(f'form-{index}-multiple_select_2')
                data3 = request.POST.getlist(f'form-{index}-multiple_select_3')
                data4 = request.POST.getlist(f'form-{index}-multiple_select_4')
                data5 = request.POST.getlist(f'form-{index}-multiple_select_5')
                user = users[index]
                user_jifen_record = dangyuanjifen.objects.filter(user=user, time__gte=start_date,
                                                                 time__lt=end_date).first()
                if user_jifen_record:  # 如果存在记录则更新
                    user_jifen_record.jifen = form.cleaned_data.get('jifen')
                    user_jifen_record.zzsz = "；".join(data1) if data1 else None
                    user_jifen_record.ywjn = "；".join(data2) if data2 else None
                    user_jifen_record.gzyj = "；".join(data3) if data3 else None
                    user_jifen_record.lxqz = "；".join(data4) if data4 else None
                    user_jifen_record.jfxd = "；".join(data5) if data5 else None
                    user_jifen_record.save()
            return redirect('djgl:dangjianguanli', banzu=banzu)

    else:
        initial_data = []
        for user in users:
            start_date = datetime(datetime.now().year, month, 1)
            end_date = (start_date + timedelta(days=31)).replace(day=1)
            user_jifen_record = dangyuanjifen.objects.filter(user=user, time__gte=start_date, time__lt=end_date).first()
            # 如果不存在记录，就创建新的
            if not user_jifen_record:
                user_jifen_record = dangyuanjifen(
                    user=user, banzu=user.banzu, jifen=0, time=start_date,)  # 初始化新字段
                user_jifen_record.save()
            initial_data.append({
                'jifen': user_jifen_record.jifen or 0,
                'zzsz': user_jifen_record.zzsz.split("；") if user_jifen_record.zzsz else [],
                'ywjn': user_jifen_record.ywjn.split("；") if user_jifen_record.ywjn else [],
                'gzyj': user_jifen_record.gzyj.split("；") if user_jifen_record.gzyj else [],
                'lxqz': user_jifen_record.lxqz.split("；") if user_jifen_record.lxqz else [],
                'jfxd': user_jifen_record.jfxd.split("；") if user_jifen_record.jfxd else [],
            })
        formset = dangyuanjifenFormSet(initial=initial_data)
    user_and_forms = list(zip(users, formset))
    month = month
    context = {
        'banzu_logged_in': banzu_logged_in,
        'users': users,
        'formset': formset,
        'banzu': banzu,
        'chejian': chejian,
        'role': role,
        'month': month,
        'banzu_display': banzu_display,
        'user_and_forms': user_and_forms,
        'zzsz_options': [
            "参加组织生活和党内活动未按规定佩戴党员徽章，扣2分/次",
            "未完成党支部布置的任务，扣2分/次",
            "无故缺席党支部“三会一课”等组织生活，扣5分/次",
            "无故迟到或早退，扣2分/次",
            "不按时、足额交纳党费，扣3分/次",
            "政治敏感性不强，在任何场合发表、转发不当言论，扣5分/次，造成影响，失格",
            "发生段党委明确的职工“思想政治素质不合格”情形，受到党纪、企业纪律处分，违纪违规被处理，扣25分",
        ],
        'ywjn_options': [
            "业务学习不积极主动，不能熟练掌握本职岗位的应知应会，扣5分",
            "执行作业标准有偏差，扣3分",
            "示范带动作用不够，不能积极带动身边群众学技练功，扣3分",
            "无故不参加培训。或者参加各类培训班表现不佳，存在违反培训纪律和培训成绩不合格情况，扣5分",
            "工作质量不高，存在明显错误，扣1分/次",
            "因责任原因发生货车检修质量问题，扣10分/次",
        ],
        'gzyj_options': [
            "两违考核情况，B类扣3分，A类扣5分",
            "违反劳动纪律，扣2分/次",
            "没有按进度完成分配的工作任务，扣2分/项",
            "因工作差错，被段通报批评，扣3分/次",
            "被集团公司通报批评，扣5分/次",
            "在党内主题实践中表现不佳，扣3分/次",
        ],
        'lxqz_options': [
            "发现队伍不稳定的问题，未及时反馈或制止的，责任区职工思想异常情况未报告，扣5分/次",
            "对身边群众的矛盾、问题视而不见，不积极帮助化解，扣3分/次",
            "损害职工群众利益，造成不良影响，扣5分/次",
            "未落实帮带责任，扣2分/次",
            "责任区内职工发生“两违的或违章大王以及责任事故，根据情形扣1分-15分/次",
            "不按时、足额交纳党费，扣3分/次",
            "服务意识不强，有党员群众中向上级反映且情况属实",
            "工作态度不端正，存在与职工推诿扯皮，与部门讨价还价，收到段通报批评或领导公开批评，视情况扣3分-5分/次",
        ],
        'jfxd_options': [
            "参加段级技能竞赛、技术比武等活动，获得名次加3分/次",
            "参加集团公司级技能竞赛、技术比武等活动获得名次加5分/次",
            "参加国铁集团级技能竞赛、技术比武等活动获得名次加10分/次",
            "参加各类业务考试、获得名次，视情况加加1-5分/次",
            "发现影响安全的重大故障受到段级通报奖励，加3分/件",
            "集团公司级通报奖励，加5分/件",
            "国铁集团级通报奖励，加10分/件",
            "主动参加立项攻关，加2分/项",
            "形成立项攻关成果并获得专利，加5-15分/项",
            "主动参与突击奉献，加1-3分/次",
            "主动讲授党课，加3分/次",
            "提出创新意见建议，受到采纳，并组织实施的，视情况最高加10分",
            "在车间、班组、科室承担工作任务多，责任大，视情况最高加5分",
            "责任区内职工群众发现影响安全的重大故障受到段级及以上通报奖励，加1-3分/件",
            "主动帮助其他职工共同完成生产任务或车间、班组、科室安排的临时工作任务，加1-3分/件",
            "在各类重点工作中表现优异，受到上级充分肯定，加2-5分/次",
            "在工作、生活中，有见义勇为、主动担当、热心助人等，受到群众好评的，视情况最高加20分",
            "其他认定可以加分的项点，由党总支总评决定",
        ],
    }
    return render(request, "dangyuanjifen_edit.html", context)


class DangjiantextForm(ModelForm):
    class Meta:
        model = models.dangjiantext
        fields = ['jieshao', 'neirong']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name == ['jieshao', 'neirong']:
                field.widget.attrs.update({'rows': 3, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def dangjiantext_edit(request, banzu):
    logged_in = check_if_user_is_logged_in(request)
    if not logged_in:
        return HttpResponseRedirect('/djgl/login3/')

    banzu_logged_in = request.session['info']['banzu']
    users = dangyuan.objects.filter(banzu=banzu_logged_in, retire=1)
    role = request.session['info']['role_code']
    chejian = request.session['info']['chejian']

    if users:  # ensure that query set is not empty
        user_sample = users[0]
        banzu_display = user_sample.get_banzu_display()
    else:
        banzu_display = ""

    instance = dangjiantext.objects.filter(banzu=banzu_logged_in).first()
    if role == 'role19':  # 修配车间
        instance = dangjiantext.objects.filter(banzu=15).first()
    elif role == 'role20':  # 修车车间
        instance = dangjiantext.objects.filter(banzu=16).first()

    if request.method == 'POST':
        form = DangjiantextForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            f = form.save(commit=False)
            f.banzu = banzu_logged_in
            if role == 'role19':  # 修配车间
                f.banzu = 15
            elif role == 'role20':  # 修车车间
                f.banzu = 16
            f.save()
            messages.success(request, f'修改成功！')
            if banzu_logged_in == 13:
                return redirect('djgl:dangjianguanli0')
            else:
                return redirect('djgl:dangjianguanli', banzu=banzu)
        else:
            form = DangjiantextForm(instance=instance)

    else:
        form = DangjiantextForm(instance=instance)

    context = {
        'banzu_logged_in': banzu_logged_in,
        'users': users,
        'banzu': banzu,
        'chejian': chejian,
        'banzu_display': banzu_display,
        'form': form,
        'role': role,
    }

    return render(request, "dangjiantext_edit.html", context)


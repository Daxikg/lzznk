import calendar
import datetime
import calendar

from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login

from app01.views import LoginForm, logger, check_if_user_is_logged_in
from app01 import models
from .models import Employee, DailyScore, Accounting

ADMIN = ["总管理员", "调度员", "安全员", "技术员"]
XIUPEI = ["轮轴班", "台车班", "轮轴班手持机", "车钩班", "探伤班", "信息班", "修配管理员"]
XIUCHE = ["架车班", "架车班手持机", "车体班", "预修班", "调车组", "内制动班", "外制动班", "修车管理员"]


def gfcx_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "gfcx_login.html", {"form": form})
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
                logger.info(f'{username} 在{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了工分查询。')
                
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
                return redirect('/gfcx/gfcx_score_verification/')
            except models.Admin.DoesNotExist:
                form.add_error("password", "用户信息不存在！")
                return render(request, "gfcx_login.html", {"form": form})
        else:
            form.add_error("password", "账号或密码错误！")
            return render(request, "gfcx_login.html", {"form": form})
    return render(request, "gfcx_login.html", {"form": form})


def register_gfcx(request):
    from app01.auth_system import unified_logout
    return unified_logout(request, redirect_url='/gfcx/gfcx_login/')


@csrf_exempt
def import_excel_score(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/gfcx/gfcx_login/')  # 重定向到登录页面

    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if excel_file:
            try:
                # 读取Excel文件
                df = pd.read_excel(excel_file)

                def is_date_column(col):
                    if isinstance(col, str) and '.' in col:
                        try:
                            float(col)
                            return True
                        except:
                            return False
                    if isinstance(col, float):
                        return True
                    return False

                def get_month_day(col):
                    if isinstance(col, float):
                        month = int(col)
                        day = int(round((col - month) * 100))
                        return month, day
                    elif isinstance(col, str):
                        month, day = map(int, col.split('.'))
                        return month, day
                    else:
                        raise ValueError("未知的日期列类型")

                # 获取当前年份
                current_year = timezone.now().year
                current_month = timezone.now().month

                # 获取所有日期列
                date_columns = [col for col in df.columns if is_date_column(col)]
                if not date_columns:
                    raise ValueError("Excel文件中没有找到日期列")

                # 获取要处理的月份（从第一个日期列中获取）
                target_month, _ = get_month_day(date_columns[0])

                # 如果目标月份大于当前月份，则说明是上一年的成绩
                if target_month > current_month:
                    current_year -= 1

                # 获取目标月份的最后一天
                _, last_day = calendar.monthrange(current_year, target_month)
                target_date = datetime.datetime(current_year, target_month, last_day)

                # 检查数据库中是否已存在该月份的数据
                existing_employees = Employee.objects.filter(
                    banzu=banzu,
                    created_time__year=current_year,
                    created_time__month=target_month
                )

                if existing_employees.exists():
                    # 获取这些员工相关的所有DailyScore记录
                    related_scores = DailyScore.objects.filter(
                        employee__in=existing_employees
                    )

                    # 删除所有相关的DailyScore记录
                    related_scores.delete()

                    # 删除这些员工记录
                    existing_employees.delete()

                    print(f"删除了{target_month}月份的现有数据")
                else:
                    print(f"没有找到{target_month}月份的现有数据，将创建新数据")

                # 从第3行开始处理（索引从0开始，所以是2）
                for index in range(1, len(df)):
                    # 使用iloc确保正确获取行数据
                    row = df.iloc[index]

                    # 获取员工基本信息
                    name = str(row.iloc[0]).strip()
                    gongzhong = str(row.iloc[1]).strip()
                    gonghao = str(row.iloc[2]).strip()

                    # 跳过空行
                    if not name or pd.isna(name):
                        continue

                    # 创建新的员工记录
                    employee = Employee.objects.create(
                        name=name,
                        gongzhong=gongzhong,
                        gonghao=gonghao,
                        banzu=banzu,
                        chejian=chejian,
                        created_time=target_date  # 设置为该月份的最后一天
                    )

                    # 遍历所有日期列

                    for date_col in date_columns:
                        month, day = get_month_day(date_col)
                        if month != target_month:
                            continue

                        # 获取当前日期列的索引
                        col_index = df.columns.get_loc(date_col)

                        # 确保索引在有效范围内
                        if col_index + 3 >= len(row):
                            continue

                        # 获取分数
                        work_score = float(row.iloc[col_index]) if not pd.isna(row.iloc[col_index]) else 0
                        study_score = float(row.iloc[col_index + 1]) if not pd.isna(row.iloc[col_index + 1]) else 0
                        business_score = float(row.iloc[col_index + 2]) if not pd.isna(
                            row.iloc[col_index + 2]) else 0
                        holiday_score = float(row.iloc[col_index + 3]) if not pd.isna(
                            row.iloc[col_index + 3]) else 0

                        # 创建日期
                        try:
                            score_date = datetime.datetime(current_year, month, day)
                        except ValueError:
                            # 如果日期无效（比如2月30日），跳过
                            continue

                        # 创建新的记录
                        DailyScore.objects.create(
                            employee=employee,
                            date=score_date,
                            work_score=work_score,
                            study_score=study_score,
                            business_score=business_score,
                            holiday_score=holiday_score
                        )

                messages.success(request, 'Excel数据导入成功！')
            except Exception as e:
                error_msg = f'导入失败：{str(e)}'
                print(f"错误详情: {error_msg}")
                messages.error(request, error_msg)
        return redirect('/gfcx/gfcx_score_verification/')
    return render(request, 'import_excel_score.html',
                  {"role": role, "admin": ADMIN,
                   "xiuche": XIUCHE,
                   "xiupei": XIUPEI, })


@csrf_exempt
def import_excel_accounting(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/gfcx/gfcx_login/')  # 重定向到登录页面
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if excel_file:
            try:
                # 读取Excel文件
                df = pd.read_excel(excel_file)

                # 获取当前年份
                current_year = timezone.now().year
                current_month = timezone.now().month

                # 从第二行第六列获取月份，只取数字部分
                month_str = df.iloc[1, 5]  # 获取"1月"这样的字符串
                month = int(month_str.split('月')[0])  # 只取"1"这个数字

                if month > current_month:
                    current_year -= 1

                # 删除已存在的数据
                Accounting.objects.filter(
                    banzu=banzu,
                    chejian=chejian,
                    year=current_year,
                    month=month
                ).delete()

                # 处理每一行数据
                for index, row in df.iterrows():

                    try:
                        # 获取数据并处理带"天"的字符串
                        name = str(row[0]).strip()  # 姓名
                        gongzhong = str(row[3]).strip()  # 工种
                        gonghao = str(row[4]).strip()  # 工号
                        total_days_str = str(row[6]).strip()  # 打分总天数
                        main_area_days_str = str(row[7]).strip()  # 本工区打分天数
                        other_area_days_str = str(row[8]).strip()  # 其他工区打分天数

                        # 提取数字部分
                        total_days = int(total_days_str.split('天')[0]) if '天' in total_days_str else int(
                            total_days_str)
                        main_area_days = int(main_area_days_str.split('天')[0]) if '天' in main_area_days_str else int(
                            main_area_days_str)
                        other_area_days = int(
                            other_area_days_str.split('天')[0]) if '天' in other_area_days_str else int(
                            other_area_days_str)

                        # 其他数值字段保持不变
                        base_coefficient = float(row[9])  # 个人挂钩基数
                        start_score = float(row[10])  # 起始分
                        main_area_score = float(row[11])  # 本工区定额所得分
                        main_area_amount = float(row[12])  # 本工区定额所得金额
                        other_area_score = float(row[13])  # 其他工区定额所得分
                        other_area_amount = float(row[14])  # 其他工区定额所得金额
                        status = str(row[15]).strip()  # 考核状态
                        remarks = str(row[16]).strip()  # 备注

                        # 创建Accounting记录
                        accounting = Accounting.objects.create(
                            name=name,
                            banzu=banzu,
                            chejian=chejian,
                            gongzhong=gongzhong,
                            gonghao=gonghao,
                            year=current_year,
                            month=month,
                            total_days=total_days,
                            main_area_days=main_area_days,
                            other_area_days=other_area_days,
                            base_coefficient=base_coefficient,
                            start_score=start_score,
                            main_area_score=main_area_score,
                            main_area_amount=main_area_amount,
                            other_area_score=other_area_score,
                            other_area_amount=other_area_amount,
                            status=status,
                            remarks=remarks
                        )

                    except Exception as e:
                        messages.error(request, f"处理第{index + 1}行数据时出错: {str(e)}")
                        continue

                messages.success(request, 'Excel数据导入成功！')
            except Exception as e:
                messages.error(request, f'导入失败：{str(e)}')

        return redirect('/gfcx/gfcx_accounting/')

    return render(request, 'import_excel_accounting.html', {
        "role": role,
        "banzu": banzu,
        "chejian": chejian,
    })


def gfcx_score_verification(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/gfcx/gfcx_login/')

    # 获取用户信息
    role = request.session['info']['role']
    user_banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    # 获取筛选参数（支持GET和POST请求）
    if request.method == 'POST':
        selected_banzu = request.POST.get('banzu')
        selected_year = request.POST.get('year')
        selected_month = request.POST.get('month')
    else:
        selected_banzu = request.GET.get('banzu', '')
        selected_year = request.GET.get('year', '')
        selected_month = request.GET.get('month', '')
    
    # 获取分页参数
    page_number = request.GET.get('page', 1)
    # 确保page_number是有效的整数
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1

    # 获取所有年份数据
    all_dates = DailyScore.objects.dates('date', 'month')
    all_years = sorted(set(d.year for d in all_dates), reverse=True)

    # 根据用户角色和车间获取可选的班组列表
    if user_banzu == 13:  # 管理员
        if chejian == 0:  # 总管理员
            allowed_banzu_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]
        elif chejian == 1:
            allowed_banzu_list = [2, 3, 6, 7, 12]
        elif chejian == 2:
            allowed_banzu_list = [1, 4, 5, 8, 9, 10]
        else:
            allowed_banzu_list = []  # 如果车间号不匹配，返回空列表
    else:
        allowed_banzu_list = [user_banzu]  # 普通用户只能看到自己的班组

    # 获取所有班组列表（只显示允许的班组）
    banzu_choices = [(key, value) for key, value in Employee.banzu_choices if key in allowed_banzu_list]

    # 构建基础查询条件
    query_conditions = {}

    # 如果是普通管理员或普通用户，添加车间筛选条件
    if user_banzu == 13 and chejian != 0:  # 普通管理员
        query_conditions['chejian'] = chejian
    elif user_banzu != 13:  # 普通用户
        query_conditions['chejian'] = chejian

    # 如果是管理员，添加班组筛选条件
    if user_banzu == 13:
        query_conditions['banzu__in'] = allowed_banzu_list
    else:
        query_conditions['banzu'] = user_banzu

    # 如果有额外的筛选条件（班组、年份、月份），添加到查询条件中
    if selected_banzu:
        query_conditions['banzu'] = int(selected_banzu)

    # 获取符合条件的班组
    teams = Employee.objects.filter(**query_conditions).values('chejian', 'banzu').distinct()

    # 准备数据
    team_data = []
    for team in teams:
        # 获取车间和班组名称
        chejian_name = dict(Employee.chejian_choices).get(team['chejian'])
        banzu_name = dict(Employee.banzu_choices).get(team['banzu'])

        # 获取当前班组的所有员工
        employees = Employee.objects.filter(
            chejian=team['chejian'],
            banzu=team['banzu']
        )

        # 构建每日评分查询条件
        daily_scores_conditions = {
            'employee__in': employees
        }

        # 添加年份和月份筛选条件
        if selected_year:
            daily_scores_conditions['date__year'] = int(selected_year)
        if selected_month:
            daily_scores_conditions['date__month'] = int(selected_month)

        # 获取每日评分数据
        daily_scores = DailyScore.objects.filter(**daily_scores_conditions)

        # 获取所有有数据的月份
        all_dates = sorted(set((d.date.year, d.date.month) for d in daily_scores), reverse=True)

        # 获取所有月份的数据
        month_scores = []
        for y, m in all_dates:
            # 获取当月所有有评分记录的员工
            month_employees = Employee.objects.filter(
                chejian=team['chejian'],
                banzu=team['banzu'],
                dailyscore__date__year=y,
                dailyscore__date__month=m
            ).distinct()

            # 计算参与考核人数（只计算当月有评分记录的员工）
            participant_count = month_employees.count()

            # 计算当月分值
            monthly_score = DailyScore.objects.filter(
                employee__in=employees,
                date__year=y,
                date__month=m
            ).aggregate(total=Sum('work_score'))['total'] or 0

            # 对结果四舍五入，取小数点后 2 位
            monthly_score = round(monthly_score, 2)

            # 计算人均分值
            average_score = monthly_score / participant_count if participant_count > 0 else 0

            month_scores.append({
                'year': y,
                'month': m,
                'monthly_score': monthly_score,
                'participant_count': participant_count,
                'average_score': round(average_score, 2),
                'confirm_status': '已核算'
            })

        # 为每个月份记录创建独立的条目
        for month_score in month_scores:
            team_data.append({
                'chejian': team['chejian'],
                'banzu': team['banzu'],
                'chejian_name': chejian_name,
                'banzu_name': banzu_name,
                'month_score': month_score,  # 单个月份数据
                'id': f"{team['chejian']}_{team['banzu']}_{month_score['year']}_{month_score['month']}"
            })

    # 分页处理 - 按照实际显示的行数分页
    from django.core.paginator import Paginator
    paginator = Paginator(team_data, 20)  # 每页显示20条记录
    page_obj = paginator.get_page(page_number)

    return render(request, 'gfcx_score_verification.html', {
        'year': selected_year or timezone.now().year,
        'month': selected_month or timezone.now().month,
        'teams': page_obj,  # 传递分页对象而不是原始数据
        'page_obj': page_obj,  # 传递分页对象用于模板
        'all_years': all_years,
        'banzu_choices': banzu_choices,
        'role': role,
        'banzu': user_banzu,
        'selected_banzu': selected_banzu,
        'selected_year': selected_year,
        'selected_month': selected_month,
        "admin": ADMIN,
        "xiuche": XIUCHE,
        "xiupei": XIUPEI,
    })


def gfcx_score(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/gfcx/gfcx_login/')  # 重定向到登录页面
    # 获取筛选参数
    role = request.session['info']['role']
    chejian = request.GET.get('chejian')
    banzu = request.GET.get('banzu')
    year = request.GET.get('year')
    month = request.GET.get('month')
    score_type = request.GET.get('score_type', 'work')  # 新增分数类型参数，默认显示工作积分

    # 如果没有从URL获取到年月，使用POST数据或默认值
    if not year or not month:
        if request.method == 'POST':
            year = int(request.POST.get('year'))
            month = int(request.POST.get('month'))
        else:
            now = timezone.now()
            year = now.year
            month = now.month
    else:
        year = int(year)
        month = int(month)

    # 根据筛选条件获取当月的员工
    employees = Employee.objects.filter(
        created_time__year=year,
        created_time__month=month
    ).order_by('name')

    if chejian:
        employees = employees.filter(chejian=int(chejian))
    if banzu:
        employees = employees.filter(banzu=int(banzu))

    # 生成当月所有日期
    days_list = []
    for day in range(1, 32):
        try:
            days_list.append(timezone.make_aware(datetime.datetime(year, month, day)))
        except ValueError:
            break

    # 准备数据
    month_log = []
    for employee in employees:
        daily_scores = []
        total_score = 0

        # 获取当月所有分数
        scores = DailyScore.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )
        for day in days_list:
            score = scores.filter(date=day).first()
            if score:
                # 根据分数类型获取相应的分数
                if score_type == 'work':
                    daily_scores.append(score.work_score)
                    total_score += score.work_score
                elif score_type == 'study':
                    daily_scores.append(score.study_score)
                    total_score += score.study_score
                elif score_type == 'business':
                    daily_scores.append(score.business_score)
                    total_score += score.business_score
                elif score_type == 'holiday':
                    daily_scores.append(score.holiday_score)
                    total_score += score.holiday_score
            else:
                daily_scores.append(0)

        month_log.append({
            'name': employee.name,
            'gongzhong': employee.gongzhong,
            'gonghao': employee.gonghao,
            'daily_scores': daily_scores,
            'total_score': round(total_score, 2)
        })

    # 定义分数类型选项
    score_types = {
        'work': '工作积分',
        'study': '学习积分',
        'business': '出差积分',
        'holiday': '休假积分'
    }

    # 计算各种类型的总分
    total_work = 0
    total_study = 0
    total_business = 0
    total_holiday = 0

    for employee in employees:
        scores = DailyScore.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )
        for score in scores:
            total_work += score.work_score
            total_study += score.study_score
            total_business += score.business_score
            total_holiday += score.holiday_score

    # 格式化总分为小数点后两位
    total_work = round(total_work, 2)
    total_study = round(total_study, 2)
    total_business = round(total_business, 2)
    total_holiday = round(total_holiday, 2)

    return render(request, 'gfcx_score.html', {
        'year': year,
        'month': month,
        'days_list': days_list,
        'month_log': month_log,
        'chejian': chejian,
        'banzu': banzu,
        'role': role,
        'admin': ADMIN,
        'xiuche': XIUCHE,
        'xiupei': XIUPEI,
        'score_type': score_type,
        'score_types': score_types,
        'total_work': total_work,
        'total_study': total_study,
        'total_business': total_business,
        'total_holiday': total_holiday
    })


def gfcx_accounting(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/gfcx/gfcx_login/')  # 重定向到登录页面
    role = request.session['info']['role']
    user_banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']

    # 创建选择字典
    chejian_choices_dict = dict(Accounting.chejian_choices)
    banzu_choices_dict = dict(Accounting.banzu_choices)

    # 获取筛选参数
    selected_banzu = request.GET.get('banzu', '')
    selected_year = request.GET.get('year', '')
    selected_month = request.GET.get('month', '')

    # 根据用户角色获取相应的班组数据
    if user_banzu == 13:  # 管理员
        if chejian == 0:  # 总管理员
            allowed_banzu_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16]
        elif chejian == 1:
            allowed_banzu_list = [2, 3, 6, 7, 12]
        elif chejian == 2:
            allowed_banzu_list = [1, 4, 5, 8, 9, 10]
        else:
            allowed_banzu_list = []  # 如果车间号不匹配，返回空列表
    else:
        allowed_banzu_list = [user_banzu]  # 普通用户只能看到自己的班组

    # 获取所有班组列表（只显示允许的班组）
    banzu_choices = [(key, value) for key, value in Accounting.banzu_choices if key in allowed_banzu_list]

    # 获取所有年份数据
    all_dates = Accounting.objects.values('year', 'month').distinct().order_by('-year', '-month')

    # 获取所有唯一年份
    all_years = sorted(set(d['year'] for d in all_dates), reverse=True)

    # 根据筛选条件查询数据
    queryset = Accounting.objects.all()

    # 根据权限过滤数据
    if user_banzu == 13:
        if chejian == 0:  # 总管理员，不需要过滤
            pass
        elif chejian == 1:
            queryset = queryset.filter(banzu__in=[2, 3, 6, 7, 12])
        elif chejian == 2:
            queryset = queryset.filter(banzu__in=[1, 4, 5, 8, 9, 10])
    else:
        queryset = queryset.filter(
            chejian=chejian,
            banzu=user_banzu
        )

    # 添加额外的筛选条件
    if selected_banzu:
        queryset = queryset.filter(banzu=int(selected_banzu))
    if selected_year:
        queryset = queryset.filter(year=int(selected_year))
    if selected_month:
        queryset = queryset.filter(month=int(selected_month))

    # 分组统计
    stats = queryset.values('year', 'month', 'chejian', 'banzu').annotate(
        total_people=Count('id', distinct=True),
        participate_people=Count('id', filter=Q(main_area_days__gt=0)),
        not_participate_people=Count('id', filter=Q(main_area_days=0))
    ).order_by('-year', '-month', 'chejian', 'banzu')

    # 分页
    paginator = Paginator(stats, 20)
    page_number = request.GET.get('page', 1)
    # 确保page_number是有效的整数
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1
    page_obj = paginator.get_page(page_number)

    return render(request, 'gfcx_accounting.html', {
        'page_obj': page_obj,
        'all_dates': all_dates,
        'all_years': all_years,  # 添加年份列表
        'banzu_choices': banzu_choices,
        'selected_banzu': selected_banzu,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'chejian': chejian,
        'banzu': user_banzu,
        'role': role,
        'admin': ADMIN,
        'xiuche': XIUCHE,
        'xiupei': XIUPEI,
        'chejian_choices_dict': chejian_choices_dict,
        'banzu_choices_dict': banzu_choices_dict,
        'is_admin': user_banzu == 13
    })


def gfcx_accounting_results(request):
    if not check_if_user_is_logged_in(request):
        return redirect('/gfcx/gfcx_login/')  # 重定向到登录页面
    role = request.session['info']['role']
    banzu = request.session['info']['banzu']
    chejian = request.session['info']['chejian']
    # 获取筛选参数
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)
    selected_banzu = request.GET.get('banzu', '')  # 添加班组筛选参数

    # 获取车间和班组的显示名称
    chejian_name = dict(Accounting.chejian_choices).get(chejian, '')

    # 根据登录用户获取班组名称
    if banzu == 13:  # 管理员
        # 获取第一个符合条件的班组名称
        first_accounting = Accounting.objects.filter(
            year=year,
            month=month,
            banzu__in=[2, 3, 6, 7, 12] if chejian == 1 else [1, 4, 5, 8, 9, 10]
        ).first()
        banzu_name = first_accounting.get_banzu_display() if first_accounting else ''
    else:  # 普通用户
        banzu_name = dict(Accounting.banzu_choices).get(banzu, '')

    # 构建查询集
    accountings = Accounting.objects.filter(year=year, month=month)

    # 根据权限和筛选条件过滤数据
    if banzu != 13:
        accountings = accountings.filter(
            chejian=chejian,
            banzu=banzu
        )
    else:
        if chejian == 1:
            accountings = accountings.filter(banzu__in=[2, 3, 6, 7, 12])
        elif chejian == 2:
            accountings = accountings.filter(banzu__in=[1, 4, 5, 8, 9, 10])

    # 如果有班组筛选参数，则进一步过滤
    if selected_banzu:
        accountings = accountings.filter(banzu=selected_banzu)

    accountings = accountings.order_by('name')

    # 计算统计信息
    total_people = accountings.count()
    participate_people = accountings.filter(main_area_days__gt=0).count()
    not_participate_people = total_people - participate_people
    total_amount = accountings.aggregate(
        main_area=Sum('main_area_amount'),
        other_area=Sum('other_area_amount')
    )
    total_amount = (total_amount['main_area'] or 0) + (total_amount['other_area'] or 0)

    # 计算总和
    totals = {
        'main_area_score': accountings.aggregate(Sum('main_area_score'))['main_area_score__sum'] or 0,
        'main_area_amount': accountings.aggregate(Sum('main_area_amount'))['main_area_amount__sum'] or 0,
        'other_area_score': accountings.aggregate(Sum('other_area_score'))['other_area_score__sum'] or 0,
        'other_area_amount': accountings.aggregate(Sum('other_area_amount'))['other_area_amount__sum'] or 0,
    }

    return render(request, 'gfcx_accounting_results.html', {
        'accountings': accountings,
        'role': role,
        'admin': ADMIN,
        'xiuche': XIUCHE,
        'xiupei': XIUPEI,
        'year': year,
        'month': month,
        'totals': totals,
        'chejian_name': chejian_name,
        'banzu_name': banzu_name,
        'total_people': total_people,
        'participate_people': participate_people,
        'not_participate_people': not_participate_people,
        'total_amount': total_amount,
        'selected_banzu': selected_banzu  # 传递筛选的班组ID
    })

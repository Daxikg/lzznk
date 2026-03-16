# E:\repair_shop_tool_system\tools\views.py
from django.contrib.auth import authenticate
from rest_framework import viewsets, permissions
from datetime import datetime

from rest_framework.utils import json

from app01.models import Admin
from app01.views import LoginForm, logger
from django.contrib.auth import authenticate, login as auth_login
from .serializers import TeamSerializer, ToolCategorySerializer
from .permissions import IsAdminOrReadOnly
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from app01.models import Admin
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Team, ToolCategory, Tool, ToolLoanRecord, \
    SimpleTeamPermission, RepairRecord, MaintenanceRecord
from .forms import CreateUserForm, UpdateUserForm, TeamForm, ToolCategoryForm, CreateToolForm, UpdateToolForm, LoanRequestForm, ReturnToolForm, \
    MaintenanceRecordForm, RepairRecordForm


def login_tools(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "login_tools.html", {"form": form})
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
                logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了工具管理。')

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
                return redirect("/tools/dashboard/")
            except Admin.DoesNotExist:
                form.add_error("password", "用户信息不存在！")
                return render(request, "login_tools.html", {"form": form})
        else:
            form.add_error("password", "账号或密码错误！")
            return render(request, "login_tools.html", {"form": form})
    return render(request, "login_tools.html", {"form": form})


def tools_register(request):
    from app01.auth_system import unified_logout
    return unified_logout(request, redirect_url='/tools/login_tools/')


def index(request):
    """大屏主页"""
    return render(request, 'dashboard/index.html')


def real_time_data(request):
    """WebSocket或AJAX获取实时数据的API端点"""
    borrowed_count = ToolLoanRecord.objects.filter(status='已发放').count()
    overdue_count = ToolLoanRecord.objects.filter(status='逾期').count()

    # 构建返回的数据结构
    data = {
        'borrowed_count': borrowed_count,
        'overdue_count': overdue_count,
        'timestamp': 'Just now'  # 实际应用中应包含准确时间戳
    }
    return JsonResponse(data)


def check_tool_operation_permission(user):
    """
    检查用户是否具有工具操作权限（创建、编辑、删除）
    这个权限专门用于控制工具管理的具体操作
    """
    return check_tools_permission(user, required_permission='manage_tools')


def check_tools_permission(user, required_permission=None, admin_roles=None):
    """
    检查用户在tools应用中的权限
    优先检查班组权限配置，然后才是用户个人配置
    特殊处理：admin用户总是拥有最高权限
    """
    try:
        # 获取对应的Admin用户对象
        from app01.models import Admin
        admin_user = Admin.objects.get(username=user.username)
        
        # 特殊处理：admin用户总是拥有最高权限
        if admin_user.username == 'admin':
            return True
        
        # 优先检查班组权限配置(SimpleTeamPermission)
        try:
            from .models import SimpleTeamPermission
            team_perm = SimpleTeamPermission.objects.get(
                workshop=admin_user.chejian,
                team=admin_user.banzu
            )
            
            # 根据请求的权限类型进行检查
            if required_permission:
                permission_mapping = {
                    'manage_tools': team_perm.can_manage_tools,
                    'manage_categories': team_perm.can_manage_categories,
                    'perform_maintenance': team_perm.can_perform_maintenance,
                    'manage_permissions': admin_user.username == 'admin',  # 只有admin用户能访问权限管理页面
                    'approve_loans': team_perm.can_approve_loans,
                    'approve_returns': team_perm.can_approve_returns,
                    'manage_repairs': team_perm.can_manage_repairs,
                    'view_reports': team_perm.can_view_records,
                    'manage_users': False,  # SimpleTeamPermission不包含此权限
                    'manage_teams': False,  # SimpleTeamPermission不包含此权限
                }
                return permission_mapping.get(required_permission, False)
            
            # 如果指定了管理员角色
            if admin_roles:
                # 班组有任意权限配置就认为是管理员角色
                return (team_perm.can_manage_tools or 
                       team_perm.can_manage_categories or 
                       team_perm.can_perform_maintenance)
            
            # 默认情况下，有班组权限配置就算通过
            return True
            
        except SimpleTeamPermission.DoesNotExist:
            # 没有班组权限配置，返回False
            return False
            
    except (AttributeError, Admin.DoesNotExist):
        return False


# --- 视图函数 ---

@login_required(login_url='/tools/login_tools/')
def user_dashboard(request):
    """Tools应用用户仪表板
    
    权限策略：
    - 所有登录用户都可以访问此页面
    - 权限仅控制页面上按钮和导航栏的显示/隐藏
    - 无权限用户可以看到基本统计信息，但无法操作受限功能
    """
    user = request.user
    
    # 获取对应的Admin用户对象
    admin_user = None
    try:
        from app01.models import Admin
        admin_user = Admin.objects.get(username=user.username)
    except Admin.DoesNotExist:
        # 如果Admin用户不存在，创建一个默认的
        from app01.models import Admin
        admin_user = Admin.objects.create(
            username=user.username,
            role='role12',  # 默认信息班角色
            chejian=1,      # 默认修配车间
            banzu=12        # 默认信息班
        )

    # 获取班组权限配置
    team_permissions = {}
    try:
        team_perm = SimpleTeamPermission.objects.get(
            workshop=admin_user.chejian,
            team=admin_user.banzu
        )

        # 构建班组权限字典
        team_permissions = {
            'can_manage_tools': team_perm.can_manage_tools,
            'can_manage_categories': team_perm.can_manage_categories,
            'can_approve_loans': team_perm.can_approve_loans,
            'can_approve_returns': team_perm.can_approve_returns,
            'can_perform_maintenance': team_perm.can_perform_maintenance,
            'can_manage_repairs': team_perm.can_manage_repairs,
            'can_view_records': team_perm.can_view_records,
            'can_manage_permissions': admin_user.username == 'admin',
        }

    except SimpleTeamPermission.DoesNotExist:
        # 没有班组权限配置，使用默认权限
        team_permissions = {
            'can_manage_tools': False,
            'can_manage_categories': False,
            'can_approve_loans': False,
            'can_approve_returns': False,
            'can_perform_maintenance': False,
            'can_manage_repairs': False,
            'can_view_records': False,
            'can_manage_permissions': False,
        }

    # 准备上下文数据
    context = {
        'can_manage_tools': team_permissions['can_manage_tools'],
        'can_manage_categories': team_permissions['can_manage_categories'],
        'can_approve_loans': team_permissions['can_approve_loans'],
        'can_approve_returns': team_permissions['can_approve_returns'],
        'can_perform_maintenance': team_permissions['can_perform_maintenance'],
        'can_manage_repairs': team_permissions['can_manage_repairs'],
        'can_view_records': team_permissions['can_view_records'],
        'can_manage_permissions': team_permissions['can_manage_permissions'],
        'is_admin': (team_permissions['can_manage_tools'] or
                   team_permissions['can_manage_categories'] or
                   team_permissions['can_perform_maintenance']),
    }
    
    # 获取一些通用数据
    # 获取当前用户的班组名称
    banzu_dict = dict(Admin.banzu_choices)
    user_team_name = banzu_dict.get(admin_user.banzu, '')

    # 本班组申领记录
    context['my_loaned_tools'] = ToolLoanRecord.objects.filter(
        borrowing_team=user_team_name, status='已发放')
    context['overdue_loans'] = ToolLoanRecord.objects.filter(
        borrowing_team=user_team_name, status='逾期')
    # 本班组申请记录（包括已申请、已发放、归还申请、逾期状态）
    context['my_applications'] = ToolLoanRecord.objects.filter(
        borrowing_team=user_team_name).exclude(status='已归还').order_by('-loan_time')
    
    # 如果用户有审批权限，显示待审批申请
    if team_permissions.get('can_approve_loans'):
        # 获取申领申请和归还申请
        pending_borrow_approvals = ToolLoanRecord.objects.filter(status='已申请')
        pending_return_approvals = ToolLoanRecord.objects.filter(status='归还申请')

        # 合并两个查询集
        from itertools import chain
        context['pending_approvals_list'] = list(chain(pending_borrow_approvals, pending_return_approvals))
        # 按时间排序
        context['pending_approvals_list'].sort(key=lambda x: x.loan_time)
    
    # 统计数据 - 按照新的分类逻辑
    # 1. 工具总数（除报废的所有的工具）
    context['total_tools'] = Tool.objects.exclude(status='报废').count()
    
    # 2. 可用工具 = 正常工具 - (已领用工具 + 归还审批中工具)
    borrowed_tool_ids = ToolLoanRecord.objects.filter(
        status__in=['已发放', '归还申请']  # 包括已领用和归还审批中的工具
    ).values_list('tool_id', flat=True)
    context['available_tools'] = Tool.objects.filter(status='正常').exclude(id__in=borrowed_tool_ids).count()
    
    # 3. 在借工具 = 处于已领用、归还待批准状态的工具个数
    context['borrowed_tools'] = ToolLoanRecord.objects.filter(
        status__in=['已发放', '归还申请']
    ).count()
    
    # 4. 逾期工具 = 已发放且超过预计归还时间的工具
    context['overdue_tools'] = ToolLoanRecord.objects.filter(
        status='已发放',
        expected_return_time__lt=timezone.now()
    ).count()
    
    # 5. 故障工具 = 处于故障和维修状态的工具
    context['faulty_tools'] = Tool.objects.filter(status__in=['故障', '维修']).count()
    
    # 6. 报废工具 = 处于报废状态的工具
    context['scrap_tools'] = Tool.objects.filter(status='报废').count()

    # 图表数据 - 圆环图（工具状态分布）
    context['chart_faulty'] = context['faulty_tools']  # 故障
    context['chart_borrowed'] = context['borrowed_tools']  # 已借出
    context['chart_scrap'] = context['scrap_tools']  # 报废
    context['chart_available'] = context['available_tools']  # 可用

    # 图表数据 - 柱状图（各班组在借工具数量）
    team_borrowed_stats = ToolLoanRecord.objects.filter(
        status__in=['已发放', '归还申请']
    ).values('borrowing_team').annotate(count=Count('id')).order_by('-count')

    # 转换为图表需要的格式
    team_labels = []
    team_data = []
    for stat in team_borrowed_stats[:10]:  # 最多显示10个班组
        team_labels.append(stat['borrowing_team'])
        team_data.append(stat['count'])

    context['chart_team_labels'] = team_labels
    context['chart_team_data'] = team_data

    # 7. 本班组借用的工具 = 查询本班组正在借用的所有工具
    # 获取用户班组名称
    if admin_user:
        banzu_dict = dict(Admin.banzu_choices)
        team_name = banzu_dict.get(admin_user.banzu, '')
        if team_name:
            # 查询本班组借用的工具（已发放或归还申请中）
            team_borrowed_records = ToolLoanRecord.objects.filter(
                borrowing_team=team_name,
                status__in=['已发放', '归还申请']
            ).select_related('tool').order_by('-loan_time')

            # 为每条记录添加状态显示
            for record in team_borrowed_records:
                if record.status == '已发放':
                    record.display_status = '已领用'
                    # 检查是否逾期（使用 record_is_overdue 避免与模型的 @property 冲突）
                    if record.expected_return_time and timezone.now() > record.expected_return_time:
                        record.display_status = '逾期'
                        record.record_is_overdue = True
                    else:
                        record.record_is_overdue = False
                elif record.status == '归还申请':
                    record.display_status = '归还审批中'
                    record.record_is_overdue = False

            context['team_name'] = team_name
            context['team_borrowed_records'] = team_borrowed_records
            context['team_borrowed_count'] = team_borrowed_records.count()

    return render(request, 'tools/user_dashboard.html', context)


@login_required
def get_team_permission_api(request, workshop, team):
    """获取指定班组的权限配置API - 适配SimpleTeamPermission模型"""
    print(f"API called with workshop={workshop}, team={team}")
    
    # 检查用户权限
    if not check_tools_permission(request.user, required_permission='manage_permissions'):
        print("Permission denied for user:", request.user.username)
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    try:
        # 优先尝试获取SimpleTeamPermission配置
        try:
            team_perm = SimpleTeamPermission.objects.get(workshop=workshop, team=team)
            print(f"Found simple team permission config: {team_perm}")
            
            data = {
                'success': True,
                'permission': {
                    'workshop': team_perm.workshop,
                    'team': team_perm.team,
                    'team_leader_username': team_perm.team_leader_username or '',
                    'can_manage_tools': team_perm.can_manage_tools,
                    'can_manage_categories': team_perm.can_manage_categories,
                    'can_approve_loans': team_perm.can_approve_loans,
                    'can_approve_returns': team_perm.can_approve_returns,
                    'can_perform_maintenance': team_perm.can_perform_maintenance,
                    'can_manage_repairs': team_perm.can_manage_repairs,
                    'can_view_records': team_perm.can_view_records,
                }
            }
        except SimpleTeamPermission.DoesNotExist:
            # 没有配置，返回默认值
            print(f"No permission config found for workshop={workshop}, team={team}")
            data = {
                'success': False,
                'message': '未找到该班组的权限配置',
                'permission': {
                    'workshop': workshop,
                    'team': team,
                    'team_leader_username': '',
                    'can_manage_tools': False,
                    'can_manage_categories': False,
                    'can_approve_loans': False,
                    'can_approve_returns': False,
                    'can_perform_maintenance': False,
                    'can_manage_repairs': False,
                    'can_view_records': False,
                }
            }
        
        print("Returning successful response")
        return JsonResponse(data)
    except Exception as e:
        print(f"Unexpected error in API: {str(e)}")
        return JsonResponse({'success': False, 'message': f'服务器错误: {str(e)}'})

@login_required
def manage_user_permissions(request):
    """个人用户权限管理 - 重定向到简化权限管理"""
    # 个人权限管理已合并到简化权限管理中
    return redirect('tools:simple_permissions')

@login_required
def simple_permissions(request):
    """简化权限管理 - 只包含三大核心权限"""
    if not check_tools_permission(request.user, required_permission='manage_permissions'):
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')

    # 处理班组权限配置的POST请求
    if request.method == 'POST' and 'simple_permissions_form' in request.POST:
        try:
            workshop = int(request.POST.get('workshop'))
            team = int(request.POST.get('team'))
            
            # 获取或创建该班组的权限配置
            team_perm, created = SimpleTeamPermission.objects.get_or_create(
                workshop=workshop,
                team=team,
                defaults={
                    'team_leader_username': request.POST.get('team_leader', ''),
                    'can_manage_tools': request.POST.get('can_manage_tools') == 'on',
                    'can_manage_categories': request.POST.get('can_manage_categories') == 'on',
                    'can_approve_loans': request.POST.get('can_approve_loans') == 'on',
                    'can_approve_returns': request.POST.get('can_approve_returns') == 'on',
                    'can_perform_maintenance': request.POST.get('can_perform_maintenance') == 'on',
                    'can_manage_repairs': request.POST.get('can_manage_repairs') == 'on',
                    'can_view_records': request.POST.get('can_view_records') == 'on'
                }
            )
            
            # 更新权限配置
            if not created:
                team_perm.team_leader_username = request.POST.get('team_leader', '')
                team_perm.can_manage_tools = request.POST.get('can_manage_tools') == 'on'
                team_perm.can_manage_categories = request.POST.get('can_manage_categories') == 'on'
                team_perm.can_approve_loans = request.POST.get('can_approve_loans') == 'on'
                team_perm.can_approve_returns = request.POST.get('can_approve_returns') == 'on'
                team_perm.can_perform_maintenance = request.POST.get('can_perform_maintenance') == 'on'
                team_perm.can_manage_repairs = request.POST.get('can_manage_repairs') == 'on'
                team_perm.can_view_records = request.POST.get('can_view_records') == 'on'
                team_perm.save()
            
            action = "创建" if created else "更新"
            messages.success(request, f"班组权限{action}成功")
            
        except Exception as e:
            messages.error(request, f"权限配置失败: {str(e)}")
        
        # 重定向回权限管理页面
        return redirect('tools:simple_permissions')

    # 获取所有唯一的车间-班组组合
    workshop_team_combinations = Admin.objects.values('chejian', 'banzu').distinct()
    
    # 准备班组数据显示
    teams_data = []
    workshop_dict = dict(Admin.chejian_choices)
    team_dict = dict(Admin.banzu_choices)
    
    for combo in workshop_team_combinations:
        workshop_name = workshop_dict.get(combo['chejian'], f"车间{combo['chejian']}")
        team_name = team_dict.get(combo['banzu'], f"班组{combo['banzu']}")
        
        # 获取该班组的成员数
        member_count = Admin.objects.filter(
            chejian=combo['chejian'], 
            banzu=combo['banzu']
        ).count()
        
        # 获取该班组的权限配置
        try:
            team_perm = SimpleTeamPermission.objects.get(
                workshop=combo['chejian'],
                team=combo['banzu']
            )
            has_permission_config = True
        except SimpleTeamPermission.DoesNotExist:
            team_perm = None
            has_permission_config = False
        
        teams_data.append({
            'workshop_id': combo['chejian'],
            'team_id': combo['banzu'],
            'workshop_name': workshop_name,
            'team_name': team_name,
            'full_name': f"{workshop_name} - {team_name}",
            'member_count': member_count,
            'permission_config': team_perm,
            'has_permission_config': has_permission_config
        })
    
    context = {
        'teams_data': teams_data,
        'workshop_choices': workshop_dict,
        'team_choices': team_dict
    }
    
    return render(request, 'tools/simple_permissions.html', context)



@login_required
def get_position_permission_api(request, position):
    """获取指定职务的权限配置API"""
    print(f"API called for position: {position}")
    
    # 检查用户权限
    if not check_tools_permission(request.user, required_permission='manage_permissions'):
        print("Permission denied for user:", request.user.username)
        return JsonResponse({'success': False, 'message': '权限不足'})
    
    # 职务映射
    position_mapping = {
        'workshop_director': '车间主任',
        'info_admin': '信息管理员', 
        'foreman': '班组长',
        'operator': '操作员'
    }
    
    if position not in position_mapping:
        return JsonResponse({'success': False, 'message': '无效的职务参数'})
    
    try:
        # 获取当前权限设置
        current_permissions = request.session.get(f'position_permissions_{position}', {
            'can_borrow': True,
            'can_manage': position in ['workshop_director', 'info_admin'],
            'can_maintain': position in ['workshop_director', 'info_admin', 'foreman'],
            'can_approve': position in ['workshop_director', 'info_admin', 'foreman'],
            'can_admin': position in ['workshop_director', 'info_admin']
        })
        
        data = {
            'success': True,
            'permission': current_permissions
        }
        print("Returning successful response")
        return JsonResponse(data)
    except Exception as e:
        print(f"Unexpected error in API: {str(e)}")
        return JsonResponse({'success': False, 'message': f'服务器错误: {str(e)}'})

@login_required
def edit_position_permissions(request, position):
    """编辑特定职务的权限设置 - 支持AJAX和传统请求"""
    if not check_tools_permission(request.user, required_permission='manage_permissions'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '权限不足'})
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')
    
    # 职务映射
    position_mapping = {
        'workshop_director': '车间主任',
        'info_admin': '信息管理员', 
        'foreman': '班组长',
        'operator': '操作员'
    }
    
    if position not in position_mapping:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '无效的职务参数'})
        messages.error(request, "无效的职务参数。")
        return redirect('tools:simple_permissions')
    
    position_display = position_mapping[position]
    
    if request.method == 'POST':
        # 处理权限更新
        can_borrow = request.POST.get('can_borrow') == 'on'
        can_manage = request.POST.get('can_manage') == 'on'
        can_maintain = request.POST.get('can_maintain') == 'on'
        can_approve = request.POST.get('can_approve') == 'on'
        can_admin = request.POST.get('can_admin') == 'on'
        
        # 这里可以保存到数据库或配置文件
        # 目前我们用session临时存储演示
        request.session[f'position_permissions_{position}'] = {
            'can_borrow': can_borrow,
            'can_manage': can_manage, 
            'can_maintain': can_maintain,
            'can_approve': can_approve,
            'can_admin': can_admin
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': f'{position_display} 的权限设置已更新！',
                'permission': request.session[f'position_permissions_{position}']
            })
        else:
            messages.success(request, f"{position_display} 的权限设置已更新！")
            return redirect('tools:simple_permissions')
    else:
        # GET请求 - 返回JSON数据给AJAX调用
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # 获取当前权限设置
            current_permissions = request.session.get(f'position_permissions_{position}', {
                'can_borrow': True,
                'can_manage': position in ['workshop_director', 'info_admin'],
                'can_maintain': position in ['workshop_director', 'info_admin', 'foreman'],
                'can_approve': position in ['workshop_director', 'info_admin', 'foreman'],
                'can_admin': position in ['workshop_director', 'info_admin']
            })
            
            return JsonResponse({
                'success': True,
                'permission': current_permissions
            })
        else:
            # 传统的页面渲染（为了向后兼容）
            current_permissions = request.session.get(f'position_permissions_{position}', {
                'can_borrow': True,
                'can_manage': position in ['workshop_director', 'info_admin'],
                'can_maintain': position in ['workshop_director', 'info_admin', 'foreman'],
                'can_approve': position in ['workshop_director', 'info_admin', 'foreman'],
                'can_admin': position in ['workshop_director', 'info_admin']
            })
            
            context = {
                'position': position,
                'position_display': position_display,
                'permissions': current_permissions
            }
            
            return render(request, 'tools/edit_position_permissions.html', context)

@login_required
def create_tool_category(request):
    """创建工具类别 - 仅信息班管理员或车间主任可访问"""
    if not check_tools_permission(request.user, required_permission='manage_categories'):
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')

    if request.method == 'POST':
        form = ToolCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"工具类别 '{category.name}' 创建成功！")
            return redirect('tools:manage_tool_categories')
    else:
        form = ToolCategoryForm()
    return render(request, 'tools/create_tool_category.html', {'form': form})

@login_required
def update_tool_category(request, category_id):
    """更新工具类别 - 支持AJAX和传统请求"""
    if not check_tools_permission(request.user, required_permission='manage_categories'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '权限不足'})
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')

    category = get_object_or_404(ToolCategory, id=category_id)
    if request.method == 'POST':
        form = ToolCategoryForm(request.POST, instance=category)
        if form.is_valid():
            updated_category = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': f"工具类别 '{updated_category.name}' 更新成功！",
                    'category': {
                        'id': updated_category.id,
                        'name': updated_category.name
                    }
                })
            else:
                messages.success(request, f"工具类别 '{updated_category.name}' 更新成功！")
                return redirect('tools:manage_tool_categories')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': '表单验证失败',
                    'errors': form.errors
                })
            # 传统请求继续使用模板渲染
    else:
        form = ToolCategoryForm(instance=category)
    
    # 对于GET请求或表单验证失败的情况，返回模板
    return render(request, 'tools/update_tool_category.html', {'form': form, 'category': category})

@login_required
def manage_tool_categories(request):
    """管理工具类别列表 - 仅信息班管理员或车间主任可访问"""
    if not check_tools_permission(request.user, required_permission='manage_categories'):
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')

    categories = ToolCategory.objects.all()
    return render(request, 'tools/manage_tool_categories.html', {'categories': categories})

@login_required
def create_tool(request):
    """创建工具 - 仅具备工具操作权限的用户可访问"""
    if not check_tool_operation_permission(request.user):
        messages.error(request, "权限不足：您没有创建工具的权限。")
        return redirect('tools:manage_tools')

    if request.method == 'POST':
        form = CreateToolForm(request.POST, request.FILES)
        if form.is_valid():
            tool = form.save()
            messages.success(request, f"工具 '{tool.name}' 创建成功！")
            return redirect('tools:manage_tools') # 修改这里，加上命名空间
    else:
        form = CreateToolForm()
    return render(request, 'tools/create_tool.html', {'form': form})

@login_required
def update_tool(request, tool_id):
    """更新工具信息 - 仅具备工具操作权限的用户可访问"""
    if not check_tool_operation_permission(request.user):
        messages.error(request, "权限不足：您没有编辑工具的权限。")
        return redirect('tools:manage_tools')

    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        form = UpdateToolForm(request.POST, request.FILES, instance=tool)
        if form.is_valid():
            # 由于状态字段被禁用，需要手动保留原始状态
            tool_form = form.save(commit=False)
            tool_form.status = tool.status  # 保持原有状态不变
            tool_form.save()
            messages.success(request, f"工具 '{tool.name}' 信息更新成功！")
            return redirect('tools:manage_tools') # 修改这里，加上命名空间
    else:
        form = UpdateToolForm(instance=tool)
    return render(request, 'tools/update_tool.html', {'form': form, 'tool': tool})


@login_required
def manage_tools(request):
    """管理工具列表 - 所有用户都可查看 但只有具备工具管理权限的用户才能进行创建 编辑 删除操作"""
    # 移除了整体的权限检查，允许所有用户查看工具列表

    # 获取当前用户的班组信息
    user = request.user
    try:
        admin_user = Admin.objects.get(username=user.username)
        banzu_dict = dict(Admin.banzu_choices)
        user_team_name = banzu_dict.get(admin_user.banzu, '')
    except Admin.DoesNotExist:
        user_team_name = ''

    # 检查用户是否有管理权限（管理员可以看到所有工具）
    has_manage_permission = check_tools_permission(user, required_permission='manage_tools')

    # 获取已领用的工具ID列表（已发放状态）
    borrowed_tool_ids = ToolLoanRecord.objects.filter(status='已发放').values_list('tool_id', flat=True)

    # 获取归还审批中的工具ID列表
    return_approval_tool_ids = ToolLoanRecord.objects.filter(status='归还申请').values_list('tool_id', flat=True)

    # 获取借出待批准的工具ID列表
    loan_pending_tool_ids = ToolLoanRecord.objects.filter(status='已申请').values_list('tool_id', flat=True)

    # 获取所有工具（除报废外）
    all_tools = Tool.objects.exclude(status='报废')

    # 获取可用工具（正常状态且未被借出且不在归还审批中）
    available_tools = Tool.objects.filter(status='正常').exclude(
        id__in=list(borrowed_tool_ids) + list(return_approval_tool_ids)
    )

    # 获取已领用工具
    # 如果用户没有管理权限，只显示本班组领用的工具
    if has_manage_permission:
        borrowed_records = ToolLoanRecord.objects.filter(
            status__in=['已发放', '归还申请']
        ).select_related('tool', 'borrower')
    else:
        # 普通用户只能看到本班组领用的工具
        borrowed_records = ToolLoanRecord.objects.filter(
            status__in=['已发放', '归还申请'],
            borrowing_team=user_team_name
        ).select_related('tool', 'borrower')

    # 获取故障工具（故障和维修状态）
    faulty_tools = Tool.objects.filter(status__in=['故障', '维修'])

    # 获取报废工具
    scrapped_tools = Tool.objects.filter(status='报废')
    
    # 为工具添加状态信息
    def add_tool_status_info(tools):
        for tool in tools:
            # 检查是否有正在进行的申领相关记录
            loan_application = ToolLoanRecord.objects.filter(
                tool=tool,
                status__in=['已申请', '归还申请', '已发放']
            ).first()

            if loan_application:
                if loan_application.status == '已申请':
                    tool.current_status = '申领审批中'
                    tool.is_available_for_loan = False
                    tool.is_overdue = False
                elif loan_application.status == '归还申请':
                    tool.current_status = '归还审批中'
                    tool.is_available_for_loan = False
                    tool.is_overdue = False
                elif loan_application.status == '已发放':
                    # 检查是否逾期
                    if loan_application.is_overdue:
                        tool.current_status = '逾期'
                        tool.is_overdue = True
                    else:
                        tool.current_status = '已领用'
                        tool.is_overdue = False
                    tool.is_available_for_loan = False
            else:
                tool.current_status = tool.status
                tool.is_available_for_loan = (tool.status == '正常')
                tool.is_overdue = False
        return tools
    
    # 为各类工具添加状态信息
    all_tools = add_tool_status_info(all_tools)
    available_tools = add_tool_status_info(available_tools)
    faulty_tools = add_tool_status_info(faulty_tools)
    scrapped_tools = add_tool_status_info(scrapped_tools)
    
    # 为申领记录添加状态信息
    for record in borrowed_records:
        if record.status == '已申请':
            record.display_status = '借出待批准'
            record.can_return = False
        elif record.status == '归还申请':
            record.display_status = '归还待批准'
            record.can_return = False
        elif record.status == '已发放':
            record.display_status = '已领用'
            record.can_return = True
        else:
            record.display_status = record.status
            record.can_return = True
    
    return render(request, 'tools/manage_tools.html', {
        'all_tools': all_tools,
        'all_tools_count': all_tools.count(),
        'available_tools': available_tools,
        'available_tools_count': available_tools.count(),
        'borrowed_records': borrowed_records,
        'borrowed_tools_count': borrowed_records.count(),
        'faulty_tools': faulty_tools,
        'faulty_tools_count': faulty_tools.count(),
        'scrapped_tools': scrapped_tools,
        'scrapped_tools_count': scrapped_tools.count()
    })





@login_required
def tool_loan_history(request, tool_id):
    """查看特定工具的申领历史记录 - 只读显示"""
    # 获取工具信息
    tool = get_object_or_404(Tool, id=tool_id)
    
    # 获取该工具的所有申领记录，按时间倒序排列
    loan_records = ToolLoanRecord.objects.filter(tool=tool).select_related(
        'borrower', 'team_leader_approval'
    ).order_by('-loan_time')
    
    return render(request, 'tools/tool_loan_history.html', {
        'tool': tool,
        'loan_records': loan_records
    })


@login_required
def delete_tool_category(request, category_id):
    """删除工具类别 - 仅信息班管理员或车间主任可访问"""
    if not check_tools_permission(request.user, required_permission='manage_categories'):
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')
    
    category = get_object_or_404(ToolCategory, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        try:
            # 检查是否有工具属于此类别
            tool_count = category.tool_set.count()
            if tool_count > 0:
                messages.error(request, f"无法删除类别 '{category_name}'，因为还有 {tool_count} 个工具属于此类别。请先将这些工具移动到其他类别。")
                return redirect('tools:manage_tool_categories')
            
            # 删除类别
            category.delete()
            messages.success(request, f"工具类别 '{category_name}' 删除成功！")
        except Exception as e:
            messages.error(request, f"删除工具类别失败：{str(e)}")
        return redirect('tools:manage_tool_categories')
    
    # GET请求显示确认页面（实际上会被模态框处理）
    return redirect('tools:manage_tool_categories')


@login_required
def delete_tool(request, tool_id):
    """删除工具 - 仅具备工具操作权限的用户可访问"""
    if not check_tool_operation_permission(request.user):
        messages.error(request, "权限不足：您没有删除工具的权限。")
        return redirect('tools:manage_tools')
    
    tool = get_object_or_404(Tool, id=tool_id)
    
    if request.method == 'POST':
        tool_name = tool.name
        try:
            # 删除工具（相关的外键记录会自动处理）
            tool.delete()
            messages.success(request, f"工具 '{tool_name}' 删除成功！")
        except Exception as e:
            messages.error(request, f"删除工具失败：{str(e)}")
        return redirect('tools:manage_tools')
    
    # GET请求显示确认页面（实际上会被模态框处理）
    return redirect('tools:manage_tools')


@login_required
def scrap_tool(request, tool_id):
    """报废工具 - 仅具备工具操作权限的用户可访问"""
    if not check_tool_operation_permission(request.user):
        messages.error(request, "权限不足：您没有报废工具的权限。")
        return redirect('tools:manage_tools')

    tool = get_object_or_404(Tool, id=tool_id)

    if request.method == 'POST':
        tool_name = tool.name
        scrap_reason = request.POST.get('scrap_reason', '').strip()

        if not scrap_reason:
            messages.error(request, "请填写报废原因！")
            return redirect('tools:update_tool', tool_id=tool_id)

        try:
            tool.status = '报废'
            # 将报废原因追加到备注中
            if tool.remark:
                tool.remark = f"{tool.remark}\n[报废原因]: {scrap_reason}"
            else:
                tool.remark = f"[报废原因]: {scrap_reason}"
            tool.save()
            messages.success(request, f"工具 '{tool_name}' 已标记为报废！")
        except Exception as e:
            messages.error(request, f"报废工具失败：{str(e)}")
        return redirect('tools:manage_tools')

    # GET请求重定向到工具管理页面
    return redirect('tools:manage_tools')


@login_required
def loan_tool(request, tool_id):
    """申请申领工具 - 智能审批流程"""
    tool = get_object_or_404(Tool, id=tool_id)
    if tool.status != '正常':
        messages.error(request, f"工具 '{tool.name}' 当前状态为 '{tool.status}'，无法申领。")
        return redirect('tools:manage_tools')

    # 检查用户是否有审批权限
    has_approval_permission = check_tools_permission(request.user, required_permission='approve_loans')

    if request.method == 'POST':
        form = LoanRequestForm(request.POST, current_user=request.user)
        if form.is_valid():
            loan_record = form.save(commit=False)
            loan_record.tool = tool
            
            # 处理申领时间字段
            loan_datetime = form.cleaned_data.get('loan_datetime')
            if loan_datetime:
                # 如果用户提供了申领时间，使用用户输入的时间
                loan_record.loan_time = loan_datetime
            # 如果没有提供，保持auto_now_add的默认行为
            
            # 关联申领人ID
            borrowing_person_id = request.POST.get('borrowing_person_id')
            if borrowing_person_id:
                loan_record.borrowing_person_id = int(borrowing_person_id)

            # 设置借款人（当前登录用户对应的Admin对象）
            try:
                loan_record.borrower = Admin.objects.get(username=request.user.username)
            except Admin.DoesNotExist:
                messages.error(request, "用户信息不存在")
                return redirect('tools:manage_tools')
            
            # 智能审批逻辑：有审批权限的用户直接申领，无权限的需要审批
            if has_approval_permission:
                # 有审批权限，直接设置为已发放
                loan_record.status = '已发放'
                loan_record.save()
                messages.success(request, f"工具申领成功！")
            else:
                # 无审批权限，需要审批
                loan_record.status = '已申请'
                loan_record.save()
                messages.success(request, f"工具申领申请已提交，等待审批！")
            
            return redirect('tools:user_dashboard')
        else:
            # 表单验证失败，显示错误信息
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # GET请求，初始化表单
        form = LoanRequestForm(current_user=request.user)
    
    return render(request, 'tools/loan_tool.html', {
        'form': form, 
        'tool': tool,
        'has_approval_permission': has_approval_permission
    })


@login_required
def approve_loan(request, loan_id):
    """班组长审批申领申请 - 仅班组长可访问"""
    loan_record = get_object_or_404(ToolLoanRecord, id=loan_id, status='已申请')
    if not check_tools_permission(request.user, required_permission='approve_loans'):
        messages.error(request, "权限不足，无法审批。")
        return redirect('tools:user_dashboard')

    # 检查申请是否属于本班组成员
    # TODO: 实现班组成员检查逻辑 (例如通过Profile模型或Team模型关联)
    # 这里暂时简化，只检查状态
    if loan_record.status == '已申请':
        # 获取当前用户的Admin对象
        try:
            admin_user = Admin.objects.get(username=request.user.username)
        except Admin.DoesNotExist:
            messages.error(request, "用户信息不存在")
            return redirect('tools:user_dashboard')

        loan_record.team_leader_approval = admin_user
        loan_record.status = '已发放'
        loan_record.save()
        messages.success(request, f"已批准 {loan_record.borrower.username} 的工具申领申请。")
    else:
        messages.error(request, "申请状态已更改，无法审批。")

    return redirect('tools:user_dashboard')  # 或跳转到待审批列表


@login_required
def approve_return(request, loan_id):
    """班组长审批归还申请 - 仅班组长可访问"""
    loan_record = get_object_or_404(ToolLoanRecord, id=loan_id, status='归还申请')
    if not check_tools_permission(request.user, required_permission='approve_loans'):
        messages.error(request, "权限不足，无法审批。")
        return redirect('tools:user_dashboard')

    if loan_record.status == '归还申请':
        # 获取当前用户的Admin对象
        try:
            admin_user = Admin.objects.get(username=request.user.username)
        except Admin.DoesNotExist:
            messages.error(request, "用户信息不存在")
            return redirect('tools:user_dashboard')

        loan_record.return_approval = admin_user

        # 完成归还流程
        loan_record.status = '已归还'
        loan_record.tool.status = '正常'  # 归还后工具状态变回正常
        loan_record.tool.save()
        loan_record.save()
        messages.success(request, f"已批准 {loan_record.borrower.username} 的工具归还申请。")
    else:
        messages.error(request, "归还申请状态已更改，无法审批。")

    return redirect('tools:user_dashboard')


@login_required
def ajax_approve_loan(request, loan_id):
    """AJAX审批申领/归还申请接口"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只支持POST请求'})

    if not check_tools_permission(request.user, required_permission='approve_loans'):
        return JsonResponse({'success': False, 'message': '权限不足，无法审批'})

    # 获取当前用户的Admin对象
    try:
        admin_user = Admin.objects.get(username=request.user.username)
    except Admin.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户信息不存在'})

    try:
        loan_type = request.POST.get('loan_type')

        if loan_type == 'borrow':
            # 审批申领申请
            loan_record = get_object_or_404(ToolLoanRecord, id=loan_id, status='已申请')
            loan_record.team_leader_approval = admin_user
            loan_record.status = '已发放'
            loan_record.save()
            return JsonResponse({
                'success': True,
                'message': f'已批准 {loan_record.borrower.username} 的工具申领申请'
            })

        elif loan_type == 'return':
            # 审批归还申请
            loan_record = get_object_or_404(ToolLoanRecord, id=loan_id, status='归还申请')
            loan_record.return_approval = admin_user
            # 完成归还流程
            loan_record.status = '已归还'
            loan_record.tool.status = '正常'  # 归还后工具状态变回正常
            loan_record.tool.save()
            loan_record.save()
            return JsonResponse({
                'success': True,
                'message': f'已批准 {loan_record.borrower.username} 的工具归还申请'
            })

        else:
            return JsonResponse({'success': False, 'message': '无效的申请类型'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'审批失败: {str(e)}'})


@login_required
def return_tool(request, loan_id):
    """申请归还工具 - 智能审批流程"""
    # 获取对应的Admin用户
    try:
        admin_user = Admin.objects.get(username=request.user.username)
    except Admin.DoesNotExist:
        messages.error(request, "用户信息不存在")
        return redirect('tools:user_dashboard')

    # 检查用户是否有管理工具的权限
    has_manage_permission = check_tools_permission(request.user, required_permission='manage_tools')

    if has_manage_permission:
        # 有管理权限的用户可以为任何人申请归还
        loan_record = get_object_or_404(ToolLoanRecord, id=loan_id, status='已发放')
    else:
        # 没有管理权限的用户，只能归还本班组申领的工具
        banzu_dict = dict(Admin.banzu_choices)
        user_team_name = banzu_dict.get(admin_user.banzu, '')
        loan_record = get_object_or_404(
            ToolLoanRecord,
            id=loan_id,
            status='已发放',
            borrowing_team=user_team_name
        )
    
    # 检查用户是否有审批权限
    has_approval_permission = check_tools_permission(request.user, required_permission='approve_loans')
    
    if request.method == 'POST':
        form = ReturnToolForm(request.POST)
        if form.is_valid():
            # 智能审批逻辑：有审批权限的用户直接归还，无权限的需要审批
            if has_approval_permission:
                # 有审批权限，直接完成归还
                loan_record.actual_return_time = form.cleaned_data['actual_return_time']
                loan_record.remarks = form.cleaned_data['remarks']
                loan_record.status = '已归还'
                loan_record.tool.status = '正常'  # 工具状态变回正常
                loan_record.tool.save()
                loan_record.save()
                messages.success(request, f"工具归还成功！")
            else:
                # 无审批权限，需要审批
                loan_record.actual_return_time = form.cleaned_data['actual_return_time']
                loan_record.remarks = form.cleaned_data['remarks']
                loan_record.status = '归还申请'  # 改为归还申请状态
                loan_record.save()
                messages.success(request, f"归还申请已提交，等待审批。")
            
            return redirect('tools:user_dashboard')
    else:
        form = ReturnToolForm(initial={'actual_return_time': timezone.now()})
    return render(request, 'tools/return_tool.html', {
        'form': form, 
        'loan_record': loan_record,
        'has_approval_permission': has_approval_permission
    })


@login_required
def create_maintenance_record(request, tool_id):
    """创建保养记录 - 仅信息班管理员或车间主任可访问"""
    if not check_tools_permission(request.user, required_permission='perform_maintenance'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '权限不足'})
        messages.error(request, "权限不足。")
        return redirect('tools:user_dashboard')

    tool = get_object_or_404(Tool, id=tool_id)

    # 获取对应的Admin用户
    try:
        admin_user = Admin.objects.get(username=request.user.username)
    except Admin.DoesNotExist:
        messages.error(request, "用户信息不存在")
        return redirect('tools:manage_tools')

    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST, request.FILES)
        if form.is_valid():
            maintenance_record = form.save(commit=False)
            maintenance_record.tool = tool
            maintenance_record.maintainer = admin_user
            maintenance_record.save()

            # 更新工具的上次保养日期
            tool.last_maintenance_date = maintenance_record.date
            tool.save()

            # 处理多张图片上传
            images = request.FILES.getlist('images')
            for image_file in images:
                from .models import MaintenanceImage
                MaintenanceImage.objects.create(record=maintenance_record, image=image_file)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f"工具 '{tool.name}' 的保养记录已创建"})
            messages.success(request, f"工具 '{tool.name}' 的保养记录已创建。")
            return redirect('tools:manage_tools')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = MaintenanceRecordForm()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('tools/maintenance_form_modal.html', {'form': form, 'tool': tool, 'tool_id': tool_id, 'today': timezone.now().date()}, request=request)
        return JsonResponse({'success': True, 'html': html})

    return render(request, 'tools/maintenance_form.html', {'form': form, 'tool': tool})


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]


class ToolCategoryViewSet(viewsets.ModelViewSet):
    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]


@login_required
def get_tool_detail_api(request, tool_id):
    """获取工具的详细信息用于模态框展示"""
    try:
        tool = Tool.objects.get(id=tool_id)

        # 获取保养周期显示标签
        maintenance_cycle_label = ''
        for value, label in tool.MAINTENANCE_CYCLE_CHOICES:
            if value == tool.maintenance_cycle:
                maintenance_cycle_label = label
                break

        # 计算 current_status（与 manage_tools 视图逻辑一致）
        loan_application = ToolLoanRecord.objects.filter(
            tool=tool,
            status__in=['已申请', '归还申请', '已发放']
        ).first()

        if loan_application:
            if loan_application.status == '已申请':
                current_status = '申领审批中'
            elif loan_application.status == '归还申请':
                current_status = '归还审批中'
            elif loan_application.status == '已发放':
                current_status = '已领用'
            else:
                current_status = tool.status
        else:
            current_status = tool.status

        # 构造返回数据
        tool_data = {
            'id': tool.id,
            'code': tool.code,
            'name': tool.name,
            'specification': tool.specification,
            'manufacturer': tool.manufacturer or '',
            'category_name': tool.category.name if tool.category else '',
            'purchase_date': tool.purchase_date.strftime('%Y-%m-%d') if tool.purchase_date else '',
            'value': str(tool.value) if tool.value else '0',
            'is_high_value': tool.is_high_value,
            'status': tool.status,
            'current_status': current_status,
            'maintenance_cycle': tool.maintenance_cycle,
            'maintenance_cycle_label': maintenance_cycle_label,
            'last_maintenance_date': tool.last_maintenance_date.strftime('%Y-%m-%d') if tool.last_maintenance_date else '',
            'next_maintenance_date': tool.next_maintenance_date.strftime('%Y-%m-%d') if tool.next_maintenance_date else '',
            'remark': tool.remark or '',
            'image': tool.image.url if tool.image else '',
            'technical_docs': tool.technical_docs.url if tool.technical_docs else '',
            'technical_docs_name': tool.technical_docs.name.split('/')[-1] if tool.technical_docs else '',
        }

        return JsonResponse({
            'success': True,
            'tool': tool_data
        })

    except Tool.DoesNotExist:
        return JsonResponse({'success': False, 'message': '未找到该工具'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'服务器错误: {str(e)}'})


@login_required
def get_team_users_api(request, team_id):
    """根据班组ID获取该班组的所有人员信息"""
    try:
        # 导入bzrz应用的TeamUser模型
        from bzrz.models import TeamUser

        # 根据班组ID筛选人员
        team_users = TeamUser.objects.filter(banzu=team_id, retire=1)  # 只获取在职人员

        # 构造返回数据
        users_data = []
        for user in team_users:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'skill': user.get_jineng_display() if user.jineng else '',
                'level': user.get_dengji_display() if user.dengji else ''
            })

        return JsonResponse({
            'success': True,
            'users': users_data,
            'count': len(users_data)
        })

    except ImportError:
        return JsonResponse({'success': False, 'message': 'bzrz应用未安装或TeamUser模型不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'服务器错误: {str(e)}'})


@login_required
def get_tool_category_api(request, category_id):
    """获取工具类别的详细信息用于编辑"""
    if not check_tools_permission(request.user, required_permission='manage_categories'):
        return JsonResponse({'success': False, 'message': '权限不足'}, status=403)
    
    try:
        category = ToolCategory.objects.get(id=category_id)
        
        # 获取该类别的权限配置
        category_perms = {
            'can_borrow_default': getattr(category, 'can_borrow_default', True),
            'can_manage_default': getattr(category, 'can_manage_default', False),
            'can_maintain_default': getattr(category, 'can_maintain_default', True),
            'can_approve_default': getattr(category, 'can_approve_default', False),
            'can_admin_default': getattr(category, 'can_admin_default', False)
        }
        
        data = {
            'id': category.id,
            'name': category.name,
            'description': '',  # ToolCategory模型没有description字段
            'tool_count': category.tool_set.count(),
            'permissions': category_perms
        }
        
        return JsonResponse({'success': True, 'data': data})
    
    except ToolCategory.DoesNotExist:
        return JsonResponse({'success': False, 'message': '未找到该工具类别'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'服务器错误: {str(e)}'})


@login_required
def update_tool_category(request, category_id):
    """更新工具类别权限配置"""
    if not check_tools_permission(request.user, required_permission='manage_categories'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '权限不足'}, status=403)
        messages.error(request, "权限不足")
        return redirect('tools:user_dashboard')
    
    try:
        category = ToolCategory.objects.get(id=category_id)
        
        if request.method == 'POST':
            # 处理AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    data = json.loads(request.body)
                    
                    # 更新类别名称
                    if 'name' in data:
                        category.name = data['name']
                    
                    # 更新权限字段（如果有提供）
                    if 'can_borrow_default' in data:
                        category.can_borrow_default = data['can_borrow_default']
                    if 'can_manage_default' in data:
                        category.can_manage_default = data['can_manage_default']
                    if 'can_maintain_default' in data:
                        category.can_maintain_default = data['can_maintain_default']
                    if 'can_approve_default' in data:
                        category.can_approve_default = data['can_approve_default']
                    if 'can_admin_default' in data:
                        category.can_admin_default = data['can_admin_default']
                    
                    category.save()
                    
                    return JsonResponse({
                        'success': True, 
                        'message': f'工具类别 "{category.name}" 更新成功！'
                    })
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'message': '无效的JSON数据'})
                except Exception as e:
                    return JsonResponse({'success': False, 'message': f'更新失败: {str(e)}'})
            
            # 处理普通表单提交
            else:
                # 获取表单数据
                name = request.POST.get('name')
                if name:
                    category.name = name
                    category.save()
                    messages.success(request, f'工具类别 "{category.name}" 更新成功！')
                return redirect('tools:simple_permissions')
        
        # GET请求 - 返回类别详情
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'description': '',  # ToolCategory模型没有description字段
                    'can_borrow_default': getattr(category, 'can_borrow_default', True),
                    'can_manage_default': getattr(category, 'can_manage_default', False),
                    'can_maintain_default': getattr(category, 'can_maintain_default', True),
                    'can_approve_default': getattr(category, 'can_approve_default', False),
                    'can_admin_default': getattr(category, 'can_admin_default', False)
                }
            })
        
        # 普通GET请求
        return render(request, 'tools/update_tool_category.html', {'category': category})
        
    except ToolCategory.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '未找到该工具类别'})
        messages.error(request, "未找到该工具类别")
        return redirect('tools:simple_permissions')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'服务器错误: {str(e)}'})
        messages.error(request, f"操作失败: {str(e)}")
        return redirect('tools:simple_permissions')


@login_required
def report_fault(request, tool_id):
    """故障报修功能 - 所有用户都可以使用"""
    tool = get_object_or_404(Tool, id=tool_id)
    
    # 检查工具状态，故障工具和报废工具不能报修
    if tool.status in ['故障', '报废']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'message': f'工具当前状态为"{tool.get_status_display()}"，无法进行故障报修'
            })
        messages.error(request, f'工具当前状态为"{tool.get_status_display()}"，无法进行故障报修')
        return redirect('tools:manage_tools')
    
    if request.method == 'POST':
        from .forms import FaultReportForm
        form = FaultReportForm(request.POST)
        if form.is_valid():
            try:
                # 获取报修人信息
                reporter_id = form.cleaned_data.get('reporter_id')
                reporter_name = form.cleaned_data.get('reporter_name')
                            
                print(f"DEBUG: 提交的报修人 ID: {reporter_id}, 报修人姓名：{reporter_name}")
                            
                if not reporter_id:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': '请选择有效的报修人'
                        })
                    messages.error(request, '请选择有效的报修人')
                    return redirect('tools:manage_tools')
                            
                # 尝试将 reporter_id 转换为整数
                try:
                    reporter_id = int(reporter_id)
                except (ValueError, TypeError):
                    print(f"DEBUG: reporter_id 无法转换为整数：{reporter_id}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': '报修人 ID 格式错误'
                        })
                    messages.error(request, '报修人 ID 格式错误')
                    return redirect('tools:manage_tools')
                                
                # 获取对应的 TeamUser 作为报修人（来自 bzrz 应用）
                from bzrz.models import TeamUser
                try:
                    reporter_teamuser = TeamUser.objects.get(id=reporter_id)
                    print(f"DEBUG: 找到报修人：{reporter_teamuser.name} (班组：{reporter_teamuser.get_banzu_display()})")
                except TeamUser.DoesNotExist:
                    print(f"DEBUG: 未找到 ID 为 {reporter_id} 的 TeamUser 用户")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': '报修人不存在'
                        })
                    messages.error(request, '报修人不存在')
                    return redirect('tools:manage_tools')
                
                # 尝试从 Admin 模型中查找匹配的用户（使用 name 匹配 username）
                from app01.models import Admin
                try:
                    admin_reporter = Admin.objects.get(username=reporter_teamuser.name)
                except Admin.DoesNotExist:
                    # 如果找不到对应的 Admin，使用当前登录用户
                    admin_reporter = request.user if hasattr(request.user, 'username') else None
                    if not admin_reporter:
                        # 如果当前用户也不是 Admin，抛出错误
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False, 
                                'message': '无法确定报修人身份'
                            })
                        messages.error(request, '无法确定报修人身份')
                        return redirect('tools:manage_tools')

                repair_record = RepairRecord.objects.create(
                    tool=tool,
                    reporter=admin_reporter,  # 使用 Admin 对象
                    fault_description=form.cleaned_data['fault_description'],
                    repair_status='待维修'
                )
                
                # 更新工具状态为故障
                tool.status = '故障'
                tool.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'工具"{tool.name}"故障报修成功！工具状态已更新为"故障"'
                    })
                else:
                    messages.success(request, f'工具"{tool.name}"故障报修成功！工具状态已更新为"故障"')
                    return redirect('tools:manage_tools')
                    
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'message': f'报修失败: {str(e)}'
                    })
                messages.error(request, f'报修失败: {str(e)}')
                return redirect('tools:manage_tools')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # 构建详细的错误信息
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                
                return JsonResponse({
                    'success': False, 
                    'message': '表单验证失败: ' + '; '.join(error_messages),
                    'errors': form.errors,
                    'form_data': dict(request.POST)  # 用于调试
                })
            # 传统请求继续处理
    
    # GET 请求或表单验证失败，返回 JSON 响应给 AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from .forms import FaultReportForm
            
        # 获取当前登录用户的班组信息
        initial_data = {}
        try:
            from app01.models import Admin
            admin_user = Admin.objects.get(username=request.user.username)
            # 根据班组 ID 获取班组名称（使用 Admin 模型的 banzu_choices）
            banzu_dict = dict(Admin.banzu_choices)
            current_team_name = banzu_dict.get(admin_user.banzu, '')
            if current_team_name:
                initial_data['team'] = current_team_name
                print(f"DEBUG: 为用户 {request.user.username} 设置默认班组：{current_team_name}")
        except Admin.DoesNotExist:
            print(f"DEBUG: 用户 {request.user.username} 的 Admin 记录不存在")
            pass
            
        form = FaultReportForm(initial=initial_data)
        return JsonResponse({
            'success': True,
            'html': render_to_string('tools/fault_report_modal.html', {
                'form': form,
                'tool': tool
            }, request=request)
        })
    
    # 传统请求 - 这种情况不应该发生，因为我们只通过 AJAX 调用
    return redirect('tools:manage_tools')


@login_required
def tool_repair_records(request, tool_id):
    """查看工具的维修记录 - 所有用户都可以访问"""
    tool = get_object_or_404(Tool, id=tool_id)

    # 获取该工具的所有维修记录，按时间倒序排列
    repair_records = RepairRecord.objects.filter(tool=tool).select_related(
        'reporter'
    ).order_by('-report_time')

    # 获取维修管理权限
    can_manage_repairs = check_tools_permission(request.user, required_permission='manage_repairs')

    return render(request, 'tools/tool_repair_records.html', {
        'tool': tool,
        'repair_records': repair_records,
        'can_manage_repairs': can_manage_repairs,
    })


@login_required
def tool_maintenance_records(request, tool_id):
    """查看工具的保养记录 - 所有用户都可以访问"""
    tool = get_object_or_404(Tool, id=tool_id)

    # 获取该工具的所有保养记录，按时间倒序排列
    maintenance_records = MaintenanceRecord.objects.filter(tool=tool).select_related(
        'maintainer'
    ).prefetch_related(
        'images'
    ).order_by('-date')

    # 获取保养执行权限
    can_perform_maintenance = check_tools_permission(request.user, required_permission='perform_maintenance')

    return render(request, 'tools/tool_maintenance_records.html', {
        'tool': tool,
        'maintenance_records': maintenance_records,
        'can_perform_maintenance': can_perform_maintenance,
    })


@login_required
def update_repair_record(request, record_id):
    """更新维修记录 - 仅具备维修管理权限的用户可访问"""
    if not check_tools_permission(request.user, required_permission='manage_repairs'):
        messages.error(request, "权限不足：您没有管理维修记录的权限。")
        return redirect('tools:manage_tools')

    repair_record = get_object_or_404(RepairRecord, id=record_id)

    if request.method == 'POST':
        form = RepairRecordForm(request.POST, instance=repair_record)
        if form.is_valid():
            repair_record = form.save(commit=False)

            # 如果维修状态改变为已完成，更新工具状态为正常
            if form.cleaned_data['repair_status'] == '已完成' and repair_record.tool.status == '故障':
                repair_record.tool.status = '正常'
                repair_record.tool.save()

            repair_record.save()
            messages.success(request, f"维修记录更新成功！")
            return redirect('tools:tool_repair_records', tool_id=repair_record.tool.id)
    else:
        form = RepairRecordForm(instance=repair_record)
    
    return render(request, 'tools/update_repair_record.html', {
        'form': form,
        'repair_record': repair_record,
        'tool': repair_record.tool
    })


@login_required
def manage_repair_records(request):
    """维修记录管理页面 - 显示所有维修记录"""
    # 获取权限信息
    can_manage_repairs = check_tools_permission(request.user, required_permission='manage_repairs')

    # 获取查询参数
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    # 构建查询
    repair_records = RepairRecord.objects.select_related('tool', 'reporter').order_by('-report_time')

    # 状态筛选
    if status_filter:
        repair_records = repair_records.filter(repair_status=status_filter)

    # 搜索功能
    if search_query:
        repair_records = repair_records.filter(
            Q(tool__code__icontains=search_query) |
            Q(tool__name__icontains=search_query) |
            Q(reporter__username__icontains=search_query) |
            Q(fault_description__icontains=search_query)
        )

    # 统计信息
    all_count = RepairRecord.objects.count()
    pending_count = RepairRecord.objects.filter(repair_status='待维修').count()
    completed_count = RepairRecord.objects.filter(repair_status='已完成').count()

    return render(request, 'tools/manage_repair_records.html', {
        'repair_records': repair_records,
        'can_manage_repairs': can_manage_repairs,
        'status_filter': status_filter,
        'search_query': search_query,
        'all_count': all_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
    })


# ==================== 自由下载区功能 ====================
import os
import json
import shutil
from datetime import datetime
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


FREE_DOWNLOAD_DIR = os.path.join(os.path.dirname(settings.BASE_DIR), '自由下载区')


def get_file_info_free(path, base_dir):
    """获取文件/文件夹信息"""
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
            'rel_path': rel_path,
        })
    items.sort(key=lambda x: (not x['is_dir'], x['name']))
    return items


def file_explorer_free(request, rel_path=''):
    """自由下载区文件浏览器主视图"""
    # 确保根目录存在
    if not os.path.exists(FREE_DOWNLOAD_DIR):
        os.makedirs(FREE_DOWNLOAD_DIR)

    abs_path = os.path.join(FREE_DOWNLOAD_DIR, rel_path)
    files = get_file_info_free(abs_path, FREE_DOWNLOAD_DIR)

    # 生成面包屑导航
    breadcrumbs = []
    parts = rel_path.split('/') if rel_path else []
    for i in range(len(parts) + 1):
        breadcrumbs.append({
            'name': parts[i - 1] if i else '首页',
            'path': '/'.join(parts[:i])
        })

    return render(request, 'tools/file_explorer_free.html', {
        'files': files,
        'breadcrumbs': breadcrumbs,
        'current_path': rel_path,
    })


@csrf_exempt
def upload_files_free(request):
    """上传文件 - 允许任意文件类型"""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        rel_path = request.POST.get('current_path', '')
        target_dir = os.path.join(FREE_DOWNLOAD_DIR, rel_path)

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                # 检查文件大小 (1000MB限制)
                if file.size > 1048576000:
                    failed_files.append({
                        'name': file.name,
                        'error': '文件大小超过限制(1000MB)'
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

        return JsonResponse({
            'status': 'success' if not failed_files else 'partial',
            'uploaded': uploaded_files,
            'failed': failed_files,
            'target_dir': target_dir
        })

    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})


@csrf_exempt
def create_folder_free(request):
    """创建文件夹 - 无权限验证"""
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        folder_name = data.get('folder_name', '')
        current_path = data.get('current_path', '')
        target_dir = os.path.join(FREE_DOWNLOAD_DIR, current_path, folder_name)

        try:
            if not folder_name:
                return JsonResponse({'status': 'error', 'message': '文件夹名称不能为空'})

            if os.path.exists(target_dir):
                return JsonResponse({'status': 'error', 'message': '文件夹已存在'})

            os.makedirs(target_dir)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})


@csrf_exempt
def rename_item_free(request):
    """重命名文件/文件夹 - 无权限验证"""
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        old_path = data.get('old_path', '')
        new_name = data.get('new_name', '')

        try:
            if not new_name:
                return JsonResponse({'status': 'error', 'message': '新名称不能为空'})

            old_full_path = os.path.join(FREE_DOWNLOAD_DIR, old_path)
            new_full_path = os.path.join(os.path.dirname(old_full_path), new_name)

            if not os.path.exists(old_full_path):
                return JsonResponse({'status': 'error', 'message': '原文件/文件夹不存在'})

            if os.path.exists(new_full_path):
                return JsonResponse({'status': 'error', 'message': '新名称已存在'})

            os.rename(old_full_path, new_full_path)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})


@csrf_exempt
def delete_files_free(request):
    """删除文件/文件夹 - 无权限验证"""
    if request.method == 'POST':
        data = request.body.decode('utf-8')
        try:
            files = json.loads(data).get('files', [])
            for rel_path in files:
                abs_path = os.path.join(FREE_DOWNLOAD_DIR, rel_path)
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

    return JsonResponse({'status': 'error', 'message': '仅支持POST请求'})


def download_file_free(request, rel_path):
    """下载文件"""
    abs_path = os.path.join(FREE_DOWNLOAD_DIR, rel_path)

    if not os.path.exists(abs_path):
        raise Http404("文件不存在")

    if os.path.isdir(abs_path):
        raise Http404("不能下载文件夹")

    # 获取文件的MIME类型
    import mimetypes
    mime_type, _ = mimetypes.guess_type(abs_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    response = FileResponse(open(abs_path, 'rb'), content_type=mime_type)
    # 设置为附件下载
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(abs_path)}"'
    return response


def preview_file_free(request, rel_path):
    """预览文件"""
    abs_path = os.path.join(FREE_DOWNLOAD_DIR, rel_path)

    if not os.path.exists(abs_path):
        raise Http404("文件不存在")

    if os.path.isdir(abs_path):
        raise Http404("不能预览文件夹")

    # 获取文件的MIME类型
    import mimetypes
    mime_type, _ = mimetypes.guess_type(abs_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    response = FileResponse(open(abs_path, 'rb'), content_type=mime_type)
    # 设置为inline预览
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(abs_path)}"'
    return response


def list_all_files_free(scan_dir, base_dir):
    """递归列出所有文件和文件夹"""
    result = []
    for root, dirs, files in os.walk(scan_dir):
        for d in dirs:
            abs_path = os.path.join(root, d)
            rel_path = os.path.relpath(abs_path, base_dir)
            result.append({'type': 'dir', 'name': d, 'rel_path': rel_path.replace("\\", "/")})
        for f in files:
            abs_path = os.path.join(root, f)
            rel_path = os.path.relpath(abs_path, base_dir)
            result.append({'type': 'file', 'name': f, 'rel_path': rel_path.replace("\\", "/")})
    return result


def search_files_free(request):
    """搜索文件"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'error': '请输入搜索关键词'})

    if not os.path.exists(FREE_DOWNLOAD_DIR):
        return JsonResponse({'results': []})

    results = []
    all_items = list_all_files_free(FREE_DOWNLOAD_DIR, FREE_DOWNLOAD_DIR)

    for item in all_items:
        if query.lower() in item['name'].lower():
            results.append(item)

    return JsonResponse({'results': results[:50]})  # 限制返回50条


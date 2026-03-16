# 基于现有Admin模型的权限管理方案

## 目标
在不改变现有app01.Admin模型结构的前提下，实现：
1. 班组级别的权限管理
2. 个人用户的权限精细化控制
3. 直观易用的管理界面

## 设计方案

### 1. 权限模型设计
```python
# tools/models.py
class TeamPermissionConfig(models.Model):
    """基于Admin班组的权限配置"""
    workshop = models.IntegerField(choices=Admin.chejian_choices, verbose_name="车间")
    team = models.IntegerField(choices=Admin.banzu_choices, verbose_name="班组")
    
    # 功能权限
    can_manage_users = models.BooleanField(default=False, verbose_name="管理用户")
    can_manage_tools = models.BooleanField(default=False, verbose_name="管理工具")
    can_approve_loans = models.BooleanField(default=False, verbose_name="审批借用")
    can_perform_maintenance = models.BooleanField(default=False, verbose_name="执行保养")
    can_manage_repairs = models.BooleanField(default=False, verbose_name="管理维修")
    
    # 班组特殊权限
    team_leader_username = models.CharField(max_length=32, blank=True, 
                                          verbose_name="班组长用户名")
    
    class Meta:
        unique_together = ('workshop', 'team')
        verbose_name = "班组权限配置"
        verbose_name_plural = "班组权限配置"

class UserPermissionOverride(models.Model):
    """个人用户权限覆盖"""
    admin_user = models.OneToOneField('app01.Admin', on_delete=models.CASCADE,
                                     verbose_name="用户")
    
    # 可覆盖的权限项
    override_can_manage_users = models.BooleanField(null=True, blank=True,
                                                   verbose_name="管理用户权限")
    override_can_manage_tools = models.BooleanField(null=True, blank=True,
                                                   verbose_name="管理工具权限")
    override_can_approve_loans = models.BooleanField(null=True, blank=True,
                                                    verbose_name="审批借用权限")
    override_can_perform_maintenance = models.BooleanField(null=True, blank=True,
                                                          verbose_name="执行保养权限")
    override_can_manage_repairs = models.BooleanField(null=True, blank=True,
                                                     verbose_name="管理维修权限")
    
    # 权限有效期
    effective_from = models.DateTimeField(null=True, blank=True, 
                                         verbose_name="生效时间")
    expires_at = models.DateTimeField(null=True, blank=True,
                                     verbose_name="过期时间")
    
    def get_effective_permission(self, permission_name):
        """获取实际生效的权限"""
        override_field = f'override_{permission_name}'
        if hasattr(self, override_field) and getattr(self, override_field) is not None:
            return getattr(self, override_field)
        # 如果没有个人覆盖，则使用班组权限
        return self.get_team_permission(permission_name)
    
    def get_team_permission(self, permission_name):
        """获取所在班组的基础权限"""
        try:
            team_config = TeamPermissionConfig.objects.get(
                workshop=self.admin_user.chejian,
                team=self.admin_user.banzu
            )
            return getattr(team_config, f'can_{permission_name}', False)
        except TeamPermissionConfig.DoesNotExist:
            return False
```

### 2. 权限检查工具函数
```python
# tools/utils.py
def check_user_permission(admin_user, permission_name):
    """检查用户是否具有指定权限"""
    # 先检查个人权限覆盖
    try:
        user_override = UserPermissionOverride.objects.get(admin_user=admin_user)
        return user_override.get_effective_permission(permission_name)
    except UserPermissionOverride.DoesNotExist:
        pass
    
    # 检查班组权限
    try:
        team_config = TeamPermissionConfig.objects.get(
            workshop=admin_user.chejian,
            team=admin_user.banzu
        )
        return getattr(team_config, f'can_{permission_name}', False)
    except TeamPermissionConfig.DoesNotExist:
        return False

def get_user_permissions(admin_user):
    """获取用户所有权限"""
    permissions = {}
    permission_list = [
        'manage_users', 'manage_tools', 'approve_loans',
        'perform_maintenance', 'manage_repairs'
    ]
    
    for perm in permission_list:
        permissions[perm] = check_user_permission(admin_user, perm)
    
    return permissions
```

### 3. 管理界面设计
```python
# tools/views.py
@login_required
def manage_team_permissions(request):
    """班组权限管理"""
    # 只允许系统管理员或车间主任访问
    if not check_tools_permission(request.user, required_permission='manage_permissions'):
        messages.error(request, "权限不足")
        return redirect('tools:user_dashboard')
    
    if request.method == 'POST':
        workshop = int(request.POST.get('workshop'))
        team = int(request.POST.get('team'))
        
        # 获取或创建班组权限配置
        team_perm, created = TeamPermissionConfig.objects.get_or_create(
            workshop=workshop,
            team=team,
            defaults={
                'team_leader_username': request.POST.get('team_leader', '')
            }
        )
        
        # 更新权限
        team_perm.can_manage_users = request.POST.get('can_manage_users') == 'on'
        team_perm.can_manage_tools = request.POST.get('can_manage_tools') == 'on'
        team_perm.can_approve_loans = request.POST.get('can_approve_loans') == 'on'
        team_perm.can_perform_maintenance = request.POST.get('can_perform_maintenance') == 'on'
        team_perm.can_manage_repairs = request.POST.get('can_manage_repairs') == 'on'
        team_perm.team_leader_username = request.POST.get('team_leader', '')
        team_perm.save()
        
        messages.success(request, "班组权限更新成功")
        return redirect('tools:manage_team_permissions')
    
    # 获取所有班组配置
    team_configs = TeamPermissionConfig.objects.all()
    
    # 准备车间和班组选择数据
    workshop_choices = dict(Admin.chejian_choices)
    team_choices = dict(Admin.banzu_choices)
    
    context = {
        'team_configs': team_configs,
        'workshop_choices': workshop_choices,
        'team_choices': team_choices,
        'chejian_choices': Admin.chejian_choices,
        'banzu_choices': Admin.banzu_choices
    }
    
    return render(request, 'tools/manage_team_permissions.html', context)

@login_required
def manage_user_permissions(request):
    """个人用户权限管理"""
    if not check_tools_permission(request.user, required_permission='manage_permissions'):
        messages.error(request, "权限不足")
        return redirect('tools:user_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            admin_user = Admin.objects.get(username=username)
            
            # 获取或创建用户权限覆盖
            user_perm, created = UserPermissionOverride.objects.get_or_create(
                admin_user=admin_user
            )
            
            # 更新个人权限覆盖
            perms = ['manage_users', 'manage_tools', 'approve_loans', 
                    'perform_maintenance', 'manage_repairs']
            
            for perm in perms:
                override_value = request.POST.get(f'override_{perm}')
                if override_value == 'true':
                    setattr(user_perm, f'override_{perm}', True)
                elif override_value == 'false':
                    setattr(user_perm, f'override_{perm}', False)
                else:
                    setattr(user_perm, f'override_{perm}', None)  # 使用班组默认权限
            
            # 设置有效期
            effective_from = request.POST.get('effective_from')
            expires_at = request.POST.get('expires_at')
            
            if effective_from:
                user_perm.effective_from = timezone.datetime.strptime(
                    effective_from, '%Y-%m-%d %H:%M'
                )
            if expires_at:
                user_perm.expires_at = timezone.datetime.strptime(
                    expires_at, '%Y-%m-%d %H:%M'
                )
            
            user_perm.save()
            messages.success(request, f"用户 {username} 的权限已更新")
            
        except Admin.DoesNotExist:
            messages.error(request, f"用户 {username} 不存在")
        
        return redirect('tools:manage_user_permissions')
    
    # 获取所有需要管理的用户
    users = Admin.objects.all().order_by('chejian', 'banzu', 'username')
    
    context = {
        'users': users,
        'team_permission_configs': TeamPermissionConfig.objects.all()
    }
    
    return render(request, 'tools/manage_user_permissions.html', context)
```

### 4. 模板界面示例
```html
<!-- tools/templates/tools/manage_team_permissions.html -->
{% extends 'tools/base.html' %}

{% block title %}班组权限管理{% endblock %}

{% block content %}
<div class="container-fluid">
    <h2>班组权限管理</h2>
    
    <!-- 快速配置面板 -->
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>快速配置班组权限</h5>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        <div class="row">
                            <div class="col-md-3">
                                <select name="workshop" class="form-control" required>
                                    <option value="">选择车间</option>
                                    {% for code, name in chejian_choices %}
                                        <option value="{{ code }}">{{ name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-3">
                                <select name="team" class="form-control" required>
                                    <option value="">选择班组</option>
                                    {% for code, name in banzu_choices %}
                                        <option value="{{ code }}">{{ name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-3">
                                <input type="text" name="team_leader" class="form-control" 
                                       placeholder="班组长用户名">
                            </div>
                            <div class="col-md-3">
                                <button type="submit" class="btn btn-primary">配置权限</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 班组权限列表 -->
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5>现有班组权限配置</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>车间</th>
                                    <th>班组</th>
                                    <th>班组长</th>
                                    <th>用户管理</th>
                                    <th>工具管理</th>
                                    <th>借用审批</th>
                                    <th>执行保养</th>
                                    <th>维修管理</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for config in team_configs %}
                                <tr>
                                    <td>{{ config.get_workshop_display }}</td>
                                    <td>{{ config.get_team_display }}</td>
                                    <td>{{ config.team_leader_username|default:"未设置" }}</td>
                                    <td>
                                        {% if config.can_manage_users %}
                                            <span class="badge bg-success">✓</span>
                                        {% else %}
                                            <span class="badge bg-secondary">✗</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if config.can_manage_tools %}
                                            <span class="badge bg-success">✓</span>
                                        {% else %}
                                            <span class="badge bg-secondary">✗</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if config.can_approve_loans %}
                                            <span class="badge bg-success">✓</span>
                                        {% else %}
                                            <span class="badge bg-secondary">✗</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if config.can_perform_maintenance %}
                                            <span class="badge bg-success">✓</span>
                                        {% else %}
                                            <span class="badge bg-secondary">✗</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if config.can_manage_repairs %}
                                            <span class="badge bg-success">✓</span>
                                        {% else %}
                                            <span class="badge bg-secondary">✗</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary" 
                                                onclick="editTeamPermission({{ config.id }})">
                                            编辑
                                        </button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- 编辑模态框 -->
<div class="modal fade" id="editTeamModal" tabindex="-1">
    <!-- 模态框内容 -->
</div>
{% endblock %}
```

## 实施优势

✅ **零破坏性改动**：完全基于现有Admin模型
✅ **权限继承机制**：个人权限可覆盖班组权限
✅ **灵活配置**：支持权限有效期设置
✅ **直观界面**：清晰展示班组和个人权限状态
✅ **易于维护**：符合现有系统架构习惯

这个方案既满足了你的需求，又避免了大规模的系统重构，你觉得如何？
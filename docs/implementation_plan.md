# 统一班组车间管理实施计划

## 第一阶段：基础设施建设（1-2周）

### 1. 创建核心模型
```python
# app01/models.py
class Organization(models.Model):
    """统一组织架构模型"""
    WORKSHOP_CHOICES = [
        ('修配车间', '修配车间'),
        ('修车车间', '修车车间'), 
        ('管理员', '管理员')
    ]
    
    TEAM_CHOICES = [
        ('架车班', '架车班'),
        ('轮轴班', '轮轴班'),
        ('台车班', '台车班'),
        # ... 其他班组
    ]
    
    name = models.CharField(max_length=100)
    org_type = models.CharField(max_length=20, choices=[
        ('workshop', '车间'),
        ('team', '班组')
    ])
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

class UnifiedUserProfile(models.Model):
    """统一用户配置"""
    admin_user = models.OneToOneField('Admin', on_delete=models.CASCADE)
    workshop = models.ForeignKey(Organization, 
                                limit_choices_to={'org_type': 'workshop'},
                                on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Organization,
                            limit_choices_to={'org_type': 'team'}, 
                            on_delete=models.SET_NULL, null=True)
    
    # 兼容字段 - 自动生成
    @property
    def chejian(self):
        """兼容 app01.Admin.chejian """
        mapping = {'修配车间': 1, '修车车间': 2, '管理员': 0}
        return mapping.get(self.workshop.name if self.workshop else '', 0)
    
    @property  
    def banzu(self):
        """兼容 app01.Admin.banzu"""
        # 可以建立ID映射或直接返回班组名称
        return self.team.name if self.team else ''
```

### 2. 数据迁移脚本
```python
# migrations/0002_unified_organization.py
def migrate_existing_data(apps, schema_editor):
    Admin = apps.get_model('app01', 'Admin')
    Organization = apps.get_model('app01', 'Organization') 
    UnifiedUserProfile = apps.get_model('app01', 'UnifiedUserProfile')
    
    # 创建车间组织
    workshops = [
        Organization.objects.get_or_create(
            name=name, 
            code=f"WS{code}",
            org_type='workshop'
        )[0] for code, name in Admin.chejian_choices
    ]
    
    # 创建班组组织  
    teams = [
        Organization.objects.get_or_create(
            name=name,
            code=f"TM{i}",
            org_type='team' 
        )[0] for i, (code, name) in enumerate(Admin.banzu_choices)
    ]
    
    # 迁移现有用户数据
    for admin in Admin.objects.all():
        profile, created = UnifiedUserProfile.objects.get_or_create(
            admin_user=admin
        )
        # 根据现有数据设置关联
        profile.workshop = Organization.objects.filter(
            org_type='workshop', 
            name=dict(Admin.chejian_choices).get(admin.chejian, '')
        ).first()
        
        profile.team = Organization.objects.filter(
            org_type='team',
            name=dict(Admin.banzu_choices).get(admin.banzu, '')  
        ).first()
        
        profile.save()
```

## 第二阶段：兼容层实现（1周）

### 1. 保持现有接口不变
```python
# app01/models.py - 修改Admin模型
class Admin(models.Model):
    # 保留原有字段但标记为deprecated
    chejian = models.IntegerField(_('车间'), choices=chejian_choices, editable=False)
    banzu = models.IntegerField(_('班组'), choices=banzu_choices, editable=False)
    
    # 通过属性方法连接到统一系统
    @property
    def unified_profile(self):
        return getattr(self, 'unifieduserprofile', None)
    
    @property
    def actual_chejian(self):
        """获取实际车间信息"""
        if self.unified_profile and self.unified_profile.workshop:
            return self.unified_profile.workshop.name
        return dict(self.chejian_choices).get(self.chejian, '')
    
    @property
    def actual_banzu(self):
        """获取实际班组信息"""  
        if self.unified_profile and self.unified_profile.team:
            return self.unified_profile.team.name
        return dict(self.banzu_choices).get(self.banzu, '')
```

### 2. 更新相关查询
```python
# 替换硬编码查询
# 旧方式：
Admin.objects.filter(banzu=1)  # 架车班

# 新方式：
workshop_org = Organization.objects.get(name='架车班', org_type='team')
Admin.objects.filter(unifieduserprofile__team=workshop_org)
```

## 第三阶段：逐步迁移（1-2月）

### 1. 新功能使用统一模型
- 用户管理界面改为使用Organization管理
- 权限系统基于统一模型重构
- 报表统计使用统一数据源

### 2. 逐步替换旧查询
```python
# tools应用中的查询替换示例
# 旧：
users = Admin.objects.filter(banzu=request.user.banzu)

# 新：
current_team = request.user.unified_profile.team
users = Admin.objects.filter(unifieduserprofile__team=current_team)
```

## 风险控制措施

### 1. 双轨运行
- 同时维护新旧两套数据
- 提供切换开关
- 完整的回滚方案

### 2. 监控告警
- 关键业务指标监控
- 性能基准对比
- 异常情况及时告警

### 3. 分阶段上线
- 先在测试环境验证
- 小范围灰度发布
- 全面推广前充分验证

## 预期收益

✅ **数据一致性**：消除多套班组体系带来的数据不一致
✅ **维护简化**：统一管理界面，降低维护成本  
✅ **查询优化**：减少重复数据，提升查询性能
✅ **扩展性好**：支持未来组织架构调整
✅ **风险可控**：渐进式迁移，随时可以回退

这种方案能够最大程度减少对你现有代码的影响，同时实现真正的统一管理。
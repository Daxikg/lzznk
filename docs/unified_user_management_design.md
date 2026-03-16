# 统一用户班组管理体系设计方案

## 当前痛点分析

### 多套体系并存
```
app01.Admin
├── banzu (固定班组选择)
└── chejian (固定车间选择)

tools.Team  
├── 动态班组管理
└── tools.Profile.team (用户班组关联)

tools.ToolsUserProfile
└── assigned_team (工具系统班组关联)
```

### 主要问题
1. **数据冗余**：相同样概念在多处维护
2. **同步困难**：班组信息变更需要多处更新
3. **查询复杂**：跨系统查询需要多次JOIN
4. **权限分散**：不同应用维护各自的权限逻辑

## 推荐统一方案

### 核心设计原则
- **渐进式迁移**：最小化对现有业务的影响
- **向后兼容**：保留现有接口，逐步替换底层实现
- **集中管理**：统一的数据源和管理界面

### 新架构设计

```python
# 统一组织架构模型
class Organization(models.Model):
    """组织架构基础模型"""
    name = models.CharField(max_length=100, verbose_name="名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="编码")
    org_type = models.CharField(max_length=20, choices=[
        ('company', '公司'),
        ('workshop', '车间'), 
        ('department', '部门'),
        ('team', '班组')
    ], verbose_name="组织类型")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, 
                              null=True, blank=True, verbose_name="上级组织")
    description = models.TextField(blank=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    class Meta:
        verbose_name = "组织架构"
        verbose_name_plural = "组织架构"

class UnifiedUser(models.Model):
    """统一用户模型（继承自Admin）"""
    admin_user = models.OneToOneField('app01.Admin', on_delete=models.CASCADE, 
                                     verbose_name="基础用户")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name="所属组织")
    
    # 缓存常用字段提升查询性能
    cached_workshop = models.CharField(max_length=50, blank=True, 
                                      verbose_name="缓存车间")
    cached_team = models.CharField(max_length=50, blank=True,
                                  verbose_name="缓存班组")
    
    def sync_organization_cache(self):
        """同步组织缓存信息"""
        if self.organization:
            # 根据组织树结构向上查找车间信息
            current = self.organization
            while current:
                if current.org_type == 'workshop':
                    self.cached_workshop = current.name
                elif current.org_type == 'team':
                    self.cached_team = current.name
                current = current.parent
            self.save(update_fields=['cached_workshop', 'cached_team'])

# 兼容性代理模型
class WorkshopProxy(models.Model):
    """车间代理模型 - 兼容现有代码"""
    unified_user = models.OneToOneField(UnifiedUser, on_delete=models.CASCADE)
    
    @property
    def chejian_display(self):
        """兼容原有的 chejian 显示"""
        workshop_mapping = {
            '修配车间': 1,
            '修车车间': 2,
            '管理员': 0
        }
        return workshop_mapping.get(self.unified_user.cached_workshop, 0)

class TeamProxy(models.Model):
    """班组代理模型 - 兼容现有代码"""  
    unified_user = models.OneToOneField(UnifiedUser, on_delete=models.CASCADE)
    
    @property
    def banzu_display(self):
        """兼容原有的 banzu 显示"""
        # 可以建立映射关系或直接使用班组名称
        return self.unified_user.cached_team
```

## 迁移策略

### 阶段一：基础架构搭建
1. 创建新的组织架构表
2. 建立统一用户模型
3. 实现数据迁移脚本

### 阶段二：渐进式替换
1. 新功能使用统一模型
2. 逐步改造现有功能
3. 保持双轨运行

### 阶段三：完全统一
1. 下线旧模型
2. 清理冗余代码
3. 优化查询性能

## 对现有系统的影响评估

### 低影响变更
✅ 只需修改模型层，视图和模板基本无需改动
✅ 通过代理模型保持API兼容性
✅ 可以逐步迁移，风险可控

### 需要注意的点
⚠️ 数据迁移需要仔细规划
⚠️ 权限系统需要重新梳理
⚠️ 历史数据的兼容性处理

## 实施建议

### 短期目标（1-2周）
- 完成新模型设计和数据库迁移
- 建立兼容层确保现有功能正常

### 中期目标（1-2月）  
- 逐步将新功能接入统一系统
- 完善管理界面和API

### 长期目标（3-6月）
- 完全替换旧系统
- 优化性能和用户体验

这个方案能够在保证业务连续性的前提下，实现真正的统一管理。
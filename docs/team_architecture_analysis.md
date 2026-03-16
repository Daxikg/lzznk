# 班组架构分析与优化建议

## 当前问题分析

### 双班组系统现状
1. **app01.Admin 模型**：使用固定的 `banzu_choices` 班组选项
2. **tools.Team 模型**：支持动态创建班组

### 主要冲突点
- 数据冗余：相同概念的班组在两个地方维护
- 同步困难：用户在两个系统中的班组归属可能不一致
- 权限分散：需要在两套班组系统中分别管理权限

## 推荐解决方案

### 方案一：统一班组管理（推荐）
将 tools.Team 作为主班组系统，app01.Admin 引用 tools 班组：

```python
# 修改 app01/models.py
class Admin(models.Model):
    # 移除原有的 banzu 字段
    # banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    
    # 改为外键引用 tools 班组
    team = models.ForeignKey('tools.Team', on_delete=models.SET_NULL, 
                           null=True, blank=True, verbose_name="所属班组")
```

### 方案二：保持现状但加强同步
建立同步机制确保两个系统的班组信息一致：

```python
# 在 tools/models.py 中添加信号处理器
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Team)
def sync_team_to_admin_choices(sender, instance, created, **kwargs):
    """当创建新班组时，同步更新 Admin 的班组选择"""
    # 可以通过缓存或其他机制动态提供班组选项
    pass
```

### 方案三：明确职责分离
- **app01.Admin.banzu**：用于组织架构管理（人事、考勤等）
- **tools.Team**：专门用于工具管理系统的工作班组

## 实施建议

1. **短期**：保持现有架构，但建立清晰的数据治理规范
2. **中期**：评估是否需要统一班组管理
3. **长期**：考虑重构为单一用户班组系统

## 注意事项

⚠️ **重要提醒**：
- 任何结构性改动都需要考虑历史数据迁移
- 建议先在测试环境验证方案可行性
- 确保不影响现有的业务流程
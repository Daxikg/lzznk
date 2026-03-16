from ckeditor.fields import RichTextField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext as _
from django import forms
from django.contrib.auth.hashers import make_password, check_password


class Admin(models.Model):
    ROLE_CHOICES = (
        ('role1', '总管理员'),
        ('role2', '架车班'),
        ('role3', '轮轴班'),
        ('role4', '台车班'),
        ('role5', '架车班手持机'),
        ('role6', '轮轴班手持机'),
        ('role7', '调度员'),
        ('role8', '安全员'),
        ('role9', '技术员'),
        ('role10', '内制动班'),
        ('role11', '外制动班'),
        ('role12', '车钩班'),
        ('role13', '探伤班'),
        ('role14', '调车组'),
        ('role15', '车体班'),
        ('role16', '预修班'),
        ('role18', '信息班'),
        ('role19', '修配管理员'),
        ('role20', '修车管理员'),
    )
    banzu_choices = (
        (1, "架车班"),
        (2, "轮轴班"),
        (3, "台车班"),
        (4, "内制动班"),
        (5, "外制动班"),
        (6, "车钩班"),
        (7, "探伤班"),
        (8, "调车组"),
        (9, "车体班"),
        (10, "预修班"),
        (12, "信息班"),
        (13, "干部"),
    )
    chejian_choices = (
        (0, "管理员"),
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices)
    username = models.CharField(verbose_name='用户名', max_length=32, unique=True)
    password = models.CharField(verbose_name='密码', max_length=128)  # 增加长度以支持哈希
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    role = models.CharField(verbose_name='角色', max_length=32, choices=ROLE_CHOICES)
    
    # 添加Django认证所需的字段
    last_login = models.DateTimeField(_('最后登录时间'), blank=True, null=True)
    is_superuser = models.BooleanField(_('超级用户状态'), default=False)
    
    # 添加用于Django认证的方法
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_staff(self):
        return self.is_superuser

    def get_role_display(self):
        dict_roles = dict(self.ROLE_CHOICES)
        return dict_roles.get(self.role)
    
    def __str__(self):
        return self.username


class initial(models.Model):
    todaytime = models.DateTimeField(_('日期'))

    taiwei_choices = (
        (1, "7-1"),
        (2, "7-2"),
        (3, "7-3"),
        (4, "7-4"),
        (5, "7-5"),
        (6, "7-6"),
        (7, "7-7"),
        (8, "7-8"),
        (9, "7-9"),
        (10, "8-1"),
        (11, "8-2"),
        (12, "8-3"),
        (13, "8-4"),
        (14, "8-5"),
        (15, "8-6"),
        (16, "8-7"),
        (17, "8-8"),
        (18, "8-9"),
        (19, "9-1"),
        (20, "9-2"),
        (21, "9-3"),
        (22, "9-4"),
        (23, "9-5"),
        (24, "9-6"),
        (25, "9-7"),
        (26, "9-8"),
        (27, "9-9"),
    )
    taiwei = models.SmallIntegerField(_("台位顺序"), choices=taiwei_choices, )

    shunxu_choices = (
        (1, "一次入库"),
        (2, "二次入库"),
        (3, "三次入库"),
    )
    shunxu = models.SmallIntegerField(_("进车顺序"), choices=shunxu_choices, )

    chegou1 = models.IntegerField(_('一位钩高'), blank=True, null=True,
                                  validators=[MinValueValidator(850), MaxValueValidator(999)])
    chegou2 = models.IntegerField(_('二位钩高'), blank=True, null=True,
                                  validators=[MinValueValidator(850), MaxValueValidator(999)])
    dianban1 = models.IntegerField(_('一位垫板'), blank=True, null=True,
                                   validators=[MinValueValidator(0), MaxValueValidator(50)])
    dianban2 = models.IntegerField(_('二位垫板'), blank=True, null=True,
                                   validators=[MinValueValidator(0), MaxValueValidator(50)])
    lunjing1 = models.IntegerField(_('一位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    lunjing2 = models.IntegerField(_('二位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    lunjing3 = models.IntegerField(_('三位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    lunjing4 = models.IntegerField(_('四位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    pangcheng1 = models.IntegerField(_('一位上旁承'), blank=True, null=True,
                                     validators=[MinValueValidator(0), MaxValueValidator(35)])
    pangcheng2 = models.IntegerField(_('二位上旁承'), blank=True, null=True,
                                     validators=[MinValueValidator(0), MaxValueValidator(35)])

    xiucheng = models.CharField(_("货车修程"), max_length=10, choices=(("段", "段"), ("厂", "厂"), ("临", "临")),
                                blank=True, null=True, default="段")
    chexing = models.CharField(_("车种车型"), max_length=20, blank=True, null=True)

    nianxian_choices = (
        (4, "0.8"),
        (5, "0.9"),
        (6, "0.10"),
        (7, "0.11"),
        (1, "1"),
        (8, "1.1"),
        (9, "1.2"),
        (10, "1.3"),
        (11, "1.4"),
        (12, "1.5"),
        (2, "1.6"),
        (13, "1.7"),
        (14, "1.8"),
        (15, "1.9"),
        (16, "1.10"),
        (17, "1.11"),
        (3, "2"),
        (18, "2.1"),
        (19, "2.2"),
        (20, "2.3"),
        (21, "2.4"),
        (22, "2.5"),
    )
    nianxian = models.SmallIntegerField(_("轮对年限"), choices=nianxian_choices, blank=True, null=True)

    beizhu_choices = (
        (1, "放7-1前"),
        (2, "放7-2前"),
        (3, "放7-3前"),
        (4, "放7-4前"),
        (5, "放7-5前"),
        (6, "放7-6前"),
        (7, "放7-7前"),
        (8, "放7-8前"),
        (9, "放7-9前"),
        (10, "放7-9后"),
        (11, "放8-1前"),
        (12, "放8-2前"),
        (13, "放8-3前"),
        (14, "放8-4前"),
        (15, "放8-5前"),
        (16, "放8-6前"),
        (17, "放8-7前"),
        (18, "放8-8前"),
        (19, "放8-9前"),
        (20, "放8-9后"),
        (21, "放9-1前"),
        (22, "放9-2前"),
        (23, "放9-3前"),
        (24, "放9-4前"),
        (25, "放9-5前"),
        (26, "放9-6前"),
        (27, "放9-7前"),
        (28, "放9-8前"),
        (29, "放9-9前"),
        (30, "放9-9后"),
    )
    beizhu = models.SmallIntegerField(_("临时出车顺序"), choices=beizhu_choices, blank=True, null=True)

    is_updated = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)


class bogie(models.Model):
    taiwei_choices = (
        (1, "7-1"),
        (2, "7-2"),
        (3, "7-3"),
        (4, "7-4"),
        (5, "7-5"),
        (6, "7-6"),
        (7, "7-7"),
        (8, "7-8"),
        (9, "7-9"),
        (10, "8-1"),
        (11, "8-2"),
        (12, "8-3"),
        (13, "8-4"),
        (14, "8-5"),
        (15, "8-6"),
        (16, "8-7"),
        (17, "8-8"),
        (18, "8-9"),
        (19, "9-1"),
        (20, "9-2"),
        (21, "9-3"),
        (22, "9-4"),
        (23, "9-5"),
        (24, "9-6"),
        (25, "9-7"),
        (26, "9-8"),
        (27, "9-9"),
    )
    taiwei = models.SmallIntegerField(_("台位顺序"), choices=taiwei_choices)

    shunxu_choices = (
        (1, "一次入库"),
        (2, "二次入库"),
        (3, "三次入库"),
    )
    shunxu = models.SmallIntegerField(_("出车顺序"), choices=shunxu_choices)

    dianban1 = models.IntegerField(_('一位垫板'), blank=True, null=True,
                                   validators=[MinValueValidator(-20), MaxValueValidator(60)])
    dianban2 = models.IntegerField(_('二位垫板'), blank=True, null=True,
                                   validators=[MinValueValidator(-20), MaxValueValidator(60)])
    lunjing1 = models.IntegerField(_('一位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    lunjing2 = models.IntegerField(_('二位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    lunjing3 = models.IntegerField(_('三位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    lunjing4 = models.IntegerField(_('四位轮径'), blank=True, null=True,
                                   validators=[MinValueValidator(750), MaxValueValidator(850)])
    todaytime = models.DateTimeField(_('日期'))

    is_updated = models.BooleanField(default=False)


class order(models.Model):
    gudao1_choices = (
        (9, "9道"),
        (8, "8道"),
        (7, "7道")
    )
    gudao1 = models.SmallIntegerField(_("第一线"), choices=gudao1_choices)
    gudao2_choices = (
        (7, "7道"),
        (8, "8道"),
        (9, "9道")
    )
    gudao2 = models.SmallIntegerField(_("第二线"), choices=gudao2_choices)
    gudao3_choices = (
        (8, "8道"),
        (7, "7道"),
        (9, "9道")
    )
    gudao3 = models.SmallIntegerField(_("第三线"), choices=gudao3_choices)
    todaytime = models.DateTimeField(_('日期'))


class tasks(models.Model):
    guotie1 = models.IntegerField(_('年度国铁厂修总任务'), blank=True, null=True)
    guotie2 = models.IntegerField(_('年度国铁厂修已完成'), blank=True, null=True)
    guotie3 = models.IntegerField(_('年度自备厂修已完成'), blank=True, null=True)
    guotie7 = models.IntegerField(_('年度自备厂修总任务'), blank=True, null=True)
    guotie4 = models.IntegerField(_('年度国铁段修总任务'), blank=True, null=True)
    guotie5 = models.IntegerField(_('年度国铁段修已完成'), blank=True, null=True)
    guotie6 = models.IntegerField(_('年度自备段修已完成'), blank=True, null=True)
    guotie8 = models.IntegerField(_('年度自备段修总任务'), blank=True, null=True)
    pengche1 = models.IntegerField(_('棚车适应改造总任务'), blank=True, null=True)
    pengche2 = models.IntegerField(_('棚车适应改造已完成'), blank=True, null=True)
    pengche3 = models.IntegerField(_('棚车门锁改造总任务'), blank=True, null=True)
    pengche4 = models.IntegerField(_('棚车门锁改造已完成'), blank=True, null=True)
    changche1 = models.IntegerField(_('敞车门锁改造总任务'), blank=True, null=True)
    changche2 = models.IntegerField(_('敞车门锁改造已完成'), blank=True, null=True)

    duanxiu1 = models.IntegerField(_('月计划国铁段修总任务'), blank=True, null=True)
    duanxiu2 = models.IntegerField(_('月完成国铁段修总任务'), blank=True, null=True)
    duanxiu3 = models.IntegerField(_('月计划局管内用车段修'), blank=True, null=True)
    duanxiu4 = models.IntegerField(_('月完成局管内用车段修'), blank=True, null=True)
    duanxiu5 = models.IntegerField(_('月计划自备段修'), blank=True, null=True)
    duanxiu6 = models.IntegerField(_('月完成自备段修'), blank=True, null=True)
    changxiu1 = models.IntegerField(_('月计划国铁厂修'), blank=True, null=True)
    changxiu2 = models.IntegerField(_('月完成国铁厂修'), blank=True, null=True)
    changxiu3 = models.IntegerField(_('月计划自备厂修'), blank=True, null=True)
    changxiu4 = models.IntegerField(_('月完成自备厂修'), blank=True, null=True)
    heji1 = models.IntegerField(_('月计划合计'), blank=True, null=True)
    heji2 = models.IntegerField(_('月完成合计'), blank=True, null=True)
    diban1 = models.IntegerField(_('月度复合地板'), blank=True, null=True)
    diban2 = models.IntegerField(_('年度复合地板'), blank=True, null=True)
    TgaiK = models.IntegerField(_('T改K'), blank=True, null=True)
    linxiu = models.IntegerField(_('月计划临修车'), blank=True, null=True)
    linxiu1 = models.IntegerField(_('月完成临修车'), blank=True, null=True)
    zhengzhi = models.IntegerField(_('木地板专项修'), blank=True, null=True)
    JSQ = models.IntegerField(_('年度JSQ段修完成总数'), blank=True, null=True)
    time1 = models.DateTimeField(_('劳动安全开始时间'), blank=True, null=True)
    time2 = models.DateTimeField(_('行车安全开始时间'), blank=True, null=True)
    time3 = models.DateTimeField(_('车辆故障开始时间'), blank=True, null=True)


class Transactions(models.Model):
    shiwubiaoti = models.TextField(_('重要事务标题'))
    user = models.TextField(_('发布人'), blank=True, null=True)
    shiwuneirong = RichTextField(_('重要事务内容'), blank=True, null=True)
    todaytime = models.DateTimeField(_('日期'))
    chejian_choices = (
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices)


class TransactionAttachment(models.Model):
    transaction = models.ForeignKey(Transactions, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(_('附件'), upload_to='attachment/%Y-%m-%d/', max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class TransactionReads(models.Model):
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

from datetime import date

from django.db import models
from django.utils.translation import gettext as _


class TeamLog(models.Model):
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
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    shijian = models.DateTimeField(_('学习时间'))
    didian = models.TextField(_('学习地点'), blank=True, null=True)
    zhuchiren = models.TextField(_('主持人'), blank=True, null=True)
    renyuan1 = models.IntegerField(_('应到人员'), blank=True, null=True)
    renyuan2 = models.IntegerField(_('实到人员'), blank=True, null=True)
    renyuan3 = models.TextField(_('请假人员及原因'), blank=True, null=True)
    neirong = models.TextField(_('内容'), blank=True, null=True)
    pic = models.ImageField(_('学习现场照片'), upload_to='meeting/%Y/%m/%d/', max_length=100, blank=True, null=True)
    pic1 = models.ImageField(_('签到照片'), upload_to='meeting/%Y/%m/%d/', max_length=100, blank=True, null=True)


class TeamUser(models.Model):
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
        (15, "修配综合班"),
        (16, "修车综合班"),
        (17, "修配领导"),
        (18, "修车领导"),
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    jineng_choices = (
        (1, "车辆钳工"),
        (2, "制动钳工（外）"),
        (3, "制动钳工（内）"),
        (4, "熔焊工"),
        (5, "探伤工"),
        (6, "轮轴装修工"),
        (7, "连接员"),
        (8, "轨道车司机"),
        (9, "铆工"),
    )
    jineng = models.IntegerField(_('工种'), choices=jineng_choices, blank=True, null=True)
    certificate = models.TextField(_('持证情况'), blank=True, null=True)
    dengji_choices = (
        (1, "初级工"),
        (2, "中级工"),
        (3, "高级工"),
        (4, "技师"),
        (5, "高级技师"),
    )
    dengji = models.IntegerField(_('技能等级'), choices=dengji_choices, blank=True, null=True)
    marriage_choices = (
        (1, "已婚"),
        (2, "未婚"),
    )
    marriage = models.IntegerField(_('婚姻状况'), choices=marriage_choices, blank=True, null=True)
    retire_choices = (
        (1, "在职"),
        (2, "退休"),
        (3, "调离"),
    )
    retire = models.IntegerField(_('在职/退休/调离'), default=1, choices=retire_choices)
    gender_choices = (
        (1, "男"),
        (2, "女"),
    )
    gender = models.IntegerField(_('性别'), choices=gender_choices, blank=True, null=True)
    birth = models.DateField(_('出生年月日'), blank=True, null=True)
    name = models.TextField(_('姓名'), )
    number = models.TextField(_('电话号码'), blank=True, null=True)
    wenhua_choices = (
        (1, "初中"),
        (2, "高中"),
        (3, "中专"),
        (4, "中技"),
        (5, "大学专科"),
        (6, "大学本科"),
        (7, "研究生及以上"),
    )
    wenhua = models.IntegerField(_('文化程度'), choices=wenhua_choices, blank=True, null=True)
    jiguan = models.TextField(_('籍贯'), blank=True, null=True)
    mianmao_choices = (
        (1, "团员"),
        (2, "群众"),
        (3, "党员"),
    )
    mianmao = models.IntegerField(_('政治面貌'), choices=mianmao_choices, blank=True, null=True)
    didian = models.TextField(_('探亲地点'), blank=True, null=True)
    leibie_choices = (
        (1, "探父母"),
        (2, "探配偶"),
    )
    leibie = models.IntegerField(_('探亲类别'), choices=leibie_choices, blank=True, null=True)
    award = models.TextField(_('获奖情况'), blank=True, null=True)
    beizhu = models.TextField(_('备注'), blank=True, null=True)

    def calculate_age(self):
        if self.birth:
            today = date.today()
            return today.year - self.birth.year - (
                    (today.month, today.day) < (self.birth.month, self.birth.day)
            )
        return None

    def has_certificate_pic(self):
        return self.certificates.filter(pic__isnull=False).exists()


class Certificate(models.Model):
    """
    每个Certificate对象关联了一个用户、一个证书类型和一个照片。这样，你可以为每个用户存储任意数量和类型的证书。
    在TeamUser模型中添加一个certificates的反向关联，而不是certificate_set。然后你就可以使用以下方式来获取一个用户的所有证书：
    user = TeamUser.objects.get(id=some_id)
    certificates = user.certificates.all()
    """
    CERTIFICATE_TYPES = (
        ('熔化焊接与热切割作业', '熔化焊接与热切割作业'),
        ('A.特种设备安全管理', 'A.特种设备安全管理'),
        ('Q1.起重机指挥', 'Q1.起重机指挥'),
        ('Q2.起重机司机', 'Q2.起重机司机'),
        ('N1.叉车司机', 'N1.叉车司机'),
    )
    user = models.ForeignKey('TeamUser', related_name='certificates', on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=CERTIFICATE_TYPES)
    pic = models.ImageField(upload_to='users/%Y/%m/%d/', max_length=100, blank=True, null=True)


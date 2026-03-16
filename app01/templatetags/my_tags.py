# my_tags.py
from django import template
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter
def get_item(dictionary, key):
    if dictionary is not None and key is not None:
        return dictionary.get(key)
    else:
        return None


@register.filter
def make_list(value, arg):
    return range(value, int(arg)+1)


@register.simple_tag
def months_range():
    return range(1, 13)


@register.filter
def contains_option(beizhu, option_value):
    """检查备注中是否包含某个选项值"""
    if not beizhu:
        return False
    return option_value in beizhu.split('；')


@register.simple_tag
def num_times(n):
    return range(1, int(n) + 1)


@register.filter
def endswith(value, arg):
    return str(value).lower().endswith(arg)


@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def dict_get(d, k):
    if d is None:
        return None
    return d.get(k, None)


@register.filter
def index(List, i):
    try:
        return List[int(i)]
    except:
        return ''


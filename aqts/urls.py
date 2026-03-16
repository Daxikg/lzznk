from django.urls import path
from . import views

app_name = 'aqts'

urlpatterns = [
    path('anquantianshu/', views.anquantianshu_list, name='anquantianshu_list'),
    path('anquantianshu/add/', views.add_anquantianshu, name='add_anquantianshu'),
    path('anquantianshu/<int:id>/', views.anquantianshu_detail, name='anquantianshu_detail'),
    path('anquantianshu/edit/<int:id>/', views.edit_anquantianshu, name='edit_anquantianshu'),
    path('anquantianshu/delete/<int:id>/', views.delete_anquantianshu, name='delete_anquantianshu'),
]

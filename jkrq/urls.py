from django.urls import path
from . import views

app_name = 'jkrq'

urlpatterns = [
    path('', views.jkrq_login, name='jkrq_login'),
    path('jkrq_login/', views.jkrq_login, name='jkrq_login'),
    path('jkrq_index/', views.jkrq_index, name='jkrq_index'),
    path('jkrq_list1/', views.jkrq_list1, name='jkrq_list1'),
    path('license3/<int:id>/', views.license3, name='license3'),
    path('license4/<int:id>/', views.license4, name='license4'),
    path('license5/<int:id>/', views.license5, name='license5'),
    path('license6/<int:id>/', views.license6, name='license6'),
    path('license7/<int:id>/', views.license7, name='license7'),
    path('jkrq_list2/', views.jkrq_list2, name='jkrq_list2'),
    path('jkrq_log/', views.jkrq_log, name='jkrq_log'),
    path('logcheck_jkrq/<int:list_id>/', views.logcheck_jkrq, name='logcheck_jkrq'),
    path('update_jkrq1/', views.update_jkrq1, name='update_jkrq1'),
    path('add_jkrq1/', views.add_jkrq1, name='add_jkrq1'),
    path('edit_jkrq/', views.edit_jkrq, name='edit_jkrq'),
    path('update_jkrq2/', views.update_jkrq2, name='update_jkrq2'),
    path('add_jkrq2/', views.add_jkrq2, name='add_jkrq2'),
    path('people_change_jkrq/', views.people_change_jkrq, name='people_change_jkrq/'),
    path('logout/', views.logout, name='logout'),
    # path('create_ylc/', views.create_ylc, name='create_ylc'),
    # path('delete_ylc/<int:ylc_id>/', views.delete_ylc, name='delete_ylc'),
    # path('get/', views.get, name='get'),

]

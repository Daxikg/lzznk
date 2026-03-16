"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from app01 import views
from app01.views import InitialView, copy_data1, copy_data2, copy_data3, create_data, create_data1, create_data2, \
    change_password, create_data3

urlpatterns = [
    path('', views.ddd),
    path('1/', views.ddd, name='1'),
    path('wlgl/', views.wlgl, name='wlgl'),

    path('initial/', InitialView.as_view(), name='initial'),
    path('view_log/', views.view_log, name='view_log'),
    path('login/', views.login, name='login'),
    path('register/', views.register),

    path('index/', views.index, name='index'),
    path('index1/', views.index1, name='index1'),
    path('index2/', views.index2, name='index2'),
    path('index3/', views.index3, name='index3'),
    path('index4/', views.index4, name='index4'),
    path('index5/', views.index5, name='index5'),
    path('index6/', views.index6, name='index6'),
    path('index7/', views.index7, name='index7'),
    path('index8/', views.index8, name='index8'),
    path('index9/', views.index9, name='index9'),
    path('index/<int:nid1>/<int:nid2>/edit/', views.user_edit2),
    path('index/<int:nid1>/<int:nid2>/edit3/', views.user_edit3),
    path('index/<int:nid1>/<int:nid2>/edit4/', views.user_edit4),
    path('index/<int:nid1>/<int:nid2>/delete/', views.user_delete2),
    path('架车班信息采集界面1/', views.user_add1, name='user_add1'),
    path('架车班信息采集界面2/', views.user_add2, name='user_add2'),
    path('架车班信息采集界面3/', views.user_add3, name='user_add3'),
    path('架车班信息采集界面4/', views.user_add4, name='user_add4'),
    path('架车班信息采集界面5/', views.user_add5, name='user_add5'),
    path('架车班信息采集界面6/', views.user_add6, name='user_add6'),
    path('架车班信息采集界面7/', views.user_add16, name='user_add16'),
    path('架车班信息手持机采集界面/', views.user_add14, name='user_add14'),
    path('架车班信息采集界面/<int:nid1>/<int:nid2>/edit/', views.user_edit, name='user_edit'),
    path('架车班信息采集界面/<int:nid1>/<int:nid2>/edit0/', views.user_edit0, name='user_edit0'),
    path('架车班信息采集界面/<int:nid1>/<int:nid2>/delete/', views.user_delete),
    path('架车班信息查看界面1/', views.user_list1, name='user_list1'),
    path('架车班信息查看界面2/', views.user_list2, name='user_list2'),
    path('架车班信息查看界面3/', views.user_list3, name='user_list3'),
    path('架车班信息手持机查看界面1/', views.user_list4, name='user_list4'),
    path('架车班信息手持机查看界面2/', views.user_list5, name='user_list5'),
    path('架车班信息手持机查看界面3/', views.user_list6, name='user_list6'),
    path('架车班信息手持机查看界面4/', views.user_list7, name='user_list7'),
    path('架车班信息手持机查看界面5/', views.user_list8, name='user_list8'),
    path('架车班信息手持机查看界面6/', views.user_list9, name='user_list9'),
    path('架车班信息手持机查看界面7/', views.user_list20, name='user_list20'),
    path('出车顺序/', views.shunxu, name='shunxu'),
    path('出车顺序1/', views.shunxu1, name='shunxu1'),
    path('出车顺序2/', views.shunxu2, name='shunxu2'),
    path('出车顺序3/', views.shunxu3, name='shunxu3'),
    path('轮轴班信息采集界面1/', views.user_add7, name='user_add7'),
    path('轮轴班信息采集界面2/', views.user_add8, name='user_add8'),
    path('轮轴班信息采集界面3/', views.user_add9, name='user_add9'),
    path('轮轴班信息采集界面4/', views.user_add10, name='user_add10'),
    path('轮轴班信息采集界面5/', views.user_add11, name='user_add11'),
    path('轮轴班信息采集界面6/', views.user_add12, name='user_add12'),
    path('轮轴班信息采集界面7/', views.user_add13, name='user_add13'),
    path('轮轴班信息采集界面8/', views.user_add15, name='user_add15'),
    path('台车班顺序编辑1/', views.user_list10, name='user_list10'),
    path('台车班顺序编辑2/', views.user_list11, name='user_list11'),
    path('台车班顺序编辑3/', views.user_list12, name='user_list12'),

    path('轮轴班一次出库信息展示界面/', views.user_list13, name='user_list13'),
    path('轮轴班二次出库信息展示界面/', views.user_list14, name='user_list14'),
    path('轮轴班三次出库信息展示界面/', views.user_list19, name='user_list19'),
    path('轮轴班临修信息展示界面/', views.user_list15, name='user_list15'),
    path('台车班一次出库信息展示界面/', views.user_list16, name='user_list16'),
    path('台车班二次出库信息展示界面/', views.user_list17, name='user_list17'),
    path('台车班三次出库信息展示界面/', views.user_list18, name='user_list18'),

    path('copy_data', copy_data1, name='copy_data1'),
    path('copy_data2', copy_data2, name='copy_data2'),
    path('copy_data3', copy_data3, name='copy_data3'),
    path('create-data/', create_data, name='create-data'),
    path('create-data1/', create_data1, name='create-data1'),
    path('create-data2/', create_data2, name='create-data2'),
    path('create-data3/', create_data3, name='create-data3'),

    path('login1/', views.login1, name='login1'),
    path('change_password/', change_password, name='change_password'),
    path('register1/', views.register1),
    path('procedures/', views.procedures, name='procedures'),
    path('transactions/<int:year>/<int:month>/', views.transactions, name='transactions'),
    path('transaction/delete/<int:id>/', views.delete_transaction, ),
    path('transaction/edit/<int:id>/', views.edit_transaction, name='edit_transaction'),
    path('transaction/add/', views.add_transaction, name='add_transaction'),
    path('transaction/<int:id>/', views.transaction_detail, name='transaction_detail'),

    path('upload_files/', views.upload_files, name='upload_files'),
    path('create_folder/', views.create_folder, name='create_folder'),
    path('rename_item/', views.rename_item, name='rename_item'),
    path('delete_files/', views.delete_files, name='delete_files'),

    path('files/', views.file_explorer, name='file_explorer_root'),
    path('files/<path:rel_path>/', views.file_explorer, name='file_explorer'),
    path('preview/<path:rel_path>/', views.preview_pdf, name='pdf_preview'),
    path('video/<path:rel_path>/', views.preview_video, name='video_preview'),
    path('api/search_manual/', views.search_manual, name='search_manual'),
    path('api/search_manual_web/', views.search_manual_web, name='search_manual_web'),

    path('tianshu/', views.shijian, name='shijian'),
    path('jihua/', views.jihua, name='jihua'),
    path('jihua1/', views.jihua1, name='jihua1'),
    path('shiwu/', views.shiwu, name='shiwu'),
    path('get_and_save_data/', views.get_and_save_data),

    path('ckeditor/', include('ckeditor_uploader.urls')),

    path("cjgj/", include('cjgj.urls', namespace='cjgj')),
    path("djgl/", include('djgl.urls', namespace='djgl')),
    path("bzrz/", include('bzrz.urls', namespace='bzrz')),
    path("jkrq/", include('jkrq.urls', namespace='jkrq')),
    path("xfgl/", include('xfgl.urls', namespace='xfgl')),
    path("ldlcsl/", include('ldlcsl.urls', namespace='ldlcsl')),
    path("meeting/", include('meeting.urls', namespace='meeting')),
    path('wjcy/', include('wjcy.urls', namespace='wjcy')),
    path('gfcx/', include('gfcx.urls', namespace='gfcx')),
    path('aqts/', include('aqts.urls', namespace='aqts')),
    path('tools/', include('tools.urls', namespace='tools')),
    path('workshop/', include('workshop.urls', namespace='workshop')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


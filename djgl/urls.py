from django.urls import path

from djgl import views

app_name = 'djgl'

urlpatterns = [
    path('djgl_login/', views.djgl_login, name='djgl_login'),
    path('djgl_register/', views.djgl_register, name='djgl_register'),
    path('search_results/', views.search, name='search_results'),
    path('get_dangyuan_info/<int:dangyuan_id>/', views.get_dangyuan_info, name='get_dangyuan_info'),
    path('dangjianguanli/<int:banzu>/', views.dangjianguanli, name='dangjianguanli'),
    path('dangyuanjifen_ajax/', views.dangyuanjifen_ajax, name='dangyuanjifen_ajax'),
    path('dangyuancgjq_ajax/', views.dangyuancgjq_ajax, name='dangyuancgjq_ajax'),
    path('license8/<int:id>/', views.license8, name='license8'),
    path('add_dangyuan/<int:banzu>/', views.add_dangyuan, name='add_dangyuan'),
    path('edit_dangyuan/', views.edit_dangyuan, name='edit_dangyuan'),
    path('dangyuancgjq/<int:banzu>/<int:quarter>/edit/', views.dangyuancgjq_edit, name='dangyuancgjq_edit'),
    path('dangjianguanli1/<int:banzu>/<int:month>/edit/', views.dangyuanjifen_edit, name='dangjianguanli1_edit'),
    path('dangjianguanli0/', views.dangjianguanli0, name='dangjianguanli0'),
    path('six_area_partial_ajax/', views.six_area_partial_ajax, name='six_area_partial_ajax'),
    path('siyou_anquan_partial_ajax/', views.siyou_anquan_partial_ajax, name='siyou_anquan_partial_ajax'),
    path('dangjianguanli0/<int:quarter>/edit/', views.dangjianguanli0_edit, name='dangjianguanli0_edit'),
    path('dangjiantext_edit/<int:banzu>/edit/', views.dangjiantext_edit, name='dangjiantext_edit'),
]

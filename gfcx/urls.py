from django.urls import path
from . import views

app_name = 'gfcx'

urlpatterns = [
    path('', views.gfcx_login, name='gfcx_login'),
    path('gfcx_login/', views.gfcx_login, name='gfcx_login'),
    path('register_gfcx/', views.register_gfcx, name='register_gfcx'),
    path('gfcx_score/', views.gfcx_score, name='gfcx_score'),
    path('gfcx_score_verification/', views.gfcx_score_verification, name='score_verification'),
    path('gfcx_accounting/', views.gfcx_accounting, name='gfcx_accounting'),
    path('gfcx_accounting_results/', views.gfcx_accounting_results, name='gfcx_accounting_results'),

    path('import_excel_score/', views.import_excel_score, name='import_excel_score'),
    path('import_excel_accounting/', views.import_excel_accounting, name='import_excel_accounting'),
]

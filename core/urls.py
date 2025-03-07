from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('import/', views.import_data, name='import_data'),
    path('citizens/', views.citizens, name='citizens'),
    path('citizen/<int:citizen_id>/', views.citizen_detail, name='citizen_detail'),
    path('add_service/', views.add_service, name='add_service'),
    path('add_relationship/', views.add_relationship, name='add_relationship'),
    path('apply_service/', views.apply_service, name='apply_service'),
    path('approve_applications/', views.approve_applications, name='approve_applications'),
    path('reports/', views.reports, name='reports'),
    path('citizen_login/', views.citizen_login, name='citizen_login'),
    path('citizen_dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('export_citizens/', views.export_citizens, name='export_citizens'),
    path('system_health/', views.system_health, name='system_health'),
]

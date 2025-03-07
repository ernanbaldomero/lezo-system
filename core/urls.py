"""
URL routing for core app.
Includes all feature routes.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('import/', views.import_data, name='import_data'),
    path('citizens/', views.citizens, name='citizens'),
    path('api/add_service/', views.add_service, name='add_service'),
    path('api/add_relationship/', views.add_relationship, name='add_relationship'),
    path('apply_service/', views.apply_service, name='apply_service'),
    path('approve_applications/', views.approve_applications, name='approve_applications'),
    path('reports/', views.reports, name='reports'),
]

"""
URL routing for core app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('setup/', views.setup, name='setup'),
    path('citizens/', views.citizens, name='citizens'),
    path('api/add_service/', views.add_service, name='add_service'),
    path('api/add_relationship/', views.add_relationship, name='add_relationship'),
]
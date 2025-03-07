"""
Web views for Lezo LGU System.
Excel import optional, login fixed, supporting all URL routes with system health metrics.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
import logging
import psutil

logger = logging.getLogger('core')

def welcome(request):
    if request.user.is_authenticated:
        return render(request, 'core/welcome.html')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in successfully")
            return redirect('welcome')
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')

@login_required
def import_data(request):
    if request.method == 'POST' and 'excel_file' in request.FILES:
        # Optional Excel import (placeholder; implement if needed)
        logger.info("Excel file upload attempted (optional import not fully implemented)")
        return redirect('welcome')
    return render(request, 'core/import.html')

@login_required
def citizens(request):
    return render(request, 'core/citizens.html')

@login_required
def add_service(request):
    return render(request, 'core/add_service.html')

@login_required
def add_relationship(request):
    return render(request, 'core/add_relationship.html')

@login_required
def apply_service(request):
    return render(request, 'core/apply_service.html')

@login_required
def approve_applications(request):
    return render(request, 'core/approve_applications.html')

@login_required
def reports(request):
    return render(request, 'core/reports.html')

def citizen_login(request):
    if request.method == 'POST':
        # Placeholder for citizen login logic
        logger.info("Citizen login attempted")
        return redirect('citizen_dashboard')
    return render(request, 'core/citizen_login.html')

@login_required
def citizen_dashboard(request):
    return render(request, 'core/citizen_dashboard.html')

@login_required
def export_citizens(request):
    return render(request, 'core/export_citizens.html')

@login_required
def system_health(request):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    context = {
        'cpu_usage': cpu_usage,
        'memory_total': memory.total / (1024 * 1024),  # Convert to MB
        'memory_used': memory.used / (1024 * 1024),    # Convert to MB
        'memory_percent': memory.percent,
    }
    return render(request, 'core/system_health.html', context)

"""
Web views for Lezo LGU System.
Excel import made optional, login functionality simplified.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.core.files.storage import FileSystemStorage
import logging
from io import StringIO

logger = logging.getLogger('core')

def welcome(request):
    if request.user.is_authenticated:
        return render(request, 'core/welcome.html')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('welcome')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')

@login_required
def import_data(request):
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        if not excel_file.name.endswith('.xlsx'):
            logger.error(f"Invalid file type uploaded: {excel_file.name}")
            return render(request, 'core/import.html', {'error': 'Please upload an .xlsx file'})
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        logger.info(f"Excel file {filename} uploaded successfully (optional import not implemented)")
        fs.delete(filename)  # Placeholder; implement import logic if needed
        return redirect('welcome')
    return render(request, 'core/import.html')

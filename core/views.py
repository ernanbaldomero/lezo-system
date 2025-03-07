from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.forms import ModelForm
from django.http import HttpResponse
import logging
import psutil
import pandas as pd
import openpyxl
from .models import Citizen, Service, Relationship, AuditLog

logger = logging.getLogger('core')

BARANGAYS = [
    "Agcawilan", "Bagto", "Bugasongan", "Carugdog", "Cogon", "Ibao", "Mina",
    "Poblacion", "Silakat Nonok", "Sta. Cruz", "Sta. Cruz Biga-a", "Tayhawan"
]

class CitizenForm(ModelForm):
    class Meta:
        model = Citizen
        fields = [
            'no', 'last_name', 'first_name', 'middle_name', 'suffix', 'address',
            'precinct', 'legend', 'sex', 'birthday', 'place_of_birth',
            'civil_status', 'tin', 'philhealth_no', 'barangay'
        ]

    def clean_tin(self):
        tin = self.cleaned_data['tin']
        if tin and Citizen.objects.filter(tin=tin).exclude(id=self.instance.id).exists():
            raise ValidationError("TIN must be unique")
        return tin

    def clean_philhealth_no(self):
        philhealth_no = self.cleaned_data['philhealth_no']
        if philhealth_no and Citizen.objects.filter(philhealth_no=philhealth_no).exclude(id=self.instance.id).exists():
            raise ValidationError("PhilHealth No must be unique")
        return philhealth_no

class ServiceForm(ModelForm):
    class Meta:
        model = Service
        fields = ['citizen', 'barangay', 'assistance_type', 'recipient_name', 'amount', 'status', 'remarks']

class RelationshipForm(ModelForm):
    class Meta:
        model = Relationship
        fields = ['from_citizen', 'to_citizen', 'relationship_type']

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

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
            messages.success(request, "Logged in successfully")
            return redirect('welcome')
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, "Invalid credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('login')

@login_required
def import_data(request):
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        if not excel_file.name.endswith('.xlsx'):
            messages.error(request, "Please upload an .xlsx file")
            return render(request, 'core/import.html')
        
        try:
            xl = pd.ExcelFile(excel_file)
            citizens_to_create = []
            for sheet_name in xl.sheet_names:
                if sheet_name in BARANGAYS:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    for index, row in df.iterrows():
                        no = row.get('NO')
                        if not pd.isna(no) and not Citizen.objects.filter(no=no, barangay=sheet_name).exists():
                            citizens_to_create.append(Citizen(
                                no=int(no) if not pd.isna(no) else None,
                                last_name=row.get('LAST NAME', 'Unknown'),
                                first_name=row.get('FIRST NAME', 'Unknown'),
                                middle_name=row.get('MIDDLE NAME'),
                                suffix=row.get('SUFFIX'),
                                address=row.get('ADDRESS'),
                                precinct=row.get('PRECINT'),
                                legend=row.get('LEGEND'),
                                sex=row.get('SEX'),
                                birthday=row.get('BIRTHDAY'),
                                place_of_birth=row.get('PLACE OF BIRTH'),
                                civil_status=row.get('CIVIL STATUS'),
                                tin=row.get('TIN'),
                                philhealth_no=row.get('PHILHEALTH NO'),
                                barangay=sheet_name
                            ))
            if citizens_to_create:
                Citizen.objects.bulk_create(citizens_to_create)
                imported_count = len(citizens_to_create)
                AuditLog.objects.create(user=request.user, action='CREATE', model_name='Citizen', object_id=0, details=f"Imported {imported_count} citizens")
                logger.info(f"Imported {imported_count} citizens from {excel_file.name}")
                messages.success(request, f"Successfully imported {imported_count} citizens")
            else:
                messages.info(request, "No new citizens to import")
        except Exception as e:
            logger.error(f"Error importing {excel_file.name}: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    return render(request, 'core/import.html')

@login_required
def citizens(request):
    query = request.GET.get('q', '')
    citizens_list = Citizen.objects.filter(
        Q(last_name__icontains=query) | Q(first_name__icontains=query)
    ).order_by('last_name', 'first_name')
    paginator = Paginator(citizens_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/citizens.html', {'page_obj': page_obj, 'query': query})

@login_required
def citizen_detail(request, citizen_id):
    citizen = get_object_or_404(Citizen, id=citizen_id)
    relationships_from = citizen.relationships_from.all()
    relationships_to = citizen.relationships_to.all()
    services = citizen.services.all()
    if request.method == 'POST' and request.user.is_superuser:
        form = CitizenForm(request.POST, instance=citizen)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(user=request.user, action='UPDATE', model_name='Citizen', object_id=citizen.id, details="Updated citizen details")
            messages.success(request, f"Citizen {citizen} updated")
            return redirect('citizens')
    else:
        form = CitizenForm(instance=citizen)
    return render(request, 'core/citizen_detail.html', {
        'citizen': citizen,
        'form': form,
        'relationships_from': relationships_from,
        'relationships_to': relationships_to,
        'services': services
    })

@admin_required
def add_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            AuditLog.objects.create(user=request.user, action='CREATE', model_name='Service', object_id=service.id, details=f"Added {service}")
            messages.success(request, f"Service {service} added")
            return redirect('citizens')
    else:
        form = ServiceForm()
    return render(request, 'core/add_service.html', {'form': form})

@admin_required
def add_relationship(request):
    if request.method == 'POST':
        form = RelationshipForm(request.POST)
        if form.is_valid():
            relationship = form.save(commit=False)
            relationship.clean()  # Validate no self-relationship
            relationship.save()
            AuditLog.objects.create(user=request.user, action='CREATE', model_name='Relationship', object_id=relationship.id, details=f"Added {relationship}")
            messages.success(request, f"Relationship {relationship} added")
            return redirect('citizens')
    else:
        form = RelationshipForm()
    return render(request, 'core/add_relationship.html', {'form': form})

@login_required
def apply_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.status = 'Pending'
            service.save()
            messages.success(request, "Service application submitted")
            return redirect('citizen_dashboard')
    else:
        form = ServiceForm(initial={'citizen': request.user.citizen if hasattr(request.user, 'citizen') else None})
    return render(request, 'core/apply_service.html', {'form': form})

@admin_required
def approve_applications(request):
    services = Service.objects.filter(status='Pending')
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        status = request.POST.get('status')
        service = get_object_or_404(Service, id=service_id)
        service.status = status
        service.save()
        AuditLog.objects.create(user=request.user, action='UPDATE', model_name='Service', object_id=service.id, details=f"Status changed to {status}")
        messages.success(request, f"Service {service} status updated to {status}")
    return render(request, 'core/approve_applications.html', {'services': services})

@login_required
def reports(request):
    citizens_by_barangay = Citizen.objects.values('barangay').annotate(count=Count('id'))
    services_by_type = Service.objects.values('assistance_type').annotate(count=Count('id'))
    return render(request, 'core/reports.html', {
        'citizens_by_barangay': citizens_by_barangay,
        'services_by_type': services_by_type
    })

def citizen_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Could be voter_id
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully")
            return redirect('citizen_dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'core/citizen_login.html')

@login_required
def citizen_dashboard(request):
    citizen = Citizen.objects.filter(no=request.user.username).first()  # Assuming username is voter_id
    services = citizen.services.all() if citizen else []
    return render(request, 'core/citizen_dashboard.html', {'citizen': citizen, 'services': services})

@login_required
def export_citizens(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Citizens"
    ws.append(['NO', 'Last Name', 'First Name', 'Middle Name', 'Suffix', 'Address', 'Precinct', 'Sex', 'Birthday', 'Barangay'])
    for citizen in Citizen.objects.all():
        ws.append([
            citizen.no, citizen.last_name, citizen.first_name, citizen.middle_name, citizen.suffix,
            citizen.address, citizen.precinct, citizen.sex, citizen.birthday, citizen.barangay
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=citizens.xlsx'
    wb.save(response)
    AuditLog.objects.create(user=request.user, action='EXPORT', model_name='Citizen', object_id=0, details="Exported citizens list")
    return response

@login_required
def system_health(request):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    context = {
        'cpu_usage': cpu_usage,
        'memory_total': memory.total / (1024 * 1024),
        'memory_used': memory.used / (1024 * 1024),
        'memory_percent': memory.percent,
    }
    return render(request, 'core/system_health.html', context)

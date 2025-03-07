"""
Web views for Lezo LGU System.
Includes all features: auth, genealogy, services, reports, setup, password change, and new integrations.
"""

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.management import call_command
from django.contrib.auth import update_session_auth_hash, login
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date
import pandas as pd
import logging
import csv
import psutil
from io import StringIO
from .models import Citizen, Service, Transaction, Relationship, UserProfile, ServiceApplication, CitizenUser
from .utils import get_relationships, send_sms

logger = logging.getLogger('core')

def is_admin(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == 'admin'

def is_staff_or_admin(user):
    return hasattr(user, 'userprofile') and user.userprofile.role in ['staff', 'admin']

def mfa_login_callback(request, user):
    login(request, user)
    return redirect('welcome')

def welcome(request):
    # First-time setup: Check if any superusers exist
    if not User.objects.filter(is_superuser=True).exists():
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email', '')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if password != password_confirm:
                return render(request, 'core/setup.html', {'error': 'Passwords do not match'})
            
            if not username or not password:
                return render(request, 'core/setup.html', {'error': 'Username and password are required'})

            try:
                output = StringIO()
                call_command('createsuperuser', username=username, email=email, password=password, interactive=False, stdout=output)
                logger.info(f"Superuser '{username}' created successfully: {output.getvalue()}")
                return redirect('login')
            except Exception as e:
                logger.error(f"Error creating superuser: {e}")
                return render(request, 'core/setup.html', {'error': str(e)})
        
        return render(request, 'core/setup.html')
    
    # Normal flow for authenticated users
    if not request.user.is_authenticated:
        return redirect('login')

    # Superuser first login password change prompt
    if request.user.is_superuser and request.user.last_login is None and 'password_changed' not in request.session:
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'change':
                old_password = request.POST.get('old_password')
                new_password = request.POST.get('new_password')
                new_password_confirm = request.POST.get('new_password_confirm')

                if not request.user.check_password(old_password):
                    return render(request, 'core/change_password.html', {'error': 'Incorrect old password'})
                if new_password != new_password_confirm:
                    return render(request, 'core/change_password.html', {'error': 'New passwords do not match'})
                if not new_password:
                    return render(request, 'core/change_password.html', {'error': 'New password is required'})

                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                request.session['password_changed'] = True
                logger.info(f"Superuser '{request.user.username}' changed password successfully")
                return redirect('welcome')
            elif action == 'skip':
                request.session['password_changed'] = True
                logger.info(f"Superuser '{request.user.username}' skipped password change")
                return redirect('welcome')
        
        return render(request, 'core/change_password.html')

    # Role-based dashboard customization
    context = {}
    if is_admin(request.user):
        context['total_citizens'] = Citizen.objects.count()
    elif is_staff_or_admin(request.user):
        context['pending_applications'] = ServiceApplication.objects.filter(status='pending').count()
    else:
        context['citizen_count'] = Citizen.objects.count()
    return render(request, 'core/welcome.html', context)

@login_required
@user_passes_test(is_admin)
def import_data(request):
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                logger.error(f"Invalid file type uploaded: {excel_file.name}")
                return render(request, 'core/import.html', {'error': 'Please upload an .xlsx file'})
            fs = FileSystemStorage()
            filename = fs.save(excel_file.name, excel_file)
            file_path = fs.path(filename)
            try:
                logger.info(f"Processing uploaded file: {filename}")
                xls = pd.ExcelFile(file_path)
                expected_sheets = {'Agcawilan', 'Bagto', 'Bugasongan', 'Carugdog', 'Cogon', 
                                  'Ibao', 'Mina', 'Poblacion', 'Silakat Nonok', 'Sta. Cruz', 
                                  'Sta. Cruz Biga-a', 'Tayhawan'}
                if set(xls.sheet_names) != expected_sheets:
                    logger.error(f"Invalid sheet names in {filename}")
                    fs.delete(filename)
                    return render(request, 'core/import.html', {'error': 'Excel file must have 12 specific barangay sheets'})
                
                # Handle import or update based on action
                action = request.POST.get('action', 'import')
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    barangay = sheet_name
                    citizens_to_create = []
                    for index, row in df.iterrows():
                        try:
                            last_name = str(row['LAST NAME']).strip()
                            first_name = str(row['FIRST NAME']).strip()
                            tin = str(row['TIN']).strip() if 'TIN' in row and pd.notnull(row['TIN']) else None
                            philhealth_no = str(row['PHILHEALTH NO']).strip() if 'PHILHEALTH NO' in row and pd.notnull(row['PHILHEALTH NO']) else None

                            if action == 'update' and (tin or philhealth_no):
                                citizen = Citizen.objects.filter(tin=tin).first() or Citizen.objects.filter(philhealth_no=philhealth_no).first()
                                if citizen:
                                    citizen.status = str(row.get('STATUS', citizen.status)).lower()
                                    citizen.address = str(row.get('ADDRESS', citizen.address))
                                    citizen.email = str(row.get('EMAIL', citizen.email)) if 'EMAIL' in row else citizen.email
                                    citizen.save()
                                    logger.info(f"Updated citizen {citizen.id} from {barangay}")
                                    continue

                            middle_name = str(row['MIDDLE NAME']).strip() if 'MIDDLE NAME' in row and pd.notnull(row['MIDDLE NAME']) else None
                            suffix = str(row['SUFFIX']).strip() if 'SUFFIX' in row and pd.notnull(row['SUFFIX']) else None
                            address = str(row['ADDRESS']).strip() if 'ADDRESS' in row and pd.notnull(row['ADDRESS']) else None
                            precinct = str(row['PRECINCT']).strip()
                            legend = str(row['LEGEND']).strip() if 'LEGEND' in row and pd.notnull(row['LEGEND']) else None
                            sex = str(row['SEX']).strip() if 'SEX' in row and pd.notnull(row['SEX']) and row['SEX'] in ['M', 'F'] else None
                            birthday = pd.to_datetime(row.get('BIRTHDAY'), errors='coerce') if 'BIRTHDAY' in row and pd.notnull(row['BIRTHDAY']) else None
                            place_of_birth = str(row['PLACE OF BIRTH']).strip() if 'PLACE OF BIRTH' in row and pd.notnull(row['PLACE OF BIRTH']) else None
                            civil_status = str(row['CIVIL STATUS']).strip().lower() if 'CIVIL STATUS' in row and pd.notnull(row['CIVIL STATUS']) else None
                            email = str(row.get('EMAIL', '')).strip() if 'EMAIL' in row else None
                            status = str(row['STATUS']).strip().lower() if 'STATUS' in row and pd.notnull(row['STATUS']) else 'active'

                            if birthday:
                                exists = Citizen.objects.filter(last_name=last_name, first_name=first_name, birthday=birthday).exists()
                            else:
                                exists = Citizen.objects.filter(last_name=last_name, first_name=first_name).exists()

                            if not exists:
                                citizens_to_create.append(Citizen(
                                    last_name=last_name,
                                    first_name=first_name,
                                    middle_name=middle_name,
                                    suffix=suffix,
                                    address=address,
                                    precinct=precinct,
                                    legend=legend,
                                    sex=sex,
                                    birthday=birthday,
                                    place_of_birth=place_of_birth,
                                    civil_status=civil_status,
                                    tin=tin,
                                    philhealth_no=philhealth_no,
                                    email=email,
                                    status=status,
                                    barangay=barangay
                                ))
                        except Exception as e:
                            logger.error(f"Error processing row {index} in {sheet_name}: {e}")
                            continue
                    if action == 'import':
                        Citizen.objects.bulk_create(citizens_to_create)
                        logger.info(f"Imported {len(citizens_to_create)} citizens from {barangay}")
                fs.delete(filename)
                logger.info(f"File {action} completed successfully")
                return redirect('citizens')
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
                fs.delete(filename)
                return render(request, 'core/import.html', {'error': 'Error processing file'})
    return render(request, 'core/import.html')

@login_required
def citizens(request):
    query = request.GET.get('q', '')
    citizens_list = Citizen.objects.select_related().all()
    if query:
        citizens_list = citizens_list.filter(
            Q(last_name__icontains=query) | Q(first_name__icontains=query)
        )
    if not is_admin(request.user) and hasattr(request.user, 'userprofile') and request.user.userprofile.barangay:
        citizens_list = citizens_list.filter(barangay=request.user.userprofile.barangay)
    paginator = Paginator(citizens_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    citizen_ids = [c.id for c in page_obj]
    relationships = Relationship.objects.filter(citizen__id__in=citizen_ids).select_related('related_citizen')
    rel_dict = {}
    for rel in relationships:
        rel_dict.setdefault(rel.citizen_id, []).append((rel.type, rel.related_citizen))

    for citizen in page_obj:
        citizen.relationships = rel_dict.get(citizen.id, []) + get_relationships(citizen)

    return render(request, 'core/citizens.html', {'page_obj': page_obj, 'query': query})

@login_required
@user_passes_test(is_staff_or_admin)
@api_view(['POST'])
def add_service(request):
    citizen_id = request.data.get('citizen_id')
    service_name = request.data.get('service_name')
    if not citizen_id or not service_name:
        logger.error("Missing citizen_id or service_name in add_service request")
        return Response({'error': 'Missing citizen_id or service_name'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        citizen = Citizen.objects.get(id=citizen_id)
        service, created = Service.objects.get_or_create(
            name=service_name,
            defaults={'description': f"{service_name} service"}
        )
        transaction = Transaction.objects.create(
            citizen=citizen,
            service=service,
            date=date.today()
        )
        logger.info(f"Added service {service_name} to citizen {citizen}")
        return Response({'message': 'Service added successfully'}, status=status.HTTP_201_CREATED)
    except Citizen.DoesNotExist:
        logger.error(f"Citizen ID {citizen_id} not found")
        return Response({'error': 'Citizen not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        return Response({'error': 'Error adding service'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
@user_passes_test(is_staff_or_admin)
@api_view(['POST'])
def add_relationship(request):
    citizen_id = request.data.get('citizen_id')
    related_citizen_id = request.data.get('related_citizen_id')
    relationship_type = request.data.get('relationship_type')
    if not all([citizen_id, related_citizen_id, relationship_type]):
        logger.error("Missing fields in add_relationship request")
        return Response({'error': 'Missing citizen_id, related_citizen_id, or relationship_type'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        citizen = Citizen.objects.get(id=citizen_id)
        related_citizen = Citizen.objects.get(id=related_citizen_id)
        if Relationship.objects.filter(citizen=citizen, related_citizen=related_citizen, type=relationship_type).exists():
            logger.info(f"Relationship {relationship_type} already exists between {citizen} and {related_citizen}")
            return Response({'error': 'Relationship already exists'}, status=status.HTTP_400_BAD_REQUEST)
        relationship = Relationship.objects.create(
            citizen=citizen,
            related_citizen=related_citizen,
            type=relationship_type
        )
        logger.info(f"Added relationship {relationship_type} between {citizen} and {related_citizen}")
        return Response({'message': 'Relationship added successfully'}, status=status.HTTP_201_CREATED)
    except Citizen.DoesNotExist:
        logger.error(f"Citizen ID {citizen_id} or {related_citizen_id} not found")
        return Response({'error': 'Citizen not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error adding relationship: {e}")
        return Response({'error': 'Error adding relationship'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def apply_service(request):
    if request.method == 'POST':
        citizen_id = request.POST.get('citizen_id')
        service_id = request.POST.get('service_id')
        try:
            citizen = Citizen.objects.get(id=citizen_id)
            service = Service.objects.get(id=service_id)
            ServiceApplication.objects.create(citizen=citizen, service=service)
            logger.info(f"Service application created for {citizen} - {service}")
            return redirect('citizens')
        except (Citizen.DoesNotExist, Service.DoesNotExist):
            logger.error(f"Invalid citizen_id {citizen_id} or service_id {service_id}")
            return render(request, 'core/apply_service.html', {'error': 'Invalid citizen or service'})
    services = Service.objects.all()
    citizens = Citizen.objects.all()
    return render(request, 'core/apply_service.html', {'services': services, 'citizens': citizens})

@login_required
@user_passes_test(is_staff_or_admin)
def approve_applications(request):
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
        action = request.POST.get('action')
        try:
            application = ServiceApplication.objects.get(id=application_id)
            if action == 'approve':
                application.status = 'approved'
                application.approved_by = request.user
                application.date_approved = date.today()
                Transaction.objects.create(citizen=application.citizen, service=application.service, date=date.today())
                send_sms(application.citizen, f"Your {application.service.name} application has been approved.")
                if application.citizen.email:
                    send_mail(
                        f'{application.service.name} Application Approved',
                        f'Your application has been approved on {date.today()}.',
                        'from@example.com',
                        [application.citizen.email],
                        fail_silently=True,
                    )
                logger.info(f"Application {application_id} approved by {request.user}")
            elif action == 'reject':
                application.status = 'rejected'
                send_sms(application.citizen, f"Your {application.service.name} application has been rejected.")
                if application.citizen.email:
                    send_mail(
                        f'{application.service.name} Application Rejected',
                        f'Your application has been rejected on {date.today()}.',
                        'from@example.com',
                        [application.citizen.email],
                        fail_silently=True,
                    )
                logger.info(f"Application {application_id} rejected by {request.user}")
            application.save()
            return redirect('approve_applications')
        except ServiceApplication.DoesNotExist:
            logger.error(f"Application ID {application_id} not found")
    applications = ServiceApplication.objects.filter(status='pending')
    return render(request, 'core/approve_applications.html', {'applications': applications})

@login_required
@user_passes_test(is_admin)
def reports(request):
    total_citizens = Citizen.objects.count()
    by_barangay = list(Citizen.objects.values('barangay').annotate(count=Count('id')).order_by('barangay'))
    by_status = list(Citizen.objects.values('status').annotate(count=Count('id')).order_by('status'))
    by_service = list(Transaction.objects.values('service__name').annotate(count=Count('id')).order_by('service__name'))
    by_civil_status = list(Citizen.objects.values('civil_status').annotate(count=Count('id')).order_by('civil_status'))
    by_sex = list(Citizen.objects.values('sex').annotate(count=Count('id')).order_by('sex'))

    context = {
        'total_citizens': total_citizens,
        'by_barangay': by_barangay,
        'by_status': by_status,
        'by_service': by_service,
        'by_civil_status': by_civil_status,
        'by_sex': by_sex,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(context)
    return render(request, 'core/reports.html', context)

def citizen_login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')
        citizen_user = CitizenUser.objects.filter(citizen__tin=identifier).first() or CitizenUser.objects.filter(citizen__philhealth_no=identifier).first()
        if citizen_user and citizen_user.check_password(password):
            request.session['citizen_id'] = citizen_user.citizen.id
            logger.info(f"Citizen {citizen_user.citizen} logged in")
            return redirect('citizen_dashboard')
        logger.error(f"Failed login attempt for identifier {identifier}")
        return render(request, 'core/citizen_login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/citizen_login.html')

def citizen_dashboard(request):
    citizen_id = request.session.get('citizen_id')
    if not citizen_id:
        return redirect('citizen_login')
    citizen = Citizen.objects.get(id=citizen_id)
    applications = ServiceApplication.objects.filter(citizen=citizen)
    transactions = Transaction.objects.filter(citizen=citizen)
    if request.method == 'POST':
        if 'apply_service' in request.POST:
            service_id = request.POST.get('service_id')
            service = Service.objects.get(id=service_id)
            ServiceApplication.objects.create(citizen=citizen, service=service)
            logger.info(f"Citizen {citizen} applied for {service}")
        elif 'update_details' in request.POST:
            citizen.address = request.POST.get('address', citizen.address)
            citizen.email = request.POST.get('email', citizen.email)
            citizen.save()
            logger.info(f"Citizen {citizen} updated details")
        return redirect('citizen_dashboard')
    services = Service.objects.all()
    return render(request, 'core/citizen_dashboard.html', {
        'citizen': citizen,
        'applications': applications,
        'transactions': transactions,
        'services': services,
    })

@login_required
@user_passes_test(is_admin)
def export_citizens(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="citizens.csv"'
    writer = csv.writer(response)
    writer.writerow(['Last Name', 'First Name', 'Barangay', 'Status', 'Email'])
    for citizen in Citizen.objects.all():
        writer.writerow([citizen.last_name, citizen.first_name, citizen.barangay, citizen.status, citizen.email or ''])
    logger.info(f"Citizens exported by {request.user}")
    return response

@login_required
@user_passes_test(is_admin)
def system_health(request):
    health_data = {
        'disk_usage': psutil.disk_usage('/').percent,
        'memory_usage': psutil.virtual_memory().percent,
        'cpu_usage': psutil.cpu_percent(interval=1),
    }
    logger.info(f"System health checked by {request.user}")
    return render(request, 'core/health.html', health_data)

"""
Web views for Lezo LGU System.
Includes all features: auth, genealogy, services, reports.
"""

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date
import pandas as pd
import logging
from .models import Citizen, Service, Transaction, Relationship, UserProfile, ServiceApplication
from .utils import get_relationships, send_sms

logger = logging.getLogger('core')

def is_admin(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == 'admin'

def is_staff_or_admin(user):
    return hasattr(user, 'userprofile') and user.userprofile.role in ['staff', 'admin']

@login_required
def welcome(request):
    return render(request, 'core/welcome.html')

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
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    barangay = sheet_name
                    citizens_to_create = []
                    for index, row in df.iterrows():
                        try:
                            last_name = str(row['LAST NAME']).strip()
                            first_name = str(row['FIRST NAME']).strip()
                            middle_name = str(row['MIDDLE NAME']).strip() if 'MIDDLE NAME' in row and pd.notnull(row['MIDDLE NAME']) else None
                            suffix = str(row['SUFFIX']).strip() if 'SUFFIX' in row and pd.notnull(row['SUFFIX']) else None
                            address = str(row['ADDRESS']).strip() if 'ADDRESS' in row and pd.notnull(row['ADDRESS']) else None
                            precinct = str(row['PRECINCT']).strip()
                            legend = str(row['LEGEND']).strip() if 'LEGEND' in row and pd.notnull(row['LEGEND']) else None
                            sex = str(row['SEX']).strip() if 'SEX' in row and pd.notnull(row['SEX']) and row['SEX'] in ['M', 'F'] else None
                            birthday = pd.to_datetime(row.get('BIRTHDAY'), errors='coerce') if 'BIRTHDAY' in row and pd.notnull(row['BIRTHDAY']) else None
                            place_of_birth = str(row['PLACE OF BIRTH']).strip() if 'PLACE OF BIRTH' in row and pd.notnull(row['PLACE OF BIRTH']) else None
                            civil_status = str(row['CIVIL STATUS']).strip().lower() if 'CIVIL STATUS' in row and pd.notnull(row['CIVIL STATUS']) else None
                            tin = str(row['TIN']).strip() if 'TIN' in row and pd.notnull(row['TIN']) else None
                            philhealth_no = str(row['PHILHEALTH NO']).strip() if 'PHILHEALTH NO' in row and pd.notnull(row['PHILHEALTH NO']) else None
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
                                    status=status,
                                    barangay=barangay
                                ))
                        except Exception as e:
                            logger.error(f"Error processing row {index} in {sheet_name}: {e}")
                            continue
                    Citizen.objects.bulk_create(citizens_to_create)
                    logger.info(f"Imported {len(citizens_to_create)} citizens from {barangay}")
                fs.delete(filename)
                logger.info("File import completed successfully")
                return redirect('citizens')
            except Exception as e:
                logger.error(f"Error importing file {filename}: {e}")
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
                logger.info(f"Application {application_id} approved by {request.user}")
            elif action == 'reject':
                application.status = 'rejected'
                send_sms(application.citizen, f"Your {application.service.name} application has been rejected.")
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
    by_barangay = Citizen.objects.values('barangay').annotate(count=Count('id')).order_by('barangay')
    by_status = Citizen.objects.values('status').annotate(count=Count('id')).order_by('status')
    by_service = Transaction.objects.values('service__name').annotate(count=Count('id')).order_by('service__name')
    by_civil_status = Citizen.objects.values('civil_status').annotate(count=Count('id')).order_by('civil_status')
    by_sex = Citizen.objects.values('sex').annotate(count=Count('id')).order_by('sex')

    context = {
        'total_citizens': total_citizens,
        'by_barangay': by_barangay,
        'by_status': by_status,
        'by_service': by_service,
        'by_civil_status': by_civil_status,
        'by_sex': by_sex,
    }
    return render(request, 'core/reports.html', context)

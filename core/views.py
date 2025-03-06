"""
Web views for Lezo LGU System.
Optimized for performance with efficient queries and minimal memory usage.
"""

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.files.storage import FileSystemStorage
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date
import pandas as pd
import logging
from .models import Citizen, Service, Transaction, Relationship
from .utils import get_relationships

logger = logging.getLogger('core')

def welcome(request):
    """Render the welcome page with links to setup and citizens."""
    return render(request, 'core/welcome.html')

def setup(request):
    """Handle setup page for uploading voters.xlsx or initializing empty database."""
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            if not excel_file.name.endswith('.xlsx'):
                logger.error(f"Invalid file type uploaded: {excel_file.name}")
                return render(request, 'core/setup.html', {'error': 'Please upload an .xlsx file'})
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
                    return render(request, 'core/setup.html', {'error': 'Excel file must have 12 specific barangay sheets'})
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    barangay = sheet_name
                    citizens_to_create = []
                    for index, row in df.iterrows():
                        try:
                            last_name = str(row['LAST NAME']).strip()
                            first_name = str(row['FIRST NAME']).strip()
                            precinct = str(row['PRECINCT']).strip()
                            birthday = pd.to_datetime(row.get('BIRTHDAYS'), errors='coerce') if 'BIRTHDAYS' in row and pd.notnull(row['BIRTHDAYS']) else None
                            middle_name = str(row['MIDDLE NAME']).strip() if 'MIDDLE NAME' in row and pd.notnull(row['MIDDLE NAME']) else None
                            literacy_status = row['LITERACY STATUS'] == 'Yes' if 'LITERACY STATUS' in row and pd.notnull(row['LITERACY STATUS']) else False
                            senior_status = row['SENIOR STATUS'] == 'Yes' if 'SENIOR STATUS' in row and pd.notnull(row['SENIOR STATUS']) else False
                            pwd_status = row['PWD STATUS'] == 'Yes' if 'PWD STATUS' in row and pd.notnull(row['PWD STATUS']) else False

                            # Deduplication check
                            if birthday:
                                exists = Citizen.objects.filter(last_name=last_name, first_name=first_name, birthday=birthday).exists()
                            else:
                                exists = Citizen.objects.filter(last_name=last_name, first_name=first_name).exists()

                            if not exists:
                                citizens_to_create.append(Citizen(
                                    last_name=last_name,
                                    first_name=first_name,
                                    middle_name=middle_name,
                                    precinct=precinct,
                                    barangay=barangay,
                                    birthday=birthday,
                                    literacy_status=literacy_status,
                                    senior_status=senior_status,
                                    pwd_status=pwd_status
                                ))
                        except Exception as e:
                            logger.error(f"Error processing row {index} in {sheet_name}: {e}")
                            continue
                    # Bulk create for performance
                    Citizen.objects.bulk_create(citizens_to_create)
                    logger.info(f"Imported {len(citizens_to_create)} citizens from {barangay}")
                fs.delete(filename)
                logger.info("File import completed successfully")
                return redirect('citizens')
            except Exception as e:
                logger.error(f"Error importing file {filename}: {e}")
                fs.delete(filename)
                return render(request, 'core/setup.html', {'error': 'Error processing file'})
        else:
            logger.info("No file uploaded, initializing with empty database")
            return redirect('citizens')
    return render(request, 'core/setup.html')

def citizens(request):
    """Display list of citizens with search, pagination, and relationships."""
    query = request.GET.get('q', '')
    citizens_list = Citizen.objects.select_related().all()  # Optimized query
    if query:
        citizens_list = citizens_list.filter(
            Q(last_name__icontains=query) | Q(first_name__icontains=query)
        )
    paginator = Paginator(citizens_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preload relationships to avoid N+1 queries
    citizen_ids = [c.id for c in page_obj]
    relationships = Relationship.objects.filter(citizen__id__in=citizen_ids).select_related('related_citizen')
    rel_dict = {}
    for rel in relationships:
        rel_dict.setdefault(rel.citizen_id, []).append((rel.type, rel.related_citizen))

    for citizen in page_obj:
        citizen.relationships = rel_dict.get(citizen.id, []) + get_relationships(citizen)

    return render(request, 'core/citizens.html', {'page_obj': page_obj, 'query': query})

@api_view(['POST'])
def add_service(request):
    """API endpoint to add a service to a citizen."""
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

@api_view(['POST'])
def add_relationship(request):
    """API endpoint to add a relationship between citizens."""
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
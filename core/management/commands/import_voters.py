"""
Management command to import voters from Excel file.
Updated for expanded Citizen fields.
"""

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from core.models import Citizen
import logging

logger = logging.getLogger('core')

class Command(BaseCommand):
    help = 'Imports voters from a 12-tab Excel file into the Citizen model'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the voters.xlsx file')

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        if not excel_file.endswith('.xlsx'):
            logger.error(f"Invalid file type: {excel_file}")
            raise CommandError('File must be an .xlsx file')
        
        try:
            logger.info(f"Starting import from {excel_file}")
            xls = pd.ExcelFile(excel_file)
            expected_sheets = {'Agcawilan', 'Bagto', 'Bugasongan', 'Carugdog', 'Cogon', 
                              'Ibao', 'Mina', 'Poblacion', 'Silakat Nonok', 'Sta. Cruz', 
                              'Sta. Cruz Biga-a', 'Tayhawan'}
            if set(xls.sheet_names) != expected_sheets:
                logger.error(f"Invalid sheet names in {excel_file}")
                raise CommandError('Excel file must have 12 specific barangay sheets')
            
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
                        self.stdout.write(self.style.ERROR(f"Error at row {index} in {sheet_name}: {e}"))
                        continue
                Citizen.objects.bulk_create(citizens_to_create)
                logger.info(f"Imported {len(citizens_to_create)} citizens from {barangay}")
                self.stdout.write(self.style.SUCCESS(f"Imported {len(citizens_to_create)} citizens from {barangay}"))
            logger.info("Import completed successfully")
            self.stdout.write(self.style.SUCCESS('Import completed successfully'))
        except Exception as e:
            logger.error(f"Error importing {excel_file}: {e}")
            raise CommandError(f"Error importing file: {e}")

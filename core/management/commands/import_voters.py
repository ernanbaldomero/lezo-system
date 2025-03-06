"""
Management command to import voters from Excel file.
Optimized with bulk operations for performance.
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
                        self.stdout.write(self.style.ERROR(f"Error at row {index} in {sheet_name}: {e}"))
                        continue
                # Bulk create for performance
                Citizen.objects.bulk_create(citizens_to_create)
                logger.info(f"Imported {len(citizens_to_create)} citizens from {barangay}")
                self.stdout.write(self.style.SUCCESS(f"Imported {len(citizens_to_create)} citizens from {barangay}"))
            logger.info("Import completed successfully")
            self.stdout.write(self.style.SUCCESS('Import completed successfully'))
        except Exception as e:
            logger.error(f"Error importing {excel_file}: {e}")
            raise CommandError(f"Error importing file: {e}")
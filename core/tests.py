"""
Unit tests for Lezo LGU System core app.
Covers all features and updated Citizen model.
"""

from django.test import TestCase
from .models import Citizen, Service, Transaction, Relationship, UserProfile, ServiceApplication
from .utils import get_relationships
from django.contrib.auth.models import User
from datetime import date

class CoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.profile = UserProfile.objects.create(user=self.user, role='admin')
        self.citizen1 = Citizen.objects.create(
            last_name='Doe', first_name='John', precinct='P1', barangay='Poblacion',
            sex='M', civil_status='married', status='active'
        )
        self.citizen2 = Citizen.objects.create(
            last_name='Doe', first_name='Jane', precinct='P1', barangay='Poblacion',
            sex='F', civil_status='single', status='active'
        )
        self.service = Service.objects.create(name='AICS', description='Assistance')

    def test_citizen_creation(self):
        self.assertEqual(self.citizen1.last_name, 'Doe')
        self.assertEqual(self.citizen1.first_name, 'John')
        self.assertEqual(self.citizen1.sex, 'M')
        self.assertEqual(str(self.citizen1), 'John Doe')

    def test_service_creation(self):
        self.assertEqual(self.service.name, 'AICS')
        self.assertEqual(str(self.service), 'AICS')

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            citizen=self.citizen1, service=self.service, date=date.today()
        )
        self.assertEqual(transaction.citizen, self.citizen1)
        self.assertEqual(transaction.service, self.service)
        self.assertEqual(str(transaction), f"John Doe - AICS on {date.today()}")

    def test_relationship_creation(self):
        relationship = Relationship.objects.create(
            citizen=self.citizen1, related_citizen=self.citizen2, type='father'
        )
        self.assertEqual(relationship.citizen, self.citizen1)
        self.assertEqual(relationship.related_citizen, self.citizen2)
        self.assertEqual(relationship.type, 'father')
        self.assertEqual(str(relationship), 'John Doe is father of Jane Doe')

    def test_relationship_inference(self):
        Relationship.objects.create(citizen=self.citizen1, related_citizen=self.citizen2, type='father')
        citizen3 = Citizen.objects.create(
            last_name='Smith', first_name='Bob', precinct='P2', barangay='Poblacion',
            sex='M', civil_status='single', status='active'
        )
        Relationship.objects.create(citizen=citizen3, related_citizen=self.citizen1, type='brother')
        
        relationships = get_relationships(self.citizen2)
        self.assertIn(('uncle', citizen3), relationships)
        
        relationships = get_relationships(citizen3)
        self.assertIn(('nephew', self.citizen2), relationships)

    def test_service_application(self):
        app = ServiceApplication.objects.create(citizen=self.citizen1, service=self.service)
        self.assertEqual(app.status, 'pending')
        self.assertEqual(str(app), 'John Doe - AICS (pending)')

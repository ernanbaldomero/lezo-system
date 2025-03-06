"""
Unit tests for Lezo LGU System core app.
Ensures functionality and performance.
"""

from django.test import TestCase
from .models import Citizen, Service, Transaction, Relationship
from .utils import get_relationships
from datetime import date

class CoreTests(TestCase):
    def setUp(self):
        """Set up test data."""
        self.citizen1 = Citizen.objects.create(
            last_name='Doe', first_name='John', precinct='P1', barangay='Poblacion'
        )
        self.citizen2 = Citizen.objects.create(
            last_name='Doe', first_name='Jane', precinct='P1', barangay='Poblacion'
        )
        self.service = Service.objects.create(name='AICS', description='Assistance')

    def test_citizen_creation(self):
        """Test creating a citizen."""
        self.assertEqual(self.citizen1.last_name, 'Doe')
        self.assertEqual(self.citizen1.first_name, 'John')
        self.assertEqual(str(self.citizen1), 'John Doe')

    def test_service_creation(self):
        """Test creating a service."""
        self.assertEqual(self.service.name, 'AICS')
        self.assertEqual(str(self.service), 'AICS')

    def test_transaction_creation(self):
        """Test creating a transaction."""
        transaction = Transaction.objects.create(
            citizen=self.citizen1, service=self.service, date=date.today()
        )
        self.assertEqual(transaction.citizen, self.citizen1)
        self.assertEqual(transaction.service, self.service)
        self.assertEqual(str(transaction), f"John Doe - AICS on {date.today()}")

    def test_relationship_creation(self):
        """Test creating a direct relationship."""
        relationship = Relationship.objects.create(
            citizen=self.citizen1, related_citizen=self.citizen2, type='brother'
        )
        self.assertEqual(relationship.citizen, self.citizen1)
        self.assertEqual(relationship.related_citizen, self.citizen2)
        self.assertEqual(relationship.type, 'brother')
        self.assertEqual(str(relationship), 'John Doe is brother of Jane Doe')

    def test_relationship_inference(self):
        """Test inferring uncle and nephew relationships."""
        # John is father of Jane
        Relationship.objects.create(citizen=self.citizen1, related_citizen=self.citizen2, type='father')
        # Bob is brother of John
        citizen3 = Citizen.objects.create(last_name='Smith', first_name='Bob', precinct='P2', barangay='Poblacion')
        Relationship.objects.create(citizen=citizen3, related_citizen=self.citizen1, type='brother')
        
        relationships = get_relationships(self.citizen2)  # Jane's perspective
        self.assertIn(('uncle', citizen3), relationships)  # Inferred
        
        relationships = get_relationships(citizen3)  # Bob's perspective
        self.assertIn(('nephew', self.citizen2), relationships)  # Inferred
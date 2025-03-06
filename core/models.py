"""
Database models for Lezo LGU System.
Optimized with indexes for query performance.
"""

from django.db import models

class Citizen(models.Model):
    """Model representing a citizen."""
    last_name = models.CharField(max_length=100, db_index=True)  # Indexed for search
    first_name = models.CharField(max_length=100, db_index=True)  # Indexed for search
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    precinct = models.CharField(max_length=50)
    barangay = models.CharField(max_length=50, db_index=True)  # Indexed for filtering
    birthday = models.DateField(blank=True, null=True)
    literacy_status = models.BooleanField(default=False)
    senior_status = models.BooleanField(default=False)
    pwd_status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=['last_name', 'first_name', 'birthday']),  # For deduplication
        ]

class Service(models.Model):
    """Model representing a service provided to citizens."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Transaction(models.Model):
    """Model representing a service transaction for a citizen."""
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.citizen} - {self.service} on {self.date}"

    class Meta:
        indexes = [
            models.Index(fields=['citizen', 'date']),  # For efficient querying
        ]

class Relationship(models.Model):
    """Model representing relationships between citizens."""
    citizen = models.ForeignKey(Citizen, related_name='relationships', on_delete=models.CASCADE)
    related_citizen = models.ForeignKey(Citizen, related_name='related_relationships', on_delete=models.CASCADE)
    type = models.CharField(max_length=50)

    class Meta:
        unique_together = ('citizen', 'related_citizen', 'type')
        indexes = [
            models.Index(fields=['citizen', 'type']),  # For relationship queries
        ]

    def __str__(self):
        return f"{self.citizen} is {self.type} of {self.related_citizen}"
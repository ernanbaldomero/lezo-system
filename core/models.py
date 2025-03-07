"""
Database models for Lezo LGU System.
Includes expanded Citizen fields, CitizenUser, and all required models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('viewer', 'Viewer'),
    ], default='viewer')
    barangay = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Citizen(models.Model):
    last_name = models.CharField(max_length=100, db_index=True)
    first_name = models.CharField(max_length=100, db_index=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    suffix = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    precinct = models.CharField(max_length=50)
    legend = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')], blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)
    civil_status = models.CharField(max_length=20, choices=[
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('divorced', 'Divorced'),
    ], blank=True, null=True)
    tin = models.CharField(max_length=20, blank=True, null=True)
    philhealth_no = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)  # Added for email notifications
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('dead', 'Dead'),
        ('bedridden', 'Bedridden'),
        ('moved', 'Moved'),
    ], default='active')
    barangay = models.CharField(max_length=50, db_index=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=['last_name', 'first_name', 'birthday']),
            models.Index(fields=['barangay', 'status']),
        ]

class CitizenUser(models.Model):
    citizen = models.OneToOneField(Citizen, on_delete=models.CASCADE)
    password = models.CharField(max_length=128)  # Hashed password

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.citizen.first_name} {self.citizen.last_name}"

class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class Transaction(models.Model):
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.citizen} - {self.service} on {self.date}"

    class Meta:
        indexes = [
            models.Index(fields=['citizen', 'date']),
        ]

class Relationship(models.Model):
    citizen = models.ForeignKey(Citizen, related_name='relationships', on_delete=models.CASCADE)
    related_citizen = models.ForeignKey(Citizen, related_name='related_relationships', on_delete=models.CASCADE)
    type = models.CharField(max_length=50)

    class Meta:
        unique_together = ('citizen', 'related_citizen', 'type')
        indexes = [
            models.Index(fields=['citizen', 'type']),
        ]

    def __str__(self):
        return f"{self.citizen} is {self.type} of {self.related_citizen}"

class ServiceApplication(models.Model):
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    date_applied = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_approved = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.citizen} - {self.service} ({self.status})"

    class Meta:
        indexes = [
            models.Index(fields=['status', 'date_applied']),
        ]

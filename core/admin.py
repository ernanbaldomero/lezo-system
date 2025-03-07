"""
Admin configuration for core app.
Updated for all models and fields.
"""

from django.contrib import admin
from .models import Citizen, Service, Transaction, Relationship, UserProfile, ServiceApplication

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'barangay', 'precinct', 'status')
    search_fields = ('last_name', 'first_name', 'tin', 'philhealth_no')
    list_filter = ('barangay', 'status', 'sex', 'civil_status')
    list_per_page = 20

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('citizen', 'service', 'date')
    list_filter = ('date',)

@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('citizen', 'related_citizen', 'type')
    list_filter = ('type',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'barangay')
    list_filter = ('role', 'barangay')

@admin.register(ServiceApplication)
class ServiceApplicationAdmin(admin.ModelAdmin):
    list_display = ('citizen', 'service', 'status', 'date_applied')
    list_filter = ('status', 'date_applied')

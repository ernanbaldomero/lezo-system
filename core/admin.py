"""
Admin configuration for core app.
Updated for all models and fields.
"""

from django.contrib import admin
from .models import Citizen, Service, Transaction, Relationship, UserProfile, ServiceApplication, AuditLog

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'barangay', 'precinct', 'status')
    search_fields = ('last_name', 'first_name', 'tin', 'philhealth_no')
    list_filter = ('barangay', 'status', 'sex', 'civil_status')
    list_per_page = 20

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'assistance_type', 'recipient_name', 'status')
    search_fields = ('name', 'recipient_name', 'assistance_type')
    list_filter = ('assistance_type', 'status')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('citizen', 'service', 'date', 'amount')
    search_fields = ('citizen__last_name', 'citizen__first_name', 'service__name')
    list_filter = ('date',)

@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    # Adjusted field names to match model
    list_display = ('from_citizen', 'to_citizen', 'relationship_type')
    search_fields = ('from_citizen__last_name', 'to_citizen__last_name')
    list_filter = ('relationship_type',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'barangay')
    search_fields = ('user__username', 'role')
    list_filter = ('role', 'barangay')

@admin.register(ServiceApplication)
class ServiceApplicationAdmin(admin.ModelAdmin):
    list_display = ('citizen', 'service', 'status', 'date_applied')
    search_fields = ('citizen__last_name', 'citizen__first_name', 'service__name')
    list_filter = ('status', 'date_applied')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    search_fields = ('user__username', 'model_name', 'details')
    list_filter = ('action', 'timestamp')

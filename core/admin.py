"""
Admin configuration for core app.
Optimized for efficient admin interface.
"""

from django.contrib import admin
from .models import Citizen, Service, Transaction, Relationship

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'barangay', 'precinct')
    search_fields = ('last_name', 'first_name')
    list_per_page = 20  # Reduced for performance

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
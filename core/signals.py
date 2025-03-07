"""
Signal handlers for audit logging.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Citizen, ServiceApplication, Transaction
import logging

logger = logging.getLogger('core')

@receiver(post_save, sender=Citizen)
def log_citizen_update(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    user = getattr(instance, '_meta.user', 'unknown') if hasattr(instance, '_meta.user') else 'system'
    logger.info(f"Citizen {instance.id} {action} by {user}")

@receiver(post_save, sender=ServiceApplication)
def log_application_update(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    user = instance.approved_by.username if instance.approved_by else 'unknown'
    logger.info(f"ServiceApplication {instance.id} {action} by {user}")

@receiver(post_save, sender=Transaction)
def log_transaction_update(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Transaction {instance.id} created for {instance.citizen} by system")

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Citizen(models.Model):
    no = models.IntegerField(null=True, blank=True, unique=True)
    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    suffix = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    precinct = models.CharField(max_length=50, blank=True, null=True)
    legend = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=10, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)
    civil_status = models.CharField(max_length=50, blank=True, null=True)
    tin = models.CharField(max_length=50, blank=True, null=True, unique=True)
    philhealth_no = models.CharField(max_length=50, blank=True, null=True, unique=True)
    barangay = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    # Added 'status' field to match CitizenAdmin.list_display
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.barangay})"

    class Meta:
        verbose_name = "Citizen"
        verbose_name_plural = "Citizens"

class Service(models.Model):
    ASSISTANCE_TYPES = (
        ('Medical', 'Medical'),
        ('Burial', 'Burial'),
        ('Educational', 'Educational'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='services')
    barangay = models.CharField(max_length=100)
    assistance_type = models.CharField(max_length=50, choices=ASSISTANCE_TYPES)
    recipient_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Added fields to match ServiceAdmin.list_display
    name = models.CharField(max_length=100, default='Assistance')  # Placeholder for display
    description = models.TextField(default='Service assistance')

    def __str__(self):
        return f"{self.assistance_type} for {self.recipient_name} ({self.barangay})"

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

class Relationship(models.Model):
    RELATIONSHIP_TYPES = (
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Son', 'Son'),
        ('Daughter', 'Daughter'),
        ('Brother', 'Brother'),
        ('Sister', 'Sister'),
        ('Spouse', 'Spouse'),
        ('Grandparent', 'Grandparent'),
        ('Grandchild', 'Grandchild'),
        ('Uncle', 'Uncle'),
        ('Aunt', 'Aunt'),
        ('Nephew', 'Nephew'),
        ('Niece', 'Niece'),
        ('Cousin', 'Cousin'),
    )

    from_citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='relationships_from')
    to_citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='relationships_to')
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_citizen} is {self.relationship_type} of {self.to_citizen}"

    def clean(self):
        if self.from_citizen == self.to_citizen:
            raise ValidationError("A citizen cannot be related to themselves")

    class Meta:
        verbose_name = "Relationship"
        verbose_name_plural = "Relationships"
        unique_together = ('from_citizen', 'to_citizen', 'relationship_type')

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} on {self.model_name} ({self.object_id})"

# Added Models to Match admin.py

class Transaction(models.Model):
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='transactions')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateTimeField(auto_now_add=True)  # Matches TransactionAdmin.list_display
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.citizen} - {self.service} - {self.date}"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default='Citizen')  # Matches UserProfileAdmin.list_display
    barangay = models.CharField(max_length=100, blank=True, null=True)  # Matches UserProfileAdmin.list_display

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class ServiceApplication(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='service_applications')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Matches ServiceApplicationAdmin.list_display
    date_applied = models.DateTimeField(auto_now_add=True)  # Matches ServiceApplicationAdmin.list_display

    def __str__(self):
        return f"{self.citizen} applied for {self.service}"

    class Meta:
        verbose_name = "Service Application"
        verbose_name_plural = "Service Applications"

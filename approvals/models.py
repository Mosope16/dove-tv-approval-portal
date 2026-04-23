from django.db import models
from django.contrib.auth.models import User
from datetime import date

# 1. User Profiles & RBAC
class UserProfile(models.Model):
    class Role(models.TextChoices):
        STAFF = 'STAFF', 'Staff'
        MANAGER = 'MANAGER', 'Manager'
        HOU = 'HOU', 'Head of Unit'
        EXECUTIVE = 'EXECUTIVE', 'Executive'

    class Department(models.TextChoices):
        UNASSIGNED = 'UNASSIGNED', 'Unassigned'
        ICT = 'ICT', 'ICT'
        EDITING_SUITE = 'EDITING_SUITE', 'Editing Suite'
        MARKETING = 'MARKETING', 'Marketing'
        CAMERA = 'CAMERA', 'Camera'
        PRESENTER = 'PRESENTER', 'Presenter'
        MCR_LIBRARIAN = 'MCR_LIBRARIAN', 'MCR/Librarian'
        FINANCE = 'FINANCE', 'Finance'
        RECEPTION = 'RECEPTION', 'Reception'
        DATA_CENTRE = 'DATA_CENTRE', 'Data Centre'

    ACCESS_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('USER', 'User'),
    ]
    JOB_CHOICES = [
        ('MD_CEO', 'MD/CEO'),
        ('MFA', 'MFA'),
        ('MM', 'MM'),
        ('MES', 'MES'),
        ('MP', 'MP'),
        ('HOU_ICT', 'HOU-ICT'),
        ('HOU_EDIT', 'HOU-Editing Suite'),
        ('HOU_MKT', 'HOU-Marketing'),
        ('HOU_CAM', 'HOU-Camera'),
        ('HOU_PRES', 'HOU-Presenter'),
        ('HOU_FIN', 'HOU-Finance'),
        ('HOU_MCR', 'HOU-MCR'),
        ('MCR_LIB', 'MCR-Librarian'),
        ('MD_SEC', 'MD Secretary'),
        ('DATA_CTR', 'Data Centre'),
        ('WRK_ENGR', 'Workshop-Engr'),
        ('VCR', 'VCR'),
        ('SOC_MED', 'Social-Media'),
        ('OLD_ARENA', 'Old-Arena'),
        ('NEW_ARENA', 'New-Arena'),
        ('STR_ROOM', 'Streaming Room'),
        ('PRE_ROOM', 'Preview-Room'),
        ('RECEPTION', 'Reception'),
        ('PROG_ENG', 'Program Engineer'),
        ('ENG_MGR', 'Engineering Manager'),
        ('STAFF', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    access_role = models.CharField(max_length=10, choices=ACCESS_CHOICES, default='STAFF')
    job_role = models.CharField(max_length=20, choices=JOB_CHOICES, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    department = models.CharField(max_length=50, choices=Department.choices, default=Department.UNASSIGNED)
    is_out_of_office = models.BooleanField(default=False)
    email_on_status_change = models.BooleanField(default=True)
    email_on_action_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.access_role} ({self.job_role or 'No Job'})"

# Signals to auto-create profile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        access = 'ADMIN' if instance.is_superuser else 'STAFF'
        job = 'ENG_MGR' if instance.is_superuser else None
        UserProfile.objects.get_or_create(
            user=instance, 
            defaults={'access_role': access, 'job_role': job}
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# 2. Notifications
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # info, success, warning, alert
    type = models.CharField(max_length=20, default='info')
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

# 3. Gear Vault (Inventory)
class Equipment(models.Model):
    CATEGORY_CHOICES = [
        ('CAMERA', 'Camera'),
        ('MONITOR', 'Monitor'),
        ('STREAMBOX', 'Streambox'),
        ('CABLES', 'Cables'),
        ('MISC', 'Miscellaneous'),
    ]
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('IN_MAINTENANCE', 'In Maintenance'),
        ('RETIRED', 'Retired'),
    ]
    name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='MISC')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    condition = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class EquipmentCheckout(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RETURNED', 'Returned'),
    ]
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checkouts')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='checkouts')
    quantity_requested = models.PositiveIntegerField(default=1)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(blank=True, null=True)
    checkout_notes = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

# 4. Studio Bookings
class StudioBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    prog_name = models.CharField(max_length=200)
    date_of_recording = models.DateField()
    time_of_recording = models.CharField(max_length=50) # Format: "HH:MM-HH:MM"
    duration = models.CharField(max_length=50)
    mode = models.CharField(max_length=20, choices=[('LIVE', 'Live'), ('PRE_RECORDED', 'Pre-Recorded')])
    
    producer = models.CharField(max_length=100)
    presenter = models.CharField(max_length=100, default="N/A")
    producer_email = models.EmailField(blank=True, null=True)
    presenter_email = models.EmailField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='studio_bookings')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_studio_bookings')
    
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# 5. Marketing Job Orders
class MarketingJobOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketing_orders')
    job_description = models.TextField()
    place_of_assignment = models.CharField(max_length=200)
    date_of_assignment = models.DateField()
    time_of_assignment = models.TimeField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_marketing_orders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# 6. Engineer Duty Roster
class DutyRoster(models.Model):
    POSITION_CHOICES = [
        ('AUDIO', 'Audio Engineer'),
        ('DUTY', 'Engineer On Duty (F)'),
        ('OB', 'Outside Broadcast / Arena'),
        ('BCAST_IT', 'Broadcast IT/ICT'),
        ('STREAMING', 'Streaming'),
    ]
    date = models.DateField()
    engineer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duty_shifts')
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='DUTY')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='duty_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('date', 'position', 'engineer') 
        ordering = ['date']

# 7. Fault Reports
class FaultReport(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100) # e.g. "Studio A"
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_faults')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_faults')
    
    resolved_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
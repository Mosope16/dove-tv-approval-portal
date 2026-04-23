from django.contrib import admin
from .models import UserProfile, Notification, Equipment, EquipmentCheckout, StudioBooking, MarketingJobOrder, DutyRoster, FaultReport

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Unregister default User admin
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_role', 'job_role', 'is_out_of_office')
    list_filter = ('access_role', 'job_role', 'is_out_of_office')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'type')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'available_quantity', 'quantity')
    list_filter = ('category', 'status')
    search_fields = ('name', 'serial_number')

@admin.register(EquipmentCheckout)
class EquipmentCheckoutAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'requester', 'quantity_requested', 'status', 'expected_return_date')
    list_filter = ('status', 'expected_return_date')

@admin.register(StudioBooking)
class StudioBookingAdmin(admin.ModelAdmin):
    list_display = ('prog_name', 'date_of_recording', 'time_of_recording', 'status', 'requester')
    list_filter = ('status', 'mode', 'date_of_recording')
    search_fields = ('prog_name', 'producer', 'presenter')

@admin.register(MarketingJobOrder)
class MarketingJobOrderAdmin(admin.ModelAdmin):
    list_display = ('place_of_assignment', 'date_of_assignment', 'status', 'requester')
    list_filter = ('status', 'date_of_assignment')

@admin.register(DutyRoster)
class DutyRosterAdmin(admin.ModelAdmin):
    list_display = ('date', 'engineer', 'created_by')
    list_filter = ('date', 'engineer')

@admin.register(FaultReport)
class FaultReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'priority', 'status', 'reporter', 'assignee')
    list_filter = ('priority', 'status', 'location')
    search_fields = ('title', 'description')
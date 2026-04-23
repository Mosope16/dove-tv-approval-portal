from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='signup'),
    
    # Bookings
    path('bookings/', views.booking_hub, name='booking_hub'),
    path('bookings/process/<int:booking_id>/<str:action>/', views.process_booking, name='process_booking'),
    path('bookings/print/<int:booking_id>/', views.print_booking_memo, name='print_booking_memo'),
    
    # Marketing
    path('marketing/', views.marketing_hub, name='marketing_hub'),
    path('marketing/process/<int:job_id>/<str:action>/', views.process_marketing, name='process_marketing'),
    path('marketing/print/<int:job_id>/', views.print_marketing_memo, name='print_marketing_memo'),
    
    # Inventory
    path('inventory/', views.inventory_hub, name='inventory'),
    path('inventory/request/<int:equipment_id>/', views.request_checkout, name='request_checkout'),
    path('inventory/process/<int:checkout_id>/<str:action>/', views.process_checkout, name='process_checkout'),
    
    # Faults
    path('faults/', views.fault_hub, name='fault_hub'),
    path('faults/update/<int:fault_id>/', views.update_fault, name='update_fault'),
    
    # Roster
    path('roster/', views.roster_view, name='roster'),
    path('roster/assign/', views.assign_duty, name='assign_duty'),
    
    # Notifications
    path('notifications/read/', views.read_notifications, name='read_notifications'),
    
    # Settings & User Management
    path('settings/', views.settings, name='settings'),
    path('settings/update-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
]
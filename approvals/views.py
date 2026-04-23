from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
import json
import calendar
from datetime import date, datetime, timedelta
from .models import (
    StudioBooking, MarketingJobOrder, EquipmentCheckout, 
    UserProfile, Notification, Equipment, FaultReport, DutyRoster
)
from .forms import (
    BookingForm, MarketingJobForm, EquipmentCheckoutForm, 
    CustomSignupForm, EquipmentForm, FaultReportForm, DutyAssignmentForm,
    UserUpdateForm, UserProfileForm
)
from .utils import role_required, can_approve_requests

def dispatch_alert(user, title, message, alert_type='info', link=None):
    Notification.objects.create(user=user, title=title, message=message, type=alert_type, link=link)

def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomSignupForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user, 
        defaults={'access_role': 'STAFF'}
    )
    user_access = profile.access_role
    user_job = profile.job_role
    
    # Checkouts that are "APPROVED" (ready for pickup) or "ACTIVE" (checked out)
    active_checkouts = EquipmentCheckout.objects.filter(status='APPROVED').select_related('requester', 'equipment')
    if user_access == 'USER' or (user_access == 'STAFF' and user_job == 'STAFF'):
        active_checkouts = active_checkouts.filter(requester=request.user)

    pending_checkouts = EquipmentCheckout.objects.filter(status='PENDING').select_related('requester', 'equipment')
    pending_bookings = StudioBooking.objects.filter(status='PENDING').select_related('requester')
    pending_marketing = MarketingJobOrder.objects.filter(status='PENDING').select_related('requester')
    
    # Detailed Stats for the new High-Fidelity UI
    total_studio = StudioBooking.objects.count()
    total_marketing = MarketingJobOrder.objects.count()
    
    total_pending = (
        pending_bookings.count() + 
        pending_marketing.count() + 
        pending_checkouts.count()
    )
    
    user_requests_count = (
        StudioBooking.objects.filter(requester=request.user).count() +
        MarketingJobOrder.objects.filter(requester=request.user).count() +
        EquipmentCheckout.objects.filter(requester=request.user).count()
    )
    
    recent_studio_requests = StudioBooking.objects.all().select_related('requester').order_by('-created_at')[:10]
    
    # Faults summary (Restored)
    open_faults = FaultReport.objects.filter(status='OPEN').count()
    critical_faults = FaultReport.objects.filter(priority='CRITICAL').exclude(status='CLOSED').count()

    context = {
        'total_bookings_count': total_studio + total_marketing,
        'pending_approvals_count': total_pending,
        'your_requests_count': user_requests_count,
        'recent_studio_requests': recent_studio_requests,
        'pending_bookings': pending_bookings,
        'pending_marketing': pending_marketing,
        'pending_checkouts': pending_checkouts,
        'open_faults_count': open_faults,
        'critical_faults_count': critical_faults,
        'user_access': user_access,
        'user_job': user_job,
        'can_approve': can_approve_requests(request.user),
        'unread_notif_count': request.user.notifications.filter(is_read=False).count(),
    }
    return render(request, 'approvals/dashboard.html', context)

@login_required
def booking_hub(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.requester = request.user
            # Combine start and end into the time_of_recording string
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            booking.time_of_recording = f"{start} - {end}"
            
            try:
                start_dt = datetime.strptime(start, '%H:%M')
                end_dt = datetime.strptime(end, '%H:%M')
                diff = end_dt - start_dt
                if diff.days < 0: diff = timedelta(days=0) # Prevent negative if clashing
                hours, remainder = divmod(diff.seconds, 3600)
                minutes = remainder // 60
                
                parts = []
                if hours > 0: parts.append(f"{hours} hr{'s' if hours > 1 else ''}")
                if minutes > 0: parts.append(f"{minutes} min{'s' if minutes > 1 else ''}")
                booking.duration = " ".join(parts) if parts else "0 mins"
            except:
                booking.duration = "Unknown"
                
            booking.save()
            
            # Notify Managers
            managers = User.objects.filter(profile__role__in=['MANAGER', 'HOU'])
            for mgr in managers:
                dispatch_alert(mgr, "New Booking Request", f"{request.user.username} requested studio for {booking.prog_name}", "info", "/dashboard/")
                
            return redirect('dashboard')
    else:
        form = BookingForm()
    
    bookings = StudioBooking.objects.all().order_by('-date_of_recording')
    return render(request, 'approvals/booking_hub.html', {'form': form, 'bookings': bookings})

@login_required
def inventory_hub(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    is_manager = profile.access_role in ['ADMIN', 'STAFF']
    
    if request.method == 'POST' and is_manager:
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.available_quantity = equipment.quantity
            equipment.save()
            return redirect('inventory')
    
    equipment_list = Equipment.objects.all().order_by('category', 'name')
    categories = Equipment.CATEGORY_CHOICES
    
    stats = {
        'total': sum(e.quantity for e in equipment_list),
        'available': sum(e.available_quantity for e in equipment_list),
        'maintenance': equipment_list.filter(status='IN_MAINTENANCE').count(),
    }
    
    return render(request, 'approvals/inventory.html', {
        'equipment_list': equipment_list,
        'categories': categories,
        'stats': stats,
        'form': EquipmentForm(),
        'is_manager': is_manager
    })

@login_required
@transaction.atomic
def request_checkout(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        return_date = request.POST.get('return_date')
        notes = request.POST.get('notes')
        
        if qty > equipment.available_quantity:
            return JsonResponse({'error': 'Not enough stock available'}, status=400)
            
        checkout = EquipmentCheckout.objects.create(
            requester=request.user,
            equipment=equipment,
            quantity_requested=qty,
            expected_return_date=return_date,
            checkout_notes=notes,
            status='PENDING'
        )
        
        return redirect('inventory')
    return redirect('inventory')

@login_required
def marketing_hub(request):
    if request.method == 'POST':
        form = MarketingJobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.requester = request.user
            job.save()
            
            # Notify Managers
            managers = User.objects.filter(profile__role__in=['MANAGER', 'HOU'])
            for mgr in managers:
                dispatch_alert(mgr, "New Marketing Job", f"{request.user.username} requested a job for {job.place_of_assignment}", "info", "/dashboard/")
                
            return redirect('dashboard')
    else:
        form = MarketingJobForm()
    
    jobs = MarketingJobOrder.objects.all().order_by('-date_of_assignment')
    return render(request, 'approvals/marketing_hub.html', {'form': form, 'jobs': jobs})

@login_required
@role_required('ADMIN', allow_delegation=True)
def process_marketing(request, job_id, action):
    job = get_object_or_404(MarketingJobOrder, id=job_id)
    
    if action == 'approve' and job.status == 'PENDING':
        job.status = 'APPROVED'
        job.approver = request.user
        job.save()
        dispatch_alert(job.requester, "Job Approved", f"Your marketing job for {job.place_of_assignment} was approved.", "success")
            
    elif action == 'reject' and job.status == 'PENDING':
        job.status = 'DENIED'
        job.save()
        
    return redirect('dashboard')

@login_required
@role_required('ADMIN', allow_delegation=True)
def process_checkout(request, checkout_id, action):
    checkout = get_object_or_404(EquipmentCheckout, id=checkout_id)
    
    if action == 'approve' and checkout.status == 'PENDING':
        if checkout.equipment.available_quantity >= checkout.quantity_requested:
            checkout.status = 'APPROVED'
            checkout.equipment.available_quantity -= checkout.quantity_requested
            checkout.equipment.save()
            checkout.save()
            dispatch_alert(checkout.requester, "Checkout Approved", f"Your request for {checkout.equipment.name} was approved.", "success")
        else:
            return JsonResponse({'error': 'Insufficient stock'}, status=400)
            
    elif action == 'reject' and checkout.status == 'PENDING':
        checkout.status = 'REJECTED'
        checkout.save()
        
    elif action == 'return' and checkout.status == 'APPROVED':
        checkout.status = 'RETURNED'
        checkout.actual_return_date = date.today()
        checkout.equipment.available_quantity += checkout.quantity_requested
        checkout.equipment.save()
        checkout.save()
        dispatch_alert(checkout.requester, "Gear Returned", f"Equipment {checkout.equipment.name} has been marked as returned.", "info")
        
    return redirect('dashboard')

@login_required
@role_required('ADMIN', allow_delegation=True)
def process_booking(request, booking_id, action):
    booking = get_object_or_404(StudioBooking, id=booking_id)
    
    if action == 'approve' and booking.status == 'PENDING':
        booking.status = 'APPROVED'
        booking.approver = request.user
        booking.save()
        dispatch_alert(booking.requester, "Studio Approved", f"Your studio booking for {booking.prog_name} was approved.", "success")
            
    elif action == 'reject' and booking.status == 'PENDING':
        booking.status = 'DENIED'
        booking.save()
        
    return redirect('dashboard')

@login_required
def fault_hub(request):
    if request.method == 'POST':
        form = FaultReportForm(request.POST)
        if form.is_valid():
            fault = form.save(commit=False)
            fault.reporter = request.user
            fault.save()
            
            # Notify engineers
            engineers = User.objects.filter(profile__department='ICT')
            for eng in engineers:
                dispatch_alert(eng, "🔴 New Fault Report", f"{request.user.username} reported a fault at {fault.location}", "alert", "/faults/")
            
            return redirect('fault_hub')
    else:
        form = FaultReportForm()
        
    faults = FaultReport.objects.all().order_by('-created_at')
    engineers = User.objects.filter(profile__department='ICT')
    
    return render(request, 'approvals/faults.html', {
        'faults': faults,
        'form': form,
        'engineers': engineers,
        'is_privileged': request.user.profile.access_role in ['ADMIN', 'STAFF']
    })

@login_required
@role_required('ADMIN', 'STAFF', allow_delegation=True)
def update_fault(request, fault_id):
    fault = get_object_or_404(FaultReport, id=fault_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        assignee_id = request.POST.get('assignee_id')
        note = request.POST.get('resolved_note')
        
        if status: fault.status = status
        if assignee_id: fault.assignee = get_object_or_404(User, id=assignee_id)
        if note: fault.resolved_note = note
        
        fault.save()
        
        # Notify reporter on status change
        if status in ['IN_PROGRESS', 'RESOLVED']:
            dispatch_alert(fault.reporter, f"Fault Update: {status}", f"Your report '{fault.title}' is now {status.lower()}.", "info")
            
    return redirect('fault_hub')

@login_required
@role_required('ADMIN', 'STAFF')
def roster_view(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    month_name = calendar.month_name[month]
    
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
        
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    start_date = date(year, month, 1)
    if month == 12: end_date = date(year + 1, 1, 1)
    else: end_date = date(year, month + 1, 1)
    
    duties = DutyRoster.objects.filter(date__gte=start_date, date__lt=end_date).select_related('engineer')
    
    duties_by_day = {}
    import calendar as py_cal
    num_days = py_cal.monthrange(year, month)[1]
    for d in range(1, num_days + 1):
        duties_by_day[d] = {}

    for duty in duties:
        if duty.position not in duties_by_day[duty.date.day]:
            duties_by_day[duty.date.day][duty.position] = []
        duties_by_day[duty.date.day][duty.position].append(duty)

    engineers = User.objects.filter(profile__department='ICT')
    positions = DutyRoster.POSITION_CHOICES

    return render(request, 'approvals/roster.html', {
        'month_days': month_days,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_m': prev_month, 'prev_y': prev_year,
        'next_m': next_month, 'next_y': next_year,
        'duties_by_day': duties_by_day,
        'engineers': engineers,
        'positions': positions,
        'is_manager': can_approve_requests(request.user)
    })

@login_required
@role_required('ADMIN', allow_delegation=True)
def assign_duty(request):
    if request.method == 'POST':
        eng_id = request.POST.get('engineer_id')
        duty_date = request.POST.get('date')
        position = request.POST.get('position')
        notes = request.POST.get('notes')
        
        DutyRoster.objects.update_or_create(
            date=duty_date,
            position=position,
            defaults={
                'engineer_id': eng_id,
                'notes': notes,
                'created_by': request.user
            }
        )
    return redirect('roster')

@login_required
def read_notifications(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get('action') == 'mark_all':
            request.user.notifications.filter(is_read=False).update(is_read=True)
        elif data.get('action') == 'mark_one':
            request.user.notifications.filter(id=data.get('notif_id')).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileForm(request.POST, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            from django.contrib import messages
            messages.success(request, "Settings updated successfully!")
            return redirect('settings')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'user_access': profile.access_role,
        'user_job': profile.job_role,
        'all_users': UserProfile.objects.all().select_related('user') if profile.access_role == 'ADMIN' else [],
        'access_choices': UserProfile.ACCESS_CHOICES,
        'job_choices': UserProfile.JOB_CHOICES
    }
    return render(request, 'approvals/settings.html', context)

@login_required
@role_required('ADMIN')
def update_user_role(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        target_profile, _ = UserProfile.objects.get_or_create(user=target_user)
        
        access_role = request.POST.get('access_role')
        job_role = request.POST.get('job_role')
        
        if access_role: target_profile.access_role = access_role
        if job_role: target_profile.job_role = job_role
        
        target_profile.save()
        from django.contrib import messages
        messages.success(request, f"Roles for {target_user.username} updated.")
        
    return redirect('settings')

@login_required
def print_booking_memo(request, booking_id):
    booking = get_object_or_404(StudioBooking, id=booking_id)
    if booking.status != 'APPROVED':
        from django.contrib import messages
        messages.error(request, "This booking has not been fully approved yet and cannot be printed.")
        return redirect('dashboard')
    
    return render(request, 'approvals/memo.html', {'booking': booking})

@login_required
def print_marketing_memo(request, job_id):
    job = get_object_or_404(MarketingJobOrder, id=job_id)
    if job.status != 'APPROVED':
        from django.contrib import messages
        messages.error(request, "This marketing job has not been fully approved yet and cannot be printed.")
        return redirect('dashboard')
        
    return render(request, 'approvals/marketing_memo.html', {'job': job})
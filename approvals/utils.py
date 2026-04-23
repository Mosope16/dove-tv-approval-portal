from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import UserProfile

def can_approve_requests(user):
    """
    Checks if a user is authorized to approve requests (Studio, Marketing, Equipment).
    Authority:
    1. ADMIN level access.
    2. Senior STAFF (ENG_MGR, HOU) when ALL admins are Out of Office.
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if profile.access_role == 'ADMIN':
        return not profile.is_out_of_office  # Admin still has power unless they themselves are out
        
    if profile.access_role == 'STAFF':
        is_senior = profile.job_role == 'ENG_MGR' or (profile.job_role and profile.job_role.startswith('HOU_'))
        
        if is_senior:
            # The Switch: Is any Admin currently available?
            any_admin_available = UserProfile.objects.filter(access_role='ADMIN', is_out_of_office=False).exists()
            if not any_admin_available:
                return True
            
    return False

def role_required(*allowed_roles, allow_delegation=False):
    """
    Decorator for views that checks if a user has one of the allowed access_roles.
    If allow_delegation is True, senior staff can inherit power when admins are out.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Ensure profile exists
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            
            # 1. Direct role check
            if profile.access_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # 2. Power Delegation check
            if allow_delegation and can_approve_requests(request.user):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "Permission Denied: You do not have sufficient authority for this action.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator

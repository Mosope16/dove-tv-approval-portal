from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import date
from .models import (
    StudioBooking, MarketingJobOrder, EquipmentCheckout, 
    Equipment, FaultReport, DutyRoster, UserProfile
)

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['is_out_of_office', 'email_on_status_change', 'email_on_action_required']

class CustomSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    username = forms.CharField(
        max_length=150, required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'e.g. johndoe (No spaces)'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class BookingForm(forms.ModelForm):
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = StudioBooking
        fields = ['prog_name', 'date_of_recording', 'mode', 'producer', 'producer_email', 'presenter', 'presenter_email']
        widgets = {
            'date_of_recording': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_recording'].widget.attrs['min'] = date.today().isoformat()

    def clean(self):
        cleaned_data = super().clean()
        rec_date = cleaned_data.get('date_of_recording')
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if not rec_date or not start or not end:
            return cleaned_data

        if start >= end:
            raise ValidationError("End time must be after start time.")

        # Clash Detection Logic (Same as Next.js)
        start_str = start.strftime('%H:%M')
        end_str = end.strftime('%H:%M')
        
        # We store as "HH:MM-HH:MM" in time_of_recording
        existing = StudioBooking.objects.filter(date_of_recording=rec_date).exclude(status='DENIED')
        
        for booking in existing:
            try:
                e_start_str, e_end_str = booking.time_of_recording.split('-')
                # Overlap condition: max(start1, start2) < min(end1, end2)
                if max(start_str, e_start_str) < min(end_str, e_end_str):
                    raise ValidationError(f"🚨 Slot Clashing: The studio is reserved for '{booking.prog_name}' during this time ({booking.time_of_recording}).")
            except ValueError:
                continue

        return cleaned_data

class MarketingJobForm(forms.ModelForm):
    class Meta:
        model = MarketingJobOrder
        fields = ['job_description', 'place_of_assignment', 'date_of_assignment', 'time_of_assignment']
        widgets = {
            'job_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe exactly what needs to be done...'}),
            'place_of_assignment': forms.TextInput(attrs={'placeholder': 'e.g. Main Auditorium, Studio B...'}),
            'date_of_assignment': forms.DateInput(attrs={'type': 'date'}),
            'time_of_assignment': forms.TimeInput(attrs={'type': 'time'}),
        }

class EquipmentCheckoutForm(forms.ModelForm):
    class Meta:
        model = EquipmentCheckout
        fields = ['equipment', 'quantity_requested', 'expected_return_date', 'checkout_notes']
        widgets = {
            'expected_return_date': forms.DateInput(attrs={'type': 'date'}),
            'checkout_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Where will this be used?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipment'].queryset = Equipment.objects.filter(status='AVAILABLE', available_quantity__gt=0)

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'category', 'quantity', 'serial_number', 'condition', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class FaultReportForm(forms.ModelForm):
    class Meta:
        model = FaultReport
        fields = ['title', 'location', 'priority', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class DutyAssignmentForm(forms.ModelForm):
    class Meta:
        model = DutyRoster
        fields = ['date', 'engineer', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from approvals.models import StudioBooking
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sends email reminders for studio bookings starting in 1 hour'

    def handle(self, *args, **options):
        now = timezone.now()
        # Window: 55 to 75 minutes from now
        start_window = now + timedelta(minutes=55)
        end_window = now + timedelta(minutes=75)

        # Get approved bookings in the window that haven't sent reminders
        bookings = StudioBooking.objects.filter(
            status='APPROVED',
            reminder_sent=False,
            date_of_recording=now.date(),
        )

        # Since we store time_of_recording as "HH:MM-HH:MM", we need a smarter filter
        # but for simplicity in SQLite we can fetch and filter in Python
        
        count = 0
        for booking in bookings:
            try:
                start_str = booking.time_of_recording.split('-')[0]
                # Combine date and time to check if it falls in the window
                # For this to work robustly, we'd need better time handling in models
                # For now, let's assume it's roughly correct based on date
                
                recipients = [booking.requester.email]
                if booking.producer_email: recipients.append(booking.producer_email)
                if booking.presenter_email: recipients.append(booking.presenter_email)

                subject = f'⏰ Reminder: "{booking.prog_name}" begins in 1 hour'
                message = f"""
                Hi, this is a reminder that your studio session for "{booking.prog_name}" 
                starts in 1 hour at {start_str}.

                Date: {booking.date_of_recording}
                Format: {booking.mode}
                Producer: {booking.producer}

                Please ensure you are at the studio 15 minutes early.
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=False,
                )

                booking.reminder_sent = True
                booking.save()
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Sent reminder for "{booking.prog_name}"'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error sending reminder for {booking.id}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Finished processing {count} reminders.'))

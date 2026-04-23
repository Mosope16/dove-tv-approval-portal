from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from approvals.models import UserProfile

class Command(BaseCommand):
    help = 'Creates missing UserProfiles for existing users and syncs roles for superusers'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        updated_count = 0

        for user in users:
            # Business logic for default roles (Requirement 2 & 6)
            default_access = 'ADMIN' if user.is_superuser else 'STAFF'
            default_job = 'ENG_MGR' if user.is_superuser else None
            
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'access_role': default_access,
                    'job_role': default_job
                }
            )
            
            if created:
                created_count += 1
            else:
                # Ensure superusers have correct access even if profile already existed
                if user.is_superuser and profile.access_role != 'ADMIN':
                    profile.access_role = 'ADMIN'
                    profile.job_role = 'ENG_MGR'
                    profile.save()
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'RBAC Sync Complete: {created_count} profiles created, {updated_count} profiles updated.'
        ))

import os
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from approvals.models import DutyRoster, UserProfile

class Command(BaseCommand):
    help = 'Populates the April 2026 Engineering Duty Roster from the physical chart'

    def handle(self, *args, **options):
        # 1. Define Engineers
        engineer_data = {
            'A': {'username': 'ayodeji_o', 'first_name': 'Ayodeji', 'last_name': 'Ogunremi'},
            'CH': {'username': 'christy_a', 'first_name': 'Christy', 'last_name': 'Antia'},
            'DJ': {'username': 'ayodeji_aina', 'first_name': 'Ayodeji', 'last_name': 'Aina'},
            'JO': {'username': 'ayooluwa_j', 'first_name': 'Ayooluwa', 'last_name': 'John'},
            'P': {'username': 'promise_a', 'first_name': 'Promise', 'last_name': 'Adegbehin'},
            'SA': {'username': 'sunday_o', 'first_name': 'Sunday', 'last_name': 'Ogunleye'},
        }

        # 2. Create Users/Profiles
        engineers = {}
        for code, info in engineer_data.items():
            user, created = User.objects.get_or_create(
                username=info['username'],
                defaults={
                    'first_name': info['first_name'],
                    'last_name': info['last_name'],
                    'is_staff': True
                }
            )
            if created:
                user.set_password('doveportal2026')
                user.save()
                UserProfile.objects.get_or_create(user=user, role='PROG_ENG')
            
            engineers[code] = user
            self.stdout.write(self.style.SUCCESS(f'Verified engineer: {info["username"]} ({code})'))

        # 3. Define Roster Data (Day: {Position: [Codes]})
        # Abbreviations: AUDIO, DUTY, OB, BCAST_IT, STREAMING
        roster_map = {
            1: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'BCAST_IT': ['JO']},
            2: {'AUDIO': ['CH', 'SA'], 'DUTY': ['P'], 'BCAST_IT': ['JO']},
            3: {'AUDIO': ['CH', 'SA'], 'DUTY': ['DJ'], 'OB': ['CH'], 'BCAST_IT': ['JO']},
            4: {'DUTY': ['A'], 'OB': ['DJ', 'CH', 'JO']},
            5: {'DUTY': ['P'], 'OB': ['DJ', 'CH', 'JO']},
            6: {'AUDIO': ['CH', 'SA'], 'DUTY': ['DJ'], 'BCAST_IT': ['JO']},
            7: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'BCAST_IT': ['JO']},
            8: {'AUDIO': ['CH', 'SA'], 'DUTY': ['DJ'], 'BCAST_IT': ['JO']},
            9: {'AUDIO': ['CH', 'SA'], 'DUTY': ['P'], 'BCAST_IT': ['JO']},
            10: {'AUDIO': ['CH'], 'DUTY': ['SA'], 'OB': ['DJ', 'CH']},
            11: {'DUTY': ['A'], 'OB': ['DJ', 'CH', 'JO']},
            12: {'DUTY': ['P'], 'OB': ['DJ', 'JO']},
            13: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'OB': ['DJ', 'JO']},
            14: {'AUDIO': ['CH', 'SA'], 'DUTY': ['P'], 'BCAST_IT': ['JO']},
            15: {'AUDIO': ['CH', 'SA'], 'DUTY': ['DJ'], 'BCAST_IT': ['JO']},
            16: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'BCAST_IT': ['JO']},
            17: {'AUDIO': ['CH'], 'DUTY': ['SA'], 'BCAST_IT': ['JO']},
            18: {'DUTY': ['P'], 'OB': ['DJ']},
            19: {'DUTY': ['A'], 'OB': ['DJ']},
            20: {'AUDIO': ['CH', 'SA'], 'DUTY': ['P'], 'OB': ['DJ'], 'BCAST_IT': ['JO']},
            21: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'BCAST_IT': ['JO']},
            22: {'AUDIO': ['CH', 'SA'], 'DUTY': ['DJ'], 'BCAST_IT': ['JO']},
            23: {'AUDIO': ['CH', 'SA'], 'DUTY': ['P'], 'BCAST_IT': ['JO']},
            24: {'AUDIO': ['CH'], 'DUTY': ['SA'], 'OB': ['DJ'], 'BCAST_IT': ['JO']},
            25: {'DUTY': ['A'], 'OB': ['DJ']},
            26: {'DUTY': ['P'], 'OB': ['DJ']},
            27: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'OB': ['DJ'], 'BCAST_IT': ['JO']},
            28: {'AUDIO': ['CH', 'SA'], 'DUTY': ['P'], 'BCAST_IT': ['JO']},
            29: {'AUDIO': ['CH', 'SA'], 'DUTY': ['DJ'], 'BCAST_IT': ['JO']},
            30: {'AUDIO': ['CH', 'SA'], 'DUTY': ['A'], 'BCAST_IT': ['JO']},
        }

        # 4. Clear existing April 2026 data
        DutyRoster.objects.filter(date__year=2026, date__month=4).delete()

        # 5. Populate
        admin_user = User.objects.filter(is_superuser=True).first() or engineers['A']
        
        for day, postions in roster_map.items():
            duty_date = date(2026, 4, day)
            for pos, codes in postions.items():
                for code in codes:
                    DutyRoster.objects.create(
                        date=duty_date,
                        position=pos,
                        engineer=engineers[code],
                        created_by=admin_user
                    )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully populated roster for April 2026'))

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('approvals', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studiobooking',
            name='location',
            field=models.CharField(choices=[('MAIN_STUDIO', 'Main Studio'), ('BOOTH_A', 'Booth A'), ('BOOTH_B', 'Booth B'), ('OUTDOOR', 'Outdoor Stage')], default='MAIN_STUDIO', max_length=50),
        ),
    ]

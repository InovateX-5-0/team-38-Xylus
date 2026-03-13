from django.db import migrations, models


def migrate_appointment_statuses(apps, schema_editor):
    Appointment = apps.get_model('myapp', 'Appointment')
    Appointment.objects.filter(status__in=['approved', 'completed']).update(status='confirmed')
    Appointment.objects.filter(status='rejected').update(status='cancelled')


def reverse_migrate_appointment_statuses(apps, schema_editor):
    Appointment = apps.get_model('myapp', 'Appointment')
    Appointment.objects.filter(status='confirmed').update(status='approved')
    Appointment.objects.filter(status='cancelled').update(status='rejected')


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_update_serviceprovider_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='notification_seen',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrate_appointment_statuses, reverse_migrate_appointment_statuses),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='pending', max_length=15),
        ),
    ]

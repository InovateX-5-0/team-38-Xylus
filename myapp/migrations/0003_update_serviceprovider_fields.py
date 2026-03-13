from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_alter_customuser_role_serviceprovider_servicebooking'),
    ]

    operations = [
        # Rename business_name -> name
        migrations.RenameField(
            model_name='serviceprovider',
            old_name='business_name',
            new_name='name',
        ),
        # Rename category -> provider_type
        migrations.RenameField(
            model_name='serviceprovider',
            old_name='category',
            new_name='provider_type',
        ),
        # Update provider_type choices and max_length
        migrations.AlterField(
            model_name='serviceprovider',
            name='provider_type',
            field=models.CharField(
                choices=[
                    ('VET', 'Vet Clinic'),
                    ('SHELTER', 'Shelter'),
                    ('PET_STORE', 'Pet Store'),
                    ('GROOMER', 'Groomer'),
                ],
                max_length=20,
            ),
        ),
        # Add provider_id_file
        migrations.AddField(
            model_name='serviceprovider',
            name='provider_id_file',
            field=models.FileField(blank=True, null=True, upload_to='provider_ids/'),
        ),
        # Add is_verified
        migrations.AddField(
            model_name='serviceprovider',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        # Make address optional (was required)
        migrations.AlterField(
            model_name='serviceprovider',
            name='address',
            field=models.TextField(blank=True),
        ),
        # Make city optional
        migrations.AlterField(
            model_name='serviceprovider',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        # Make phone optional
        migrations.AlterField(
            model_name='serviceprovider',
            name='phone',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]

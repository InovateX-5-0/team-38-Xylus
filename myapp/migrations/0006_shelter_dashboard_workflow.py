from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_vet_dashboard_workflow'),
    ]

    operations = [
        migrations.CreateModel(
            name='Animal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('species', models.CharField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('rabbit', 'Rabbit'), ('other', 'Other')], max_length=20)),
                ('breed', models.CharField(blank=True, max_length=100)),
                ('age', models.PositiveIntegerField(help_text='Age in months')),
                ('gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female')], max_length=10)),
                ('size', models.CharField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], default='medium', max_length=10)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='shelter_animals/')),
                ('rescue_location', models.CharField(blank=True, max_length=200)),
                ('intake_date', models.DateField(default=django.utils.timezone.now)),
                ('health_status', models.CharField(choices=[('healthy', 'Healthy'), ('needs_care', 'Needs Care'), ('critical', 'Critical')], default='healthy', max_length=20)),
                ('vaccination_status', models.CharField(choices=[('up_to_date', 'Up to Date'), ('due', 'Due'), ('not_vaccinated', 'Not Vaccinated')], default='due', max_length=20)),
                ('adoption_status', models.CharField(choices=[('available', 'Available'), ('adopted', 'Adopted')], default='available', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('adopted_at', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shelter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='animals', to='myapp.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='AdoptionApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applicant_name', models.CharField(max_length=150)),
                ('contact_info', models.CharField(max_length=200)),
                ('living_situation', models.CharField(max_length=200)),
                ('pet_experience', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('animal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='myapp.animal')),
                ('applicant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shelter_applications', to='myapp.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='ShelterIntake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intake_date', models.DateField(default=django.utils.timezone.now)),
                ('rescue_location', models.CharField(blank=True, max_length=200)),
                ('health_status', models.CharField(choices=[('healthy', 'Healthy'), ('needs_care', 'Needs Care'), ('critical', 'Critical')], default='healthy', max_length=20)),
                ('vaccination_status', models.CharField(choices=[('up_to_date', 'Up to Date'), ('due', 'Due'), ('not_vaccinated', 'Not Vaccinated')], default='due', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('animal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intakes', to='myapp.animal')),
                ('shelter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shelter_intakes', to='myapp.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='AdoptionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('adopter_name', models.CharField(max_length=150)),
                ('adoption_date', models.DateField(default=django.utils.timezone.now)),
                ('days_to_adoption', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('animal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adoption_records', to='myapp.animal')),
                ('application', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='adoption_records', to='myapp.adoptionapplication')),
                ('shelter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adoption_records', to='myapp.customuser')),
            ],
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_socialpost_lost_found_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='profile_visibility',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='private', max_length=10),
        ),
        migrations.AddField(
            model_name='customuser',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
    ]

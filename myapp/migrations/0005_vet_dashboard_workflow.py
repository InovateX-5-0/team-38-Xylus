from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_appointment_request_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='healthrecord',
            name='visit_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('follow_up', 'Follow-up')], default='completed', max_length=15),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=15),
        ),
        migrations.CreateModel(
            name='MedicineInventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medicine_name', models.CharField(max_length=150)),
                ('category', models.CharField(choices=[('vaccines', 'Vaccines'), ('antibiotics', 'Antibiotics'), ('surgical', 'Surgical Supplies'), ('dewormers', 'Dewormers'), ('other', 'Other')], default='other', max_length=20)),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('low_stock_threshold', models.PositiveIntegerField(default=5)),
                ('supplier_shop', models.CharField(blank=True, max_length=200)),
                ('price_per_unit', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('clinic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='medicine_inventory', to='myapp.vetclinic')),
                ('vet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medicine_inventory', to='myapp.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='SupplyOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supplier_shop', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField()),
                ('price_per_unit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('ordered', 'Ordered'), ('received', 'Received'), ('cancelled', 'Cancelled')], default='ordered', max_length=15)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('clinic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supply_orders', to='myapp.vetclinic')),
                ('medicine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='myapp.medicineinventory')),
                ('vet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supply_orders', to='myapp.customuser')),
            ],
        ),
    ]

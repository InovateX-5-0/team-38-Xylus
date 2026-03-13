from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, F, Avg
from decimal import Decimal
from datetime import timedelta, datetime
from django.db.models import Sum
from django.db.models.functions import TruncMonth
import json
import requests
from .models import *
from .forms import *


# ─── AUTH ────────────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to PawNest, {user.first_name}! 🐾")
        return redirect('dashboard')
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request,
                            username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'owner':
        pets = Pet.objects.filter(owner=user)
        reminders_qs = VaccinationReminder.objects.filter(pet__owner=user, status='pending').order_by('due_date')
        reminders = reminders_qs[:5]
        appointments = Appointment.objects.filter(owner=user, status__in=['pending', 'confirmed']).order_by('date')[:5]
        posts_count = SocialPost.objects.filter(author=user).count()
        overdue = reminders_qs.filter(due_date__lt=timezone.now().date())
        context = {
            'pets': pets,
            'service_provider': user.service_profiles.first(),
            'reminders': reminders,
            'appointments': appointments,
            'posts_count': posts_count,
            'overdue_count': overdue.count(),
            'upcoming_appointments': appointments,
        }
        return render(request, 'dashboard/owner_dashboard.html', context)

    elif user.role == 'vet':
        try:
            clinic = user.clinic
        except VetClinic.DoesNotExist:
            clinic = None
        appointments = Appointment.objects.filter(vet=user).order_by('-date')
        today = timezone.now().date()
        todays_appointments = appointments.filter(date=today)
        pending = appointments.filter(status='pending')
        unique_patients = Pet.objects.filter(appointments__vet=user).distinct().count()
        waiting_room = todays_appointments.filter(status='confirmed').count()
        recent_records = HealthRecord.objects.filter(vet=user).order_by('-date')[:8]
        medicines = MedicineInventory.objects.filter(vet=user).order_by('medicine_name')
        low_stock_items = [item for item in medicines if item.is_low_stock]

        medicine_form = MedicineInventoryForm()
        patient_record_form = VetPatientRecordForm(user=user)
        context = {
            'clinic': clinic,
            'service_provider': user.service_profiles.first(),
            'appointments': appointments[:10],
            'todays_appointments': todays_appointments.order_by('time'),
            'pending_count': pending.count(),
            'total_appointments': appointments.count(),
            'confirmed_count': appointments.filter(status='confirmed').count(),
            'appointments_today_count': todays_appointments.count(),
            'total_patients': unique_patients,
            'waiting_room_count': waiting_room,
            'recent_records': recent_records,
            'medicine_items': medicines[:8],
            'low_stock_count': len(low_stock_items),
            'medicine_form': medicine_form,
            'patient_record_form': patient_record_form,
        }
        return render(request, 'dashboard/vet_dashboard.html', context)

    elif user.role == 'shelter':
        animals = Animal.objects.filter(shelter=user).order_by('-intake_date')
        in_care = animals.filter(adoption_status='available')
        applications = AdoptionApplication.objects.filter(animal__shelter=user).select_related('animal').order_by('-created_at')
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        adopted_this_month = AdoptionRecord.objects.filter(shelter=user, adoption_date__gte=current_month_start).count()
        recent_intakes_qs = ShelterIntake.objects.filter(shelter=user).select_related('animal').order_by('-intake_date', '-created_at')
        new_intakes_today = recent_intakes_qs.filter(intake_date=today).count()
        pending_apps = applications.filter(status='pending')

        species_counts = {
            'dogs': in_care.filter(species='dog').count(),
            'cats': in_care.filter(species='cat').count(),
            'rabbits': in_care.filter(species='rabbit').count(),
            'others': in_care.exclude(species__in=['dog', 'cat', 'rabbit']).count(),
        }
        shelter_capacity = 100

        avg_days_raw = (AdoptionRecord.objects
                        .filter(shelter=user)
                        .values('animal__species')
                        .annotate(avg_days=Avg('days_to_adoption')))
        avg_days_map = {row['animal__species']: int(round(row['avg_days'] or 0)) for row in avg_days_raw}

        from django.db.models.functions import TruncMonth
        import json

        intake_chart = (ShelterIntake.objects
                        .filter(shelter=user)
                        .annotate(month=TruncMonth('intake_date'))
                        .values('month')
                        .annotate(count=Count('id'))
                        .order_by('month')[:6])

        adoption_chart = (AdoptionRecord.objects
                          .filter(shelter=user)
                          .annotate(month=TruncMonth('adoption_date'))
                          .values('month')
                          .annotate(count=Count('id'))
                          .order_by('month')[:6])

        intake_labels = [str(d['month'].strftime('%b %Y')) if d['month'] else '' for d in intake_chart]
        intake_counts = [d['count'] for d in intake_chart]
        adopt_counts = [d['count'] for d in adoption_chart]

        context = {
            'animals': animals,
            'service_provider': user.service_profiles.first(),
            'available_listings': in_care,
            'pending_requests': pending_apps[:10],
            'recent_intakes': recent_intakes_qs[:8],
            'total_listings': animals.count(),
            'available_count': in_care.count(),
            'adopted_count': animals.filter(adoption_status='adopted').count(),
            'animals_in_care': in_care.count(),
            'adopted_this_month': adopted_this_month,
            'pending_apps_count': pending_apps.count(),
            'new_intakes_today': new_intakes_today,
            'species_counts': species_counts,
            'shelter_capacity': shelter_capacity,
            'capacity_text': f"{in_care.count()}/{shelter_capacity}",
            'avg_days': {
                'dogs': avg_days_map.get('dog', 0),
                'cats': avg_days_map.get('cat', 0),
                'rabbits': avg_days_map.get('rabbit', 0),
                'others': avg_days_map.get('other', 0),
            },
            'intake_form': AnimalIntakeForm(),
            'intake_labels': json.dumps(intake_labels),
            'intake_counts': json.dumps(intake_counts),
            'adoption_counts': json.dumps(adopt_counts),
        }
        return render(request, 'dashboard/shelter_dashboard.html', context)

    elif user.role == 'store':
        try:
            store = user.stores.first()
        except Exception:
            store = None

        products = ProductInventory.objects.filter(store=store).select_related('supplier').order_by('-created_at') if store else ProductInventory.objects.none()
        low_stock_products = [product for product in products if product.is_low_stock and product.stock_quantity > 0]
        out_of_stock_products = products.filter(stock_quantity=0) if store else ProductInventory.objects.none()

        today = timezone.now().date()
        order_range = request.GET.get('order_range', 'today')
        orders = CustomerOrder.objects.filter(store=store).prefetch_related('items', 'items__product').order_by('-created_at') if store else CustomerOrder.objects.none()
        if order_range == 'month':
            orders = orders.filter(created_at__year=today.year, created_at__month=today.month)
        elif order_range == 'year':
            orders = orders.filter(created_at__year=today.year)
        else:
            order_range = 'today'
            orders = orders.filter(created_at__date=today)

        delivered_today = (OrderItem.objects
                           .filter(order__store=store, order__status='delivered', order__created_at__date=today)
                           .aggregate(total=Count('id'), revenue=Sum(F('quantity') * F('unit_price'))) if store else {'total': 0, 'revenue': 0})

        top_products = (OrderItem.objects
                        .filter(order__store=store, order__status='delivered')
                        .values('product__product_name', 'product__category')
                        .annotate(total_units_sold=Sum('quantity'))
                        .order_by('-total_units_sold')[:5]) if store else []

        suppliers = Supplier.objects.filter(owner=user).order_by('name')
        context = {
            'store': store,
            'service_provider': user.service_profiles.first(),
            'inventory': products,
            'inventory_count': products.count() if store else 0,
            'low_stock_count': len(low_stock_products) + (out_of_stock_products.count() if store else 0),
            'low_stock_items': low_stock_products[:6],
            'out_of_stock_items': out_of_stock_products[:4] if store else [],
            'top_products': top_products,
            'store_rating': store.rating if store else 0,
            'orders': orders[:20],
            'orders_today_count': CustomerOrder.objects.filter(store=store, created_at__date=today).count() if store else 0,
            'today_revenue': delivered_today['revenue'] or 0,
            'order_range': order_range,
            'product_form': ProductInventoryForm(),
            'suppliers': suppliers,
        }
        return render(request, 'dashboard/store_dashboard.html', context)

    elif user.role == 'provider':
        service = user.service_profiles.first()
        bookings = ServiceBooking.objects.filter(service__owner=user).select_related('pet', 'customer').order_by('-date', '-time')
        pending_bookings = bookings.filter(status='pending')
        today = timezone.now().date()
        todays_bookings = bookings.filter(date=today)

        if service and service.provider_type == 'GROOMER':
            sessions_qs = (GroomingSession.objects
                           .filter(groomer=user, service=service)
                           .select_related('pet', 'owner', 'booking')
                           .order_by('date', 'time'))
            today_sessions = list(sessions_qs.filter(date=today))
            now_time = timezone.localtime().time()

            next_marked = False
            for session in today_sessions:
                start_dt = datetime.combine(today, session.time)
                end_dt = start_dt + timedelta(minutes=session.duration_minutes)
                now_dt = datetime.combine(today, now_time)
                display_status = 'scheduled'
                if session.status == 'completed':
                    display_status = 'done'
                elif start_dt <= now_dt <= end_dt:
                    display_status = 'now'
                elif not next_marked and start_dt > now_dt:
                    display_status = 'next'
                    next_marked = True
                session.display_status = display_status

            supplies = GroomingSupply.objects.filter(groomer=user).order_by('product_name')
            low_stock_items = [item for item in supplies if item.is_low_stock and item.quantity > 0]
            out_of_stock_items = supplies.filter(quantity=0)

            care_notes = (ClientCareNote.objects
                          .filter(groomer=user)
                          .select_related('pet', 'booking')
                          .order_by('-created_at')[:8])

            monthly_rows = (sessions_qs
                            .exclude(status='cancelled')
                            .annotate(month=TruncMonth('date'))
                            .values('month')
                            .annotate(session_count=Count('id'), revenue=Sum('session_fee'))
                            .order_by('month')[:6])
            monthly_labels = [row['month'].strftime('%b %Y') if row['month'] else '' for row in monthly_rows]
            monthly_sessions = [row['session_count'] for row in monthly_rows]
            monthly_revenue = [float(row['revenue'] or 0) for row in monthly_rows]

            service_totals = {key: 0 for key, _ in ServiceBooking.GROOMING_SERVICE_CHOICES}
            for row in sessions_qs.exclude(status='cancelled').values('service_type').annotate(total=Count('id')):
                service_totals[row['service_type']] = row['total']
            total_services = sum(service_totals.values())
            service_breakdown_labels = [label for _, label in ServiceBooking.GROOMING_SERVICE_CHOICES]
            service_breakdown_values = [round((service_totals[key] / total_services) * 100, 2) if total_services else 0 for key, _ in ServiceBooking.GROOMING_SERVICE_CHOICES]
            service_breakdown_pairs = [
                {
                    'label': label,
                    'percent': round((service_totals[key] / total_services) * 100, 2) if total_services else 0,
                }
                for key, label in ServiceBooking.GROOMING_SERVICE_CHOICES
            ]

            today_revenue = (sessions_qs
                             .filter(date=today)
                             .exclude(status='cancelled')
                             .aggregate(total=Sum('session_fee'))['total'] or 0)

            context = {
                'service': service,
                'bookings': bookings[:10],
                'todays_sessions': today_sessions,
                'sessions_today': len(today_sessions),
                'currently_grooming': len([session for session in today_sessions if session.display_status == 'now']),
                'regular_clients': sessions_qs.values('owner').distinct().count() or bookings.values('customer').distinct().count(),
                'pending_count': pending_bookings.count(),
                'total_bookings': bookings.count(),
                'confirmed_count': bookings.filter(status='confirmed').count(),
                'completed_today': len([session for session in today_sessions if session.display_status == 'done']),
                'pending_requests': pending_bookings[:10],
                'today_revenue': today_revenue,
                'supplies': supplies[:12],
                'supply_count': supplies.count(),
                'low_stock_count': len(low_stock_items) + out_of_stock_items.count(),
                'low_stock_items': low_stock_items[:8],
                'out_of_stock_items': out_of_stock_items[:6],
                'care_notes': care_notes,
                'supply_form': GroomingSupplyForm(),
                'care_note_form': ClientCareNoteForm(groomer=user),
                'monthly_labels': json.dumps(monthly_labels),
                'monthly_sessions': json.dumps(monthly_sessions),
                'monthly_revenue': json.dumps(monthly_revenue),
                'service_breakdown_labels': json.dumps(service_breakdown_labels),
                'service_breakdown_values': json.dumps(service_breakdown_values),
                'service_breakdown_pairs': service_breakdown_pairs,
            }
            return render(request, 'dashboard/grooming_dashboard.html', context)

        context = {
            'service': service,
            'bookings': bookings[:10],
            'pending_count': pending_bookings.count(),
            'total_bookings': bookings.count(),
            'confirmed_count': bookings.filter(status='confirmed').count(),
        }
        return render(request, 'dashboard/provider_dashboard.html', context)

    return redirect('home')


# ─── PETS ─────────────────────────────────────────────────────────────────────

@login_required
def pet_list(request):
    if request.method == 'POST' and request.POST.get('form_type') == 'schedule_vaccine':
        form = VaccinationAppointmentForm(request.user, request.POST)
        if form.is_valid():
            vaccine_appt = form.save(commit=False)
            vaccine_appt.owner = request.user
            vaccine_appt.vet = vaccine_appt.clinic.vet
            vaccine_appt.status = 'pending'
            vaccine_appt.notification_seen = False

            linked_appt = Appointment.objects.create(
                owner=request.user,
                vet=vaccine_appt.vet,
                pet=vaccine_appt.pet,
                clinic=vaccine_appt.clinic,
                appointment_type='vaccination',
                date=vaccine_appt.date,
                time=vaccine_appt.time,
                status='pending',
                notification_seen=False,
                reason=vaccine_appt.notes,
            )
            vaccine_appt.linked_appointment = linked_appt
            vaccine_appt.save()

            VaccinationRecord.objects.create(
                owner=request.user,
                pet=vaccine_appt.pet,
                appointment=vaccine_appt,
                vaccine_name=vaccine_appt.vaccine_name,
                administered_date=vaccine_appt.date,
                next_due_date=vaccine_appt.date + timedelta(days=365),
                vet_clinic=vaccine_appt.clinic,
                notes=vaccine_appt.notes,
                status='scheduled',
            )

            for uploaded_file in request.FILES.getlist('medical_files'):
                MedicalRecordFile.objects.create(appointment=vaccine_appt, file=uploaded_file)

            messages.success(request, 'Vaccination appointment request sent to clinic dashboard.')
            return redirect('pet_list')
        messages.error(request, 'Please fill valid vaccination details.')

    pets = Pet.objects.filter(owner=request.user).prefetch_related('vaccination_records')
    today = timezone.now().date()
    due_soon_limit = today + timedelta(days=7)

    for pet in pets:
        records = list(pet.vaccination_records.all().order_by('-administered_date', '-created_at'))
        has_due_soon = False
        for record in records:
            if record.administered_date > today:
                new_status = 'scheduled'
            elif record.next_due_date and today <= record.next_due_date <= due_soon_limit:
                new_status = 'due_soon'
                has_due_soon = True
                VaccinationReminder.objects.get_or_create(
                    pet=pet,
                    reminder_type='vaccination',
                    title=f"Vaccine Due Soon: {record.vaccine_name}",
                    due_date=record.next_due_date,
                    defaults={
                        'notes': f"{pet.name} has vaccine due soon.",
                        'status': 'pending',
                    }
                )
            else:
                new_status = 'completed'

            if record.status != new_status:
                record.status = new_status
                record.save(update_fields=['status', 'updated_at'])

        pet.vaccination_records_list = records[:6]
        pet.has_due_soon = has_due_soon

    context = {
        'pets': pets,
        'vaccination_form': VaccinationAppointmentForm(user=request.user),
    }
    return render(request, 'pets/pet_list.html', context)


@login_required
def add_pet(request):
    form = PetForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        pet = form.save(commit=False)
        pet.owner = request.user
        pet.save()
        messages.success(request, f"{pet.name} added! 🐾")
        return redirect('pet_detail', pk=pet.pk)
    return render(request, 'pets/add_pet.html', {'form': form})


@login_required
def pet_detail(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    health_records = pet.health_records.all()[:5]
    reminders = pet.reminders.all()[:5]
    appointments = pet.appointments.all()[:5]
    record_form = HealthRecordForm()
    reminder_form = VaccinationReminderForm()

    if request.method == 'POST':
        if 'add_record' in request.POST:
            record_form = HealthRecordForm(request.POST, request.FILES)
            if record_form.is_valid():
                rec = record_form.save(commit=False)
                rec.pet = pet
                rec.save()
                messages.success(request, "Health record added!")
                return redirect('pet_detail', pk=pk)
        elif 'add_reminder' in request.POST:
            reminder_form = VaccinationReminderForm(request.POST)
            if reminder_form.is_valid():
                rem = reminder_form.save(commit=False)
                rem.pet = pet
                rem.save()
                messages.success(request, "Reminder set!")
                return redirect('pet_detail', pk=pk)

    return render(request, 'pets/pet_detail.html', {
        'pet': pet,
        'health_records': health_records,
        'reminders': reminders,
        'appointments': appointments,
        'record_form': record_form,
        'reminder_form': reminder_form,
    })


@login_required
def edit_pet(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    form = PetForm(request.POST or None, request.FILES or None, instance=pet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Pet profile updated!")
        return redirect('pet_detail', pk=pk)
    return render(request, 'pets/add_pet.html', {'form': form, 'edit': True, 'pet': pet})


@login_required
def delete_pet(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owner=request.user)
    if request.method == 'POST':
        pet.delete()
        messages.success(request, "Pet removed.")
    return redirect('pet_list')


# ─── APPOINTMENTS ─────────────────────────────────────────────────────────────

@login_required
def appointments(request):
    if request.user.role == 'owner':
        appts = Appointment.objects.filter(owner=request.user)
    elif request.user.role == 'vet':
        appts = Appointment.objects.filter(vet=request.user)
    else:
        appts = Appointment.objects.none()
    clinics = VetClinic.objects.all()
    return render(request, 'appointments/appointments.html', {'appointments': appts, 'clinics': clinics})


@login_required
def book_appointment(request):
    form = AppointmentForm(user=request.user, data=request.POST or None)
    clinics = VetClinic.objects.all()
    if request.method == 'POST' and form.is_valid():
        appt = form.save(commit=False)
        appt.owner = request.user
        vet = appt.vet
        try:
            appt.clinic = vet.clinic
        except Exception:
            pass
        appt.status = 'pending'
        appt.notification_seen = False
        appt.save()
        clinic_name = appt.clinic.clinic_name if appt.clinic else f"Dr. {vet.get_full_name() or vet.username}"
        messages.success(request, f"Appointment request sent to {clinic_name}. The clinic will confirm shortly.")
        return redirect('appointments')
    return render(request, 'appointments/book_appointment.html', {'form': form, 'clinics': clinics})


@login_required
def update_appointment_status(request, pk, status):
    appt = get_object_or_404(Appointment, pk=pk, vet=request.user)
    if status in ['confirmed', 'completed', 'cancelled']:
        appt.status = status
        appt.notification_seen = True
        appt.save()

        if hasattr(appt, 'vaccination_request'):
            vaccination_request = appt.vaccination_request
            if status == 'confirmed':
                vaccination_request.status = 'confirmed'
            elif status == 'completed':
                vaccination_request.status = 'completed'
            elif status == 'cancelled':
                vaccination_request.status = 'cancelled'
            vaccination_request.notification_seen = True
            vaccination_request.save(update_fields=['status', 'notification_seen', 'updated_at'])

            if status == 'completed':
                VaccinationRecord.objects.filter(appointment=vaccination_request).update(status='completed')
        messages.success(request, f"Appointment {status}.")
    return redirect('dashboard')


@login_required
def reschedule_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, vet=request.user)
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')
        try:
            appt.date = new_date
            appt.time = new_time
            appt.status = 'confirmed'
            appt.notification_seen = True
            appt.save(update_fields=['date', 'time', 'status', 'notification_seen'])

            if hasattr(appt, 'vaccination_request'):
                vaccination_request = appt.vaccination_request
                vaccination_request.date = appt.date
                vaccination_request.time = appt.time
                vaccination_request.status = 'rescheduled'
                vaccination_request.notification_seen = True
                vaccination_request.save(update_fields=['date', 'time', 'status', 'notification_seen', 'updated_at'])

                VaccinationRecord.objects.filter(appointment=vaccination_request).update(
                    administered_date=appt.date,
                    next_due_date=appt.date + timedelta(days=365),
                    status='scheduled',
                    updated_at=timezone.now(),
                )

            messages.success(request, 'Appointment rescheduled successfully.')
        except Exception:
            messages.error(request, 'Invalid reschedule date/time.')

    return redirect('dashboard')


@login_required
def next_booking_request(request):
    if request.user.role != 'vet':
        return JsonResponse({'found': False}, status=403)

    appt = (Appointment.objects
            .select_related('pet', 'clinic', 'owner')
            .filter(vet=request.user, status='pending', notification_seen=False)
            .order_by('-created_at')
            .first())

    if not appt:
        return JsonResponse({'found': False})

    return JsonResponse({
        'found': True,
        'id': appt.id,
        'pet_name': appt.pet.name,
        'owner_name': appt.owner.get_full_name() or appt.owner.username,
        'clinic_name': appt.clinic.clinic_name if appt.clinic else f"Dr. {request.user.get_full_name() or request.user.username}",
        'date': appt.date.strftime('%b %d, %Y'),
        'time': appt.time.strftime('%I:%M %p').lstrip('0'),
        'reason': appt.reason or 'General checkup',
    })


@login_required
def keep_waiting_booking_request(request, pk):
    if request.user.role != 'vet':
        return JsonResponse({'ok': False}, status=403)

    appt = get_object_or_404(Appointment, pk=pk, vet=request.user, status='pending')
    appt.notification_seen = True
    appt.save(update_fields=['notification_seen'])
    return JsonResponse({'ok': True})


@login_required
def add_medicine_stock(request):
    if request.user.role != 'vet':
        return redirect('dashboard')

    if request.method == 'POST':
        form = MedicineInventoryForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.vet = request.user
            medicine.clinic = getattr(request.user, 'clinic', None)
            medicine.save()
            messages.success(request, 'Medicine stock added successfully.')
        else:
            messages.error(request, 'Please provide valid medicine details.')
    return redirect('dashboard')


@login_required
def reorder_supplies_preview(request):
    if request.user.role != 'vet':
        return JsonResponse({'ok': False}, status=403)

    try:
        medicine_id = int(request.GET.get('medicine_id', '0'))
        quantity = int(request.GET.get('quantity', '0'))
        medicine = get_object_or_404(MedicineInventory, pk=medicine_id, vet=request.user)
        quantity = max(quantity, 0)
        total = Decimal(quantity) * medicine.price_per_unit
        return JsonResponse({
            'ok': True,
            'medicine_name': medicine.medicine_name,
            'price_per_unit': str(medicine.price_per_unit),
            'quantity': quantity,
            'total_price': str(total),
        })
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
def reorder_supplies_confirm(request):
    if request.user.role != 'vet':
        return redirect('dashboard')

    if request.method == 'POST':
        medicine = get_object_or_404(MedicineInventory, pk=request.POST.get('medicine_id'), vet=request.user)
        quantity = int(request.POST.get('quantity', '0') or 0)
        supplier_shop = request.POST.get('supplier_shop', '').strip() or medicine.supplier_shop or 'Default Supplier'
        if quantity <= 0:
            messages.error(request, 'Reorder quantity must be greater than zero.')
            return redirect('dashboard')

        total = Decimal(quantity) * medicine.price_per_unit
        SupplyOrder.objects.create(
            vet=request.user,
            clinic=getattr(request.user, 'clinic', None),
            medicine=medicine,
            supplier_shop=supplier_shop,
            quantity=quantity,
            price_per_unit=medicine.price_per_unit,
            total_price=total,
            status='ordered',
        )
        medicine.quantity = medicine.quantity + quantity
        medicine.save(update_fields=['quantity', 'updated_at'])
        messages.success(request, f'Reorder placed successfully. Final bill: ₹{total}')
    return redirect('dashboard')


@login_required
def add_patient_record(request):
    if request.user.role != 'vet':
        return redirect('dashboard')

    if request.method == 'POST':
        form = VetPatientRecordForm(request.user, request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.vet = request.user
            if not record.title:
                record.title = f"Visit - {record.date.strftime('%b %d, %Y')}"
            record.save()
            messages.success(request, 'Patient record saved successfully.')
        else:
            messages.error(request, 'Please provide valid patient record details.')
    return redirect('dashboard')


@login_required
def all_patient_records(request):
    if request.user.role != 'vet':
        return redirect('dashboard')

    records = HealthRecord.objects.filter(vet=request.user).select_related('pet', 'pet__owner').order_by('-date', '-created_at')
    return render(request, 'dashboard/all_patient_records.html', {'records': records})


# ─── ADOPTION ─────────────────────────────────────────────────────────────────

def adoption(request):
    species_filter = request.GET.get('species', '')
    listings = Animal.objects.filter(adoption_status='available')
    if species_filter:
        listings = listings.filter(species__icontains=species_filter)
    return render(request, 'adoption/adoption.html', {'listings': listings, 'species_filter': species_filter})


@login_required
def adoption_request(request, pk):
    listing = get_object_or_404(Animal, pk=pk, adoption_status='available')
    if request.user == listing.shelter:
        messages.error(request, "You can't adopt your own listing.")
        return redirect('adoption')
    existing = AdoptionApplication.objects.filter(animal=listing, applicant=request.user).first()
    form = AdoptionApplicationForm(request.POST or None, initial={
        'applicant_name': request.user.get_full_name() or request.user.username,
        'contact_info': request.user.email or request.user.phone,
    })
    if request.method == 'POST' and form.is_valid() and not existing:
        req = form.save(commit=False)
        req.animal = listing
        req.applicant = request.user
        req.save()
        messages.success(request, "Adoption request submitted! 🐾")
        return redirect('adoption')
    return render(request, 'adoption/adoption_request.html', {
        'listing': listing, 'form': form, 'existing': existing
    })


@login_required
def manage_adoption_request(request, pk, action):
    req = get_object_or_404(AdoptionApplication, pk=pk, animal__shelter=request.user)
    if action == 'approve':
        req.status = 'approved'
        req.animal.adoption_status = 'adopted'
        req.animal.adopted_at = timezone.now().date()
        req.animal.save()

        AdoptionApplication.objects.filter(animal=req.animal, status='pending').exclude(pk=req.pk).update(status='denied')

        days_to_adoption = max((req.animal.adopted_at - req.animal.intake_date).days, 0)
        AdoptionRecord.objects.get_or_create(
            shelter=request.user,
            animal=req.animal,
            application=req,
            defaults={
                'adopter_name': req.applicant_name,
                'adoption_date': req.animal.adopted_at,
                'days_to_adoption': days_to_adoption,
            }
        )
        messages.success(request, f"Adoption approved for {req.applicant_name}!")
    elif action in ['reject', 'deny']:
        req.status = 'denied'
    req.save()
    return redirect('dashboard')


@login_required
def view_all_applications(request):
    if request.user.role != 'shelter':
        return redirect('dashboard')

    status_filter = request.GET.get('status', '').strip().lower()
    applications = AdoptionApplication.objects.filter(animal__shelter=request.user).select_related('animal').order_by('-created_at')
    if status_filter in ['pending', 'approved', 'denied']:
        applications = applications.filter(status=status_filter)

    return render(request, 'dashboard/all_applications.html', {
        'applications': applications,
        'status_filter': status_filter,
    })


@login_required
def log_shelter_intake(request):
    if request.user.role != 'shelter':
        return redirect('dashboard')

    form = AnimalIntakeForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        animal = form.save(commit=False)
        animal.shelter = request.user
        animal.adoption_status = 'available'
        animal.save()

        ShelterIntake.objects.create(
            shelter=request.user,
            animal=animal,
            intake_date=animal.intake_date,
            rescue_location=animal.rescue_location,
            health_status=animal.health_status,
            vaccination_status=animal.vaccination_status,
        )
        messages.success(request, 'New intake logged successfully.')

    return redirect('dashboard')


@login_required
def add_adoption_listing(request):
    if request.user.role != 'shelter':
        messages.error(request, "Only shelters can add adoption listings.")
        return redirect('adoption')
    form = AdoptionListingForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        listing = form.save(commit=False)
        listing.shelter = request.user
        listing.save()
        messages.success(request, "Adoption listing added!")
        return redirect('dashboard')
    return render(request, 'adoption/add_listing.html', {'form': form})


# ─── LOST & FOUND ─────────────────────────────────────────────────────────────

def lost_found(request):
    filter_type = request.GET.get('type', '')
    reports = LostPetReport.objects.filter(is_resolved=False)
    if filter_type:
        reports = reports.filter(report_type=filter_type)
    return render(request, 'lost_found/lost_found.html', {'reports': reports, 'filter_type': filter_type})


@login_required
def report_lost_found(request):
    form = LostPetReportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.save()

        alert_text = f"{report.pet_name or report.species} has been reported as {report.report_type.upper()} in {report.location}. Please help!"
        SocialPost.objects.create(
            author=request.user,
            content=alert_text,
            photo=report.photo,
            lost_found_report=report,
        )

        messages.success(request, "Report submitted! We hope your pet is found safe. 🐾")
        return redirect('lost_found')
    return render(request, 'lost_found/report.html', {'form': form})


@login_required
def mark_resolved(request, pk):
    report = get_object_or_404(LostPetReport, pk=pk, reporter=request.user)
    report.is_resolved = True
    report.save()
    messages.success(request, "Marked as resolved!")
    return redirect('lost_found')


# ─── COMMUNITY ────────────────────────────────────────────────────────────────

@login_required
def community(request):
    posts = SocialPost.objects.select_related('author', 'pet', 'lost_found_report').prefetch_related('likes', 'comments')
    post_form = SocialPostForm(user=request.user)
    comment_form = CommentForm()
    if request.method == 'POST':
        if 'post_content' in request.POST:
            post_form = SocialPostForm(request.user, request.POST, request.FILES)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.author = request.user
                post.save()
                messages.success(request, "Posted! 🐾")
                return redirect('community')
    return render(request, 'community/community.html', {
        'posts': posts, 'post_form': post_form, 'comment_form': comment_form
    })


@login_required
def like_post(request, pk):
    post = get_object_or_404(SocialPost, pk=pk)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    return JsonResponse({'likes': post.like_count(), 'liked': created})


@login_required
def comment_post(request, pk):
    post = get_object_or_404(SocialPost, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.post = post
            c.author = request.user
            c.save()
    return redirect('community')


@login_required
def delete_post(request, pk):
    post = get_object_or_404(SocialPost, pk=pk, author=request.user)
    post.delete()
    return redirect('community')


# ─── STORES ───────────────────────────────────────────────────────────────────

@login_required
def stores(request):
    if request.user.role != 'owner':
        messages.error(request, 'Pet Stores is available for Pet Owner accounts only.')
        return redirect('dashboard')
    return render(request, 'stores.html')


@login_required
def api_stores(request):
    if request.user.role != 'owner':
        return JsonResponse({'error': 'forbidden'}, status=403)

    city = (request.GET.get('city', '') or '').strip()
    if not city:
        return JsonResponse([], safe=False)

    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': f'pet store {city}',
                'format': 'json',
                'limit': 200,
            },
            headers={'User-Agent': 'fluffbud-app'},
            timeout=10,
        )
        response.raise_for_status()
        raw_results = response.json() or []
    except Exception:
        return JsonResponse({'error': 'api_failed'}, status=502)

    payload = []
    for item in raw_results:
        display_name = item.get('display_name', '')
        name = (display_name.split(',')[0].strip() if display_name else 'Pet Store')
        payload.append({
            'name': name,
            'rating': '4.5',
            'address': display_name,
            'distance': '',
            'lat': item.get('lat', ''),
            'lon': item.get('lon', ''),
        })

    return JsonResponse(payload, safe=False)


@login_required
def manage_store(request):
    if request.user.role != 'store':
        return redirect('dashboard')
    store = request.user.stores.first()
    form = PetStoreForm(request.POST or None, request.FILES or None, instance=store)
    if request.method == 'POST' and form.is_valid():
        s = form.save(commit=False)
        s.owner = request.user
        s.save()
        messages.success(request, "Store profile updated!")
        return redirect('dashboard')
    return render(request, 'stores/manage_store.html', {'form': form, 'store': store})


@login_required
def add_inventory(request):
    if request.user.role != 'store':
        return redirect('dashboard')
    store = request.user.stores.first()
    if not store:
        messages.error(request, "Please set up your store first.")
        return redirect('manage_store')
    form = InventoryItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.store = store
        item.save()
        messages.success(request, "Item added to inventory!")
        return redirect('dashboard')
    return render(request, 'stores/add_inventory.html', {'form': form, 'store': store})


@login_required
def add_product_inventory(request):
    if request.user.role != 'store':
        return redirect('dashboard')

    store = request.user.stores.first()
    if not store:
        messages.error(request, "Please set up your store first.")
        return redirect('manage_store')

    form = ProductInventoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        supplier_name = form.cleaned_data['supplier_shop'].strip()
        supplier, _ = Supplier.objects.get_or_create(owner=request.user, name=supplier_name)
        ProductInventory.objects.create(
            store=store,
            product_name=form.cleaned_data['product_name'],
            category=form.cleaned_data['category'],
            stock_quantity=form.cleaned_data['quantity'],
            unit_type=form.cleaned_data['unit_type'],
            price_per_unit=form.cleaned_data['price_per_unit'],
            supplier=supplier,
        )
        messages.success(request, "Product added to inventory successfully.")
    elif request.method == 'POST':
        messages.error(request, "Please provide valid product details.")
    return redirect('dashboard')


@login_required
def reorder_low_stock_preview(request):
    if request.user.role != 'store':
        return JsonResponse({'ok': False}, status=403)

    try:
        product_id = int(request.GET.get('product_id', '0'))
        quantity = int(request.GET.get('quantity', '0'))
        product = get_object_or_404(ProductInventory, pk=product_id, store__owner=request.user)
        quantity = max(quantity, 0)
        total = Decimal(quantity) * product.price_per_unit
        return JsonResponse({
            'ok': True,
            'product_name': product.product_name,
            'price_per_unit': str(product.price_per_unit),
            'quantity': quantity,
            'total_price': str(total),
        })
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
def reorder_low_stock_confirm(request):
    if request.user.role != 'store':
        return redirect('dashboard')

    if request.method == 'POST':
        product = get_object_or_404(ProductInventory, pk=request.POST.get('product_id'), store__owner=request.user)
        form = AutoReorderForm(request.POST)
        if form.is_valid():
            supplier_name = form.cleaned_data['supplier_shop'].strip()
            quantity = form.cleaned_data['quantity']
            supplier, _ = Supplier.objects.get_or_create(owner=request.user, name=supplier_name)
            product.supplier = supplier
            product.stock_quantity += quantity
            product.save(update_fields=['supplier', 'stock_quantity', 'updated_at'])
            total = Decimal(quantity) * product.price_per_unit
            messages.success(request, f"Auto-reorder placed. Total price: ₹{total}")
        else:
            messages.error(request, "Please provide valid reorder details.")
    return redirect('dashboard')


@login_required
def store_orders_api(request):
    if request.user.role != 'store':
        return JsonResponse({'ok': False}, status=403)
    store = request.user.stores.first()
    if not store:
        return JsonResponse({'ok': True, 'orders': []})

    today = timezone.now().date()
    order_range = request.GET.get('range', 'today')
    orders = CustomerOrder.objects.filter(store=store).prefetch_related('items', 'items__product').order_by('-created_at')
    if order_range == 'month':
        orders = orders.filter(created_at__year=today.year, created_at__month=today.month)
    elif order_range == 'year':
        orders = orders.filter(created_at__year=today.year)
    else:
        orders = orders.filter(created_at__date=today)

    payload = []
    for order in orders[:100]:
        payload.append({
            'order_id': order.id,
            'customer_name': order.customer_name,
            'order_source': order.get_order_source_display(),
            'status': order.get_status_display(),
            'products': [
                {
                    'name': item.product.product_name,
                    'quantity': item.quantity,
                }
                for item in order.items.all()
            ],
        })
    return JsonResponse({'ok': True, 'orders': payload})


@login_required
def store_analytics_api(request):
    if request.user.role != 'store':
        return JsonResponse({'ok': False}, status=403)
    store = request.user.stores.first()
    if not store:
        return JsonResponse({'ok': True, 'weekly_revenue': [], 'category_percentages': {}})

    today = timezone.now().date()
    last_week = [today - timedelta(days=delta) for delta in range(6, -1, -1)]
    weekly_revenue = []
    for day in last_week:
        day_total = (OrderItem.objects
                     .filter(order__store=store, order__status='delivered', order__created_at__date=day)
                     .aggregate(revenue=Sum(F('quantity') * F('unit_price')))['revenue'] or 0)
        weekly_revenue.append({'day': day.strftime('%a'), 'revenue': float(day_total)})

    category_counts = (OrderItem.objects
                       .filter(order__store=store, order__status='delivered')
                       .values('pet_category')
                       .annotate(total=Sum('quantity')))

    totals = {'cat': 0, 'dog': 0, 'rabbit': 0, 'small_pets': 0}
    grand_total = 0
    for row in category_counts:
        key = row['pet_category']
        qty = row['total'] or 0
        if key in totals:
            totals[key] += qty
            grand_total += qty
    percentages = {}
    for key, qty in totals.items():
        percentages[key] = round((qty / grand_total) * 100, 2) if grand_total else 0

    return JsonResponse({'ok': True, 'weekly_revenue': weekly_revenue, 'category_percentages': percentages})


@login_required
def delete_inventory(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, store__owner=request.user)
    item.delete()
    messages.success(request, "Item removed.")
    return redirect('dashboard')


# ─── SERVICE PROVIDERS ────────────────────────────────────────────────────────

def services(request):
    city = request.GET.get('city', '')
    category = request.GET.get('category', '')
    all_services = ServiceProvider.objects.filter(is_active=True)
    if city:
        all_services = all_services.filter(city__icontains=city)
    if category:
        all_services = all_services.filter(provider_type=category)
    categories = ServiceProvider.PROVIDER_TYPE_CHOICES
    return render(request, 'services/services.html', {
        'services': all_services,
        'city': city,
        'category': category,
        'categories': categories,
    })


@login_required
def manage_service(request):
    if request.user.role != 'provider':
        return redirect('dashboard')
    service = request.user.service_profiles.first()
    form = ServiceProviderForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        s = form.save(commit=False)
        s.owner = request.user
        if 'provider_id_file' in request.FILES:
            s.is_verified = True
        s.save()
        messages.success(request, "Service profile updated!")
        return redirect('dashboard')
    return render(request, 'services/manage_service.html', {'form': form, 'service': service})


@login_required
def book_service(request, pk):
    service = get_object_or_404(ServiceProvider, pk=pk, is_active=True)
    form = ServiceBookingForm(user=request.user, service=service, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.customer = request.user
        booking.service = service
        booking.notification_seen = False
        booking.save()
        messages.success(request, f"Booking requested with {service.name}! 🐾")
        return redirect('services')
    return render(request, 'services/book_service.html', {'form': form, 'service': service})


@login_required
def update_service_booking(request, pk, status):
    booking = get_object_or_404(ServiceBooking, pk=pk, service__owner=request.user)
    if status in ['confirmed', 'completed', 'cancelled']:
        booking.status = status
        booking.save()
        if booking.service.provider_type == 'GROOMER':
            fee_default = Decimal('0')
            GroomingSession.objects.update_or_create(
                booking=booking,
                defaults={
                    'groomer': request.user,
                    'service': booking.service,
                    'pet': booking.pet,
                    'owner': booking.customer,
                    'service_type': booking.service_type,
                    'date': booking.date,
                    'time': booking.time,
                    'duration_minutes': booking.duration_minutes,
                    'special_notes': booking.notes,
                    'session_fee': fee_default,
                    'status': 'completed' if status == 'completed' else ('cancelled' if status == 'cancelled' else 'scheduled'),
                }
            )
        messages.success(request, f"Booking {status}.")
    return redirect('dashboard')


@login_required
def keep_waiting_grooming_booking(request, pk):
    if request.user.role != 'provider':
        return JsonResponse({'ok': False}, status=403)

    booking = get_object_or_404(
        ServiceBooking,
        pk=pk,
        service__owner=request.user,
        service__provider_type='GROOMER',
        status='pending',
    )
    booking.notification_seen = True
    booking.save(update_fields=['notification_seen'])
    return JsonResponse({'ok': True})


@login_required
def accept_grooming_booking(request, pk):
    if request.user.role != 'provider':
        return redirect('dashboard')

    booking = get_object_or_404(
        ServiceBooking,
        pk=pk,
        service__owner=request.user,
        service__provider_type='GROOMER',
        status='pending',
    )
    booking.status = 'confirmed'
    booking.notification_seen = True
    booking.save(update_fields=['status', 'notification_seen'])

    GroomingSession.objects.update_or_create(
        booking=booking,
        defaults={
            'groomer': request.user,
            'service': booking.service,
            'pet': booking.pet,
            'owner': booking.customer,
            'service_type': booking.service_type,
            'date': booking.date,
            'time': booking.time,
            'duration_minutes': booking.duration_minutes,
            'special_notes': booking.notes,
            'session_fee': Decimal('0'),
            'status': 'scheduled',
        }
    )
    messages.success(request, 'Grooming session accepted and added to today\'s sessions.')
    return redirect('dashboard')


@login_required
def reschedule_grooming_booking(request, pk):
    if request.user.role != 'provider':
        return redirect('dashboard')

    booking = get_object_or_404(
        ServiceBooking,
        pk=pk,
        service__owner=request.user,
        service__provider_type='GROOMER',
        status='pending',
    )

    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')
        try:
            booking.date = new_date
            booking.time = new_time
            booking.status = 'confirmed'
            booking.notification_seen = True
            booking.save(update_fields=['date', 'time', 'status', 'notification_seen'])

            GroomingSession.objects.update_or_create(
                booking=booking,
                defaults={
                    'groomer': request.user,
                    'service': booking.service,
                    'pet': booking.pet,
                    'owner': booking.customer,
                    'service_type': booking.service_type,
                    'date': booking.date,
                    'time': booking.time,
                    'duration_minutes': booking.duration_minutes,
                    'special_notes': booking.notes,
                    'session_fee': Decimal('0'),
                    'status': 'scheduled',
                }
            )
            messages.success(request, 'Session rescheduled successfully.')
        except Exception:
            messages.error(request, 'Please provide a valid date and time.')
    return redirect('dashboard')


@login_required
def add_grooming_supply(request):
    if request.user.role != 'provider':
        return redirect('dashboard')

    service = request.user.service_profiles.filter(provider_type='GROOMER').first()
    if not service:
        return redirect('dashboard')

    if request.method == 'POST':
        form = GroomingSupplyForm(request.POST)
        if form.is_valid():
            supply = form.save(commit=False)
            supply.groomer = request.user
            supply.service = service
            supply.save()
            messages.success(request, 'Supply item added successfully.')
        else:
            messages.error(request, 'Please provide valid supply details.')
    return redirect('dashboard')


@login_required
def reorder_grooming_supplies_preview(request):
    if request.user.role != 'provider':
        return JsonResponse({'ok': False}, status=403)

    try:
        supply_id = int(request.GET.get('supply_id', '0'))
        quantity = int(request.GET.get('quantity', '0'))
        supply = get_object_or_404(GroomingSupply, pk=supply_id, groomer=request.user)
        quantity = max(quantity, 0)
        total = Decimal(quantity) * supply.price_per_unit
        return JsonResponse({
            'ok': True,
            'product_name': supply.product_name,
            'price_per_unit': str(supply.price_per_unit),
            'quantity': quantity,
            'total_price': str(total),
        })
    except Exception:
        return JsonResponse({'ok': False}, status=400)


@login_required
def reorder_grooming_supplies_confirm(request):
    if request.user.role != 'provider':
        return redirect('dashboard')

    if request.method == 'POST':
        supply = get_object_or_404(GroomingSupply, pk=request.POST.get('supply_id'), groomer=request.user)
        quantity = int(request.POST.get('quantity', '0') or 0)
        supplier_name = (request.POST.get('supplier', '').strip() or supply.supplier or 'Default Supplier')
        if quantity <= 0:
            messages.error(request, 'Reorder quantity must be greater than zero.')
            return redirect('dashboard')

        total = Decimal(quantity) * supply.price_per_unit
        GroomingSupplyOrder.objects.create(
            groomer=request.user,
            service=supply.service,
            supply=supply,
            supplier=supplier_name,
            quantity=quantity,
            price_per_unit=supply.price_per_unit,
            total_price=total,
            status='ordered',
        )
        supply.quantity = supply.quantity + quantity
        supply.supplier = supplier_name
        supply.save(update_fields=['quantity', 'supplier', 'updated_at'])
        messages.success(request, f'Auto-reorder placed. Total cost: ₹{total}')
    return redirect('dashboard')


@login_required
def add_client_care_note(request):
    if request.user.role != 'provider':
        return redirect('dashboard')

    service = request.user.service_profiles.filter(provider_type='GROOMER').first()
    if not service:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ClientCareNoteForm(request.user, request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.groomer = request.user
            note.service = service
            note.save()
            messages.success(request, 'Client care note added.')
        else:
            messages.error(request, 'Please provide valid note details.')
    return redirect('dashboard')


# ─── VET CLINIC ───────────────────────────────────────────────────────────────

@login_required
def manage_clinic(request):
    if request.user.role != 'vet':
        return redirect('dashboard')
    clinic = getattr(request.user, 'clinic', None)
    form = VetClinicForm(request.POST or None, request.FILES or None, instance=clinic)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.vet = request.user
        c.save()
        messages.success(request, "Clinic profile updated!")
        return redirect('dashboard')
    return render(request, 'dashboard/manage_clinic.html', {'form': form, 'clinic': clinic})


# ─── EMERGENCY SOS ────────────────────────────────────────────────────────────

def emergency(request):
    emergency_clinics = VetClinic.objects.filter(is_emergency=True)
    all_clinics = VetClinic.objects.all()[:6]
    return render(request, 'emergency.html', {
        'emergency_clinics': emergency_clinics,
        'all_clinics': all_clinics
    })


# ─── SERVICE PROVIDER PORTAL ─────────────────────────────────────────────────

@login_required
def provider_portal(request):
    if request.method == 'POST':
        provider_type = request.POST.get('provider_type', '')
        role_map = {
            'vet': 'vet',
            'shelter': 'shelter',
            'store': 'store',
            'groomer': 'provider',
        }
        new_role = role_map.get(provider_type)
        if new_role:
            user = request.user
            user.role = new_role
            full_name = request.POST.get('full_name', '').strip()
            if full_name:
                parts = full_name.split(None, 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
            email = request.POST.get('email', '').strip()
            if email:
                user.email = email
            user.save()
            messages.success(request, f"Welcome to PawNest as a {provider_type.title()}! 🛠️")
            return redirect('dashboard')
        messages.error(request, "Please select a provider type.")
    return redirect('dashboard')


# ─── ANALYTICS ────────────────────────────────────────────────────────────────

@login_required
def analytics(request):
    if not request.user.is_service_provider() and not request.user.is_staff:
        return redirect('dashboard')

    from django.db.models.functions import TruncMonth
    import json

    appt_data = (Appointment.objects
                 .annotate(month=TruncMonth('date'))
                 .values('month')
                 .annotate(count=Count('id'))
                 .order_by('month')[:6])

    adoption_data = (AdoptionListing.objects
                     .annotate(month=TruncMonth('created_at'))
                     .values('month')
                     .annotate(count=Count('id'))
                     .order_by('month')[:6])

    if request.user.role == 'shelter':
        appt_data = (ShelterIntake.objects
                     .filter(shelter=request.user)
                     .annotate(month=TruncMonth('intake_date'))
                     .values('month')
                     .annotate(count=Count('id'))
                     .order_by('month')[:6])

        adoption_data = (AdoptionRecord.objects
                         .filter(shelter=request.user)
                         .annotate(month=TruncMonth('adoption_date'))
                         .values('month')
                         .annotate(count=Count('id'))
                         .order_by('month')[:6])

    health_issues = (HealthRecord.objects
                     .values('diagnosis')
                     .annotate(count=Count('id'))
                     .order_by('-count')[:5])

    service_labels = ['Checkups', 'Vaccinations', 'Surgery', 'Dental', 'Other']
    service_counts = [0, 0, 0, 0, 0]

    if request.user.role == 'vet':
        appt_qs = Appointment.objects.filter(vet=request.user)
        appt_data = (appt_qs
                     .annotate(month=TruncMonth('date'))
                     .values('month')
                     .annotate(count=Count('id'))
                     .order_by('month')[:6])

        total_appts = appt_qs.count() or 1
        checkup_count = appt_qs.filter(appointment_type='checkup').count()
        vaccine_count = appt_qs.filter(appointment_type='vaccination').count()
        surgery_count = appt_qs.filter(appointment_type='surgery').count()
        dental_count = appt_qs.filter(appointment_type='dental').count()
        other_count = max(total_appts - (checkup_count + vaccine_count + surgery_count + dental_count), 0)

        service_counts = [
            round((checkup_count / total_appts) * 100),
            round((vaccine_count / total_appts) * 100),
            round((surgery_count / total_appts) * 100),
            round((dental_count / total_appts) * 100),
            round((other_count / total_appts) * 100),
        ]

    appt_labels = [str(d['month'].strftime('%b %Y')) if d['month'] else '' for d in appt_data]
    appt_counts = [d['count'] for d in appt_data]
    adopt_labels = [str(d['month'].strftime('%b %Y')) if d['month'] else '' for d in adoption_data]
    adopt_counts = [d['count'] for d in adoption_data]

    context = {
        'appt_labels': json.dumps(appt_labels),
        'appt_counts': json.dumps(appt_counts),
        'adopt_labels': json.dumps(adopt_labels),
        'adopt_counts': json.dumps(adopt_counts),
        'service_labels': json.dumps(service_labels),
        'service_counts': json.dumps(service_counts),
        'health_issues': health_issues,
        'total_users': CustomUser.objects.count(),
        'total_pets': Pet.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'total_adoptions': AdoptionListing.objects.filter(status='adopted').count(),
    }
    return render(request, 'dashboard/analytics.html', context)


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'personal_info':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            user.city = request.POST.get('city', '').strip()
            user.bio = request.POST.get('bio', '').strip()
            user.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
        elif request.FILES.get('profile_photo'):
            user.profile_photo = request.FILES['profile_photo']
            user.save()
            messages.success(request, 'Avatar updated!')
            return redirect('profile')
    pets = Pet.objects.filter(owner=user)
    role_map = dict(CustomUser.ROLE_CHOICES)
    context = {
        'profile_user': user,
        'pets': pets,
        'role_display': role_map.get(user.role, 'Pet Owner'),
    }
    return render(request, 'profile.html', context)


@login_required
def settings(request):
    return render(request, 'settings.html')


@login_required
def notifications(request):
    return render(request, 'notifications.html')

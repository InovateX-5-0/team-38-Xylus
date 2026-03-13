from datetime import timedelta
from decimal import Decimal
from itertools import cycle

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from myapp.models import (
    Appointment,
    CustomUser,
    MedicalRecordFile,
    Pet,
    VaccinationAppointment,
    VaccinationRecord,
    VaccinationReminder,
    VetClinic,
)


class Command(BaseCommand):
    help = "Seed sample vaccination data for dashboard/demo usage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously seeded vaccination sample data before re-seeding",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=3,
            help="Number of vaccination sample bundles to create (default: 3)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options["reset"]
        requested_count = max(options.get("count", 3), 1)

        if reset:
            self._clear_seed_data()

        owner = self._get_or_create_owner()
        vet, clinic = self._get_or_create_vet_and_clinic()
        pets = self._get_or_create_pets(owner)

        created_count = 0
        today = timezone.now().date()
        sample_rows = self._build_sample_rows(pets, today, requested_count)

        for row in sample_rows:
            if VaccinationAppointment.objects.filter(
                owner=owner,
                pet=row["pet"],
                vaccine_name=row["vaccine"],
                notes=row["notes"],
            ).exists():
                continue

            linked_appointment = Appointment.objects.create(
                owner=owner,
                vet=vet,
                pet=row["pet"],
                clinic=clinic,
                appointment_type="vaccination",
                date=row["date"],
                time=row["time"],
                status=row["status"] if row["status"] in ["pending", "confirmed", "completed", "cancelled"] else "pending",
                notification_seen=row["status"] != "pending",
                reason=row["notes"],
            )

            vaccination_appt = VaccinationAppointment.objects.create(
                owner=owner,
                pet=row["pet"],
                vet=vet,
                clinic=clinic,
                linked_appointment=linked_appointment,
                vaccine_name=row["vaccine"],
                date=row["date"],
                time=row["time"],
                notes=row["notes"],
                status=(
                    "completed"
                    if row["status"] == "completed"
                    else ("confirmed" if row["status"] == "confirmed" else "pending")
                ),
                notification_seen=row["status"] != "pending",
            )

            record_status = "scheduled"
            if row["date"] > today:
                record_status = "scheduled"
            elif row["next_due"] and row["next_due"] <= today + timedelta(days=7):
                record_status = "due_soon"
            else:
                record_status = "completed"

            VaccinationRecord.objects.create(
                owner=owner,
                pet=row["pet"],
                appointment=vaccination_appt,
                vaccine_name=row["vaccine"],
                administered_date=row["date"],
                next_due_date=row["next_due"],
                vet_clinic=clinic,
                notes=row["notes"],
                status=record_status,
            )

            if row["next_due"] and row["next_due"] <= today + timedelta(days=7):
                VaccinationReminder.objects.get_or_create(
                    pet=row["pet"],
                    reminder_type="vaccination",
                    title=f"Vaccine Due Soon: {row['vaccine']}",
                    due_date=row["next_due"],
                    defaults={
                        "notes": "[seed] Reminder generated from sample vaccination data",
                        "status": "pending",
                    },
                )

            if row["attach"]:
                file_body = (
                    f"Sample vaccination certificate\n"
                    f"Pet: {row['pet'].name}\n"
                    f"Vaccine: {row['vaccine']}\n"
                    f"Clinic: {clinic.clinic_name}\n"
                )
                attachment = ContentFile(file_body.encode("utf-8"), name=f"seed_{row['pet'].name.lower()}_{row['vaccine'].lower()}.txt")
                medical = MedicalRecordFile(appointment=vaccination_appt)
                medical.file.save(attachment.name, attachment, save=True)

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seed complete. Created {created_count} vaccination sample bundle(s)."))
        self.stdout.write(self.style.WARNING(f"Owner login: {owner.username} / Password: {'owner12345'}"))
        self.stdout.write(self.style.WARNING(f"Vet login: {vet.username} / Password: {'vet12345'}"))

    def _get_or_create_owner(self):
        owner, created = CustomUser.objects.get_or_create(
            username="demo_owner",
            defaults={
                "first_name": "Demo",
                "last_name": "Owner",
                "email": "demo.owner@fluffbud.local",
                "role": "owner",
            },
        )
        if created:
            owner.set_password("owner12345")
            owner.save(update_fields=["password"])
        return owner

    def _get_or_create_vet_and_clinic(self):
        vet, created = CustomUser.objects.get_or_create(
            username="demo_vet",
            defaults={
                "first_name": "Demo",
                "last_name": "Vet",
                "email": "demo.vet@fluffbud.local",
                "role": "vet",
            },
        )
        if created:
            vet.set_password("vet12345")
            vet.save(update_fields=["password"])

        clinic, _ = VetClinic.objects.get_or_create(
            vet=vet,
            defaults={
                "clinic_name": "FluffBud Care Clinic",
                "address": "123 Pet Street",
                "city": "Sample City",
                "phone": "+91 9000000000",
                "specialization": "Small Animal Practice",
                "working_hours": "9 AM - 6 PM",
                "is_emergency": False,
            },
        )
        return vet, clinic

    def _get_or_create_pets(self, owner):
        pet_a, _ = Pet.objects.get_or_create(
            owner=owner,
            name="Milo",
            defaults={
                "species": "Dog",
                "breed": "Labrador",
                "age": 24,
                "gender": "male",
                "weight": Decimal("18.50"),
                "status": "healthy",
            },
        )
        pet_b, _ = Pet.objects.get_or_create(
            owner=owner,
            name="Luna",
            defaults={
                "species": "Cat",
                "breed": "Indie",
                "age": 14,
                "gender": "female",
                "weight": Decimal("4.10"),
                "status": "healthy",
            },
        )
        return [pet_a, pet_b]

    def _clear_seed_data(self):
        VaccinationReminder.objects.filter(notes__icontains="[seed]").delete()
        MedicalRecordFile.objects.filter(appointment__notes__icontains="[seed]").delete()
        VaccinationRecord.objects.filter(notes__icontains="[seed]").delete()
        VaccinationAppointment.objects.filter(notes__icontains="[seed]").delete()
        Appointment.objects.filter(reason__icontains="[seed]").delete()

    def _build_sample_rows(self, pets, today, count):
        vaccine_names = [
            "Rabies",
            "DHPP",
            "Leptospirosis",
            "Bordetella",
            "FVRCP",
            "Canine Influenza",
        ]
        slot_times = ["09:30:00", "10:00:00", "11:30:00", "14:00:00", "15:00:00", "16:30:00"]
        status_pattern = ["completed", "pending", "confirmed", "pending", "completed", "confirmed"]
        date_offsets = [-40, 3, 12, 1, -15, 6]
        attach_pattern = [True, False, False, True, False, False]

        pet_cycle = cycle(pets)
        rows = []
        for index in range(count):
            vaccine = vaccine_names[index % len(vaccine_names)]
            status = status_pattern[index % len(status_pattern)]
            date_value = today + timedelta(days=date_offsets[index % len(date_offsets)])
            row = {
                "pet": next(pet_cycle),
                "vaccine": vaccine,
                "date": date_value,
                "time": slot_times[index % len(slot_times)],
                "notes": f"[seed] Vaccination sample #{index + 1} ({vaccine})",
                "status": status,
                "next_due": date_value + timedelta(days=365),
                "attach": attach_pattern[index % len(attach_pattern)],
            }

            if status == "completed":
                row["next_due"] = today + timedelta(days=5 + (index % 5))

            rows.append(row)

        return rows

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('owner', 'Pet Owner'),
        ('vet', 'Veterinarian'),
        ('shelter', 'Animal Shelter'),
        ('store', 'Pet Store Owner'),
        ('provider', 'Service Provider'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')
    phone = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    PROFILE_VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    profile_visibility = models.CharField(max_length=10, choices=PROFILE_VISIBILITY_CHOICES, default='private')
    two_factor_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    def is_service_provider(self):
        return self.role in ['vet', 'shelter', 'store', 'provider']


class Pet(models.Model):
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female')]
    STATUS_CHOICES = [('healthy', 'Healthy'), ('needs_vaccine', 'Needs Vaccine'), ('sick', 'Sick'), ('under_treatment', 'Under Treatment')]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(help_text="Age in months")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='pets/', blank=True, null=True)
    color = models.CharField(max_length=50, blank=True)
    microchip_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='healthy')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.species})"

    def age_display(self):
        if self.age < 12:
            return f"{self.age} mo"
        return f"{self.age // 12} yr{'s' if self.age // 12 > 1 else ''}"


class HealthRecord(models.Model):
    VISIT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('follow_up', 'Follow-up'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='health_records')
    vet = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='treated_records')
    title = models.CharField(max_length=200)
    description = models.TextField()
    diagnosis = models.CharField(max_length=200, blank=True)
    treatment = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    visit_status = models.CharField(max_length=15, choices=VISIT_STATUS_CHOICES, default='completed')
    weight_at_visit = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attachment = models.FileField(upload_to='health_records/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pet.name} - {self.title} ({self.date})"

    class Meta:
        ordering = ['-date']


class VaccinationReminder(models.Model):
    TYPE_CHOICES = [
        ('vaccination', 'Vaccination'),
        ('deworming', 'Deworming'),
        ('checkup', 'Health Checkup'),
        ('grooming', 'Grooming'),
        ('medication', 'Medication'),
    ]
    STATUS_CHOICES = [('pending', 'Pending'), ('done', 'Done'), ('overdue', 'Overdue')]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pet.name} - {self.title}"

    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status == 'pending'

    class Meta:
        ordering = ['due_date']


class VaccinationAppointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rescheduled', 'Rescheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vaccination_appointments')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccination_appointments')
    vet = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_vaccination_appointments')
    clinic = models.ForeignKey('VetClinic', on_delete=models.SET_NULL, null=True, blank=True, related_name='vaccination_appointments')
    linked_appointment = models.OneToOneField('Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='vaccination_request')
    vaccine_name = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    notification_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.pet.name} vaccine request ({self.vaccine_name})"


class VaccinationRecord(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('due_soon', 'Due Soon'),
        ('scheduled', 'Scheduled'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vaccination_records')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='vaccination_records')
    appointment = models.ForeignKey(VaccinationAppointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='records')
    vaccine_name = models.CharField(max_length=200)
    administered_date = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    vet_clinic = models.ForeignKey('VetClinic', on_delete=models.SET_NULL, null=True, blank=True, related_name='vaccination_records')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-administered_date', '-created_at']

    def __str__(self):
        return f"{self.pet.name} - {self.vaccine_name}"


class MedicalRecordFile(models.Model):
    appointment = models.ForeignKey(VaccinationAppointment, on_delete=models.CASCADE, related_name='medical_files')
    file = models.FileField(upload_to='vaccination_records/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Medical file #{self.id} for {self.appointment.pet.name}"


class VetClinic(models.Model):
    vet = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='clinic')
    clinic_name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to='clinics/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    is_emergency = models.BooleanField(default=False)
    working_hours = models.CharField(max_length=100, default='9 AM - 6 PM')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.clinic_name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    TYPE_CHOICES = [
        ('checkup', 'General Checkup'),
        ('vaccination', 'Vaccination'),
        ('surgery', 'Surgery'),
        ('grooming', 'Grooming'),
        ('emergency', 'Emergency'),
        ('dental', 'Dental'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments')
    vet = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vet_appointments')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    clinic = models.ForeignKey(VetClinic, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='checkup')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    notification_seen = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    vet_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pet.name} → {self.clinic} on {self.date}"

    class Meta:
        ordering = ['-date', '-time']


class MedicineInventory(models.Model):
    CATEGORY_CHOICES = [
        ('vaccines', 'Vaccines'),
        ('antibiotics', 'Antibiotics'),
        ('surgical', 'Surgical Supplies'),
        ('dewormers', 'Dewormers'),
        ('other', 'Other'),
    ]

    vet = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='medicine_inventory')
    clinic = models.ForeignKey(VetClinic, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicine_inventory')
    medicine_name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    supplier_shop = models.CharField(max_length=200, blank=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medicine_name} ({self.quantity})"

    @property
    def is_low_stock(self):
        return self.quantity < self.low_stock_threshold


class SupplyOrder(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    vet = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='supply_orders')
    clinic = models.ForeignKey(VetClinic, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_orders')
    medicine = models.ForeignKey(MedicineInventory, on_delete=models.CASCADE, related_name='orders')
    supplier_shop = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ordered')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.medicine.medicine_name}"


class AdoptionListing(models.Model):
    STATUS_CHOICES = [('available', 'Available'), ('pending', 'Pending'), ('adopted', 'Adopted')]
    SIZE_CHOICES = [('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')]

    shelter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='adoption_listings')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(help_text="Age in months")
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium')
    color = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='adoption/', blank=True, null=True)
    description = models.TextField()
    vaccinated = models.BooleanField(default=False)
    neutered = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.species}) - {self.status}"

    def age_display(self):
        if self.age < 12:
            return f"{self.age} mo"
        return f"{self.age // 12} yr"

    class Meta:
        ordering = ['-created_at']


class AdoptionRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    listing = models.ForeignKey(AdoptionListing, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='adoption_requests')
    message = models.TextField()
    living_situation = models.CharField(max_length=200, blank=True)
    has_other_pets = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requester.username} → {self.listing.name}"


class Animal(models.Model):
    SPECIES_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('rabbit', 'Rabbit'),
        ('other', 'Other'),
    ]
    GENDER_CHOICES = [('male', 'Male'), ('female', 'Female')]
    SIZE_CHOICES = [('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')]
    HEALTH_STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('needs_care', 'Needs Care'),
        ('critical', 'Critical'),
    ]
    VACCINATION_STATUS_CHOICES = [
        ('up_to_date', 'Up to Date'),
        ('due', 'Due'),
        ('not_vaccinated', 'Not Vaccinated'),
    ]
    ADOPTION_STATUS_CHOICES = [
        ('available', 'Available'),
        ('adopted', 'Adopted'),
    ]

    shelter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='animals')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(help_text="Age in months")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium')
    photo = models.ImageField(upload_to='shelter_animals/', blank=True, null=True)
    rescue_location = models.CharField(max_length=200, blank=True)
    intake_date = models.DateField(default=timezone.now)
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default='healthy')
    vaccination_status = models.CharField(max_length=20, choices=VACCINATION_STATUS_CHOICES, default='due')
    adoption_status = models.CharField(max_length=20, choices=ADOPTION_STATUS_CHOICES, default='available')
    description = models.TextField(blank=True)
    adopted_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.species})"

    def age_display(self):
        if self.age < 12:
            return f"{self.age} mo"
        return f"{self.age // 12} yr"


class AdoptionApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='shelter_applications')
    applicant_name = models.CharField(max_length=150)
    contact_info = models.CharField(max_length=200)
    living_situation = models.CharField(max_length=200)
    pet_experience = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant_name} → {self.animal.name}"


class ShelterIntake(models.Model):
    shelter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shelter_intakes')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='intakes')
    intake_date = models.DateField(default=timezone.now)
    rescue_location = models.CharField(max_length=200, blank=True)
    health_status = models.CharField(max_length=20, choices=Animal.HEALTH_STATUS_CHOICES, default='healthy')
    vaccination_status = models.CharField(max_length=20, choices=Animal.VACCINATION_STATUS_CHOICES, default='due')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Intake: {self.animal.name} ({self.intake_date})"


class AdoptionRecord(models.Model):
    shelter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='adoption_records')
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='adoption_records')
    application = models.ForeignKey(AdoptionApplication, on_delete=models.SET_NULL, null=True, blank=True, related_name='adoption_records')
    adopter_name = models.CharField(max_length=150)
    adoption_date = models.DateField(default=timezone.now)
    days_to_adoption = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.animal.name} adopted by {self.adopter_name}"


class LostPetReport(models.Model):
    TYPE_CHOICES = [('lost', 'Lost Pet'), ('found', 'Found Pet')]

    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lost_found_reports')
    report_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    pet_name = models.CharField(max_length=100, blank=True)
    species = models.CharField(max_length=50)
    breed = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=100)
    description = models.TextField()
    photo = models.ImageField(upload_to='lost_found/', blank=True, null=True)
    location = models.CharField(max_length=200)
    date_lost_found = models.DateField()
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    contact_email = models.EmailField(blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.report_type.upper()}] {self.species} at {self.location}"

    class Meta:
        ordering = ['-created_at']


class PetStore(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to='stores/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    services = models.CharField(max_length=300, default='food,accessories')
    working_hours = models.CharField(max_length=100, default='9 AM - 8 PM')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def services_list(self):
        return [s.strip() for s in self.services.split(',')]


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Pet Food'),
        ('medicine', 'Medicine'),
        ('accessories', 'Accessories'),
        ('grooming', 'Grooming'),
        ('toys', 'Toys'),
        ('bedding', 'Bedding'),
    ]

    store = models.ForeignKey(PetStore, on_delete=models.CASCADE, related_name='inventory')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    photo = models.ImageField(upload_to='inventory/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.store.name}"


class Supplier(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=200)
    contact_info = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'name')

    def __str__(self):
        return self.name


class ProductInventory(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('toys', 'Toys'),
        ('health', 'Health'),
        ('accessories', 'Accessories'),
    ]
    UNIT_TYPE_CHOICES = [
        ('bags', 'bags'),
        ('cans', 'cans'),
        ('pcs', 'pcs'),
        ('boxes', 'boxes'),
    ]

    store = models.ForeignKey(PetStore, on_delete=models.CASCADE, related_name='product_inventory')
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    stock_quantity = models.PositiveIntegerField(default=0)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='pcs')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} ({self.store.name})"

    @property
    def is_low_stock(self):
        return self.stock_quantity < self.low_stock_threshold


class CustomerOrder(models.Model):
    ORDER_SOURCE_CHOICES = [
        ('online', 'Online'),
        ('in_store', 'In-Store'),
    ]
    STATUS_CHOICES = [
        ('packing', 'Packing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    store = models.ForeignKey(PetStore, on_delete=models.CASCADE, related_name='customer_orders')
    customer_name = models.CharField(max_length=150)
    order_source = models.CharField(max_length=20, choices=ORDER_SOURCE_CHOICES, default='online')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='packing')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    PET_CATEGORY_CHOICES = [
        ('cat', 'Cat'),
        ('dog', 'Dog'),
        ('rabbit', 'Rabbit'),
        ('small_pets', 'Small Pets'),
    ]

    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(ProductInventory, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    pet_category = models.CharField(max_length=20, choices=PET_CATEGORY_CHOICES, default='dog')

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"


class SocialPost(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    pet = models.ForeignKey(Pet, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    lost_found_report = models.ForeignKey(LostPetReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='community_posts')
    content = models.TextField()
    photo = models.ImageField(upload_to='community/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:50]}"

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()

    class Meta:
        ordering = ['-created_at']


class PostLike(models.Model):
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')


class PostComment(models.Model):
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} on post {self.post.id}"

    class Meta:
        ordering = ['created_at']


class ServiceProvider(models.Model):
    PROVIDER_TYPE_CHOICES = [
        ('VET', 'Vet Clinic'),
        ('SHELTER', 'Shelter'),
        ('PET_STORE', 'Pet Store'),
        ('GROOMER', 'Groomer'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='service_profiles')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPE_CHOICES)
    provider_id_file = models.FileField(upload_to='provider_ids/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    photo = models.ImageField(upload_to='services/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    price_range = models.CharField(max_length=100, blank=True, help_text="e.g. ₹500 - ₹2000")
    working_hours = models.CharField(max_length=100, default='9 AM - 6 PM')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"

    class Meta:
        ordering = ['-created_at']


class ServiceBooking(models.Model):
    GROOMING_SERVICE_CHOICES = [
        ('bath_brush', 'Bath & Brush'),
        ('full_groom', 'Full Groom'),
        ('breed_cut', 'Breed Cut'),
        ('nail_trim', 'Nail Trim'),
        ('de_shedding', 'De-shedding'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='service_bookings')
    service = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='bookings')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='service_bookings')
    date = models.DateField()
    time = models.TimeField()
    service_type = models.CharField(max_length=30, choices=GROOMING_SERVICE_CHOICES, default='full_groom')
    duration_minutes = models.PositiveIntegerField(default=60)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    notification_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} → {self.service.name} on {self.date}"

    class Meta:
        ordering = ['-date', '-time']


class GroomingSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    groomer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grooming_sessions')
    service = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='grooming_sessions')
    booking = models.OneToOneField(ServiceBooking, on_delete=models.SET_NULL, null=True, blank=True, related_name='grooming_session')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='grooming_sessions')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pet_grooming_sessions')
    service_type = models.CharField(max_length=30, choices=ServiceBooking.GROOMING_SERVICE_CHOICES, default='full_groom')
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    special_notes = models.TextField(blank=True)
    session_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pet.name} session ({self.get_service_type_display()})"


class GroomingSupply(models.Model):
    CATEGORY_CHOICES = [
        ('shampoo', 'Shampoo'),
        ('conditioner', 'Conditioner'),
        ('blades', 'Grooming Blades'),
        ('ear_cleaning', 'Ear Cleaning Solution'),
        ('de_shedding', 'De-shedding Spray'),
        ('other', 'Other'),
    ]

    groomer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grooming_supplies')
    service = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='grooming_supplies')
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=30, default='bottle')
    supplier = models.CharField(max_length=200, blank=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.quantity < self.low_stock_threshold

    def __str__(self):
        return self.product_name


class GroomingSupplyOrder(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    groomer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grooming_supply_orders')
    service = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='grooming_supply_orders')
    supply = models.ForeignKey(GroomingSupply, on_delete=models.CASCADE, related_name='orders')
    supplier = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ordered')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grooming Order #{self.id}"


class ClientCareNote(models.Model):
    groomer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_care_notes')
    service = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_care_notes')
    booking = models.ForeignKey(ServiceBooking, on_delete=models.SET_NULL, null=True, blank=True, related_name='care_notes')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='care_notes')
    appointment_time = models.TimeField()
    note_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.pet.name} care note"

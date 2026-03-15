from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (CustomUser, Pet, HealthRecord, VaccinationReminder,
                     Appointment, AdoptionListing, AdoptionRequest,
                     LostPetReport, PetStore, InventoryItem, SocialPost, PostComment, VetClinic,
                     ServiceProvider, ServiceBooking, MedicineInventory,
                     GroomingSupply, ClientCareNote,
                     Animal, AdoptionApplication, VaccinationAppointment, MedicalRecordFile,
                     ProductInventory)


class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'you@email.com'}))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'placeholder': '+91 XXXXX XXXXX'}))
    city = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Your city'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'city', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        exclude = ['owner', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet name'}),
            'species': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dog, Cat, Rabbit...'}),
            'breed': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Breed (optional)'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age in months'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Golden brown'}),
            'microchip_id': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ['title', 'description', 'diagnosis', 'medications', 'date', 'weight_at_visit', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weight_at_visit': forms.NumberInput(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


class VaccinationReminderForm(forms.ModelForm):
    class Meta:
        model = VaccinationReminder
        fields = ['reminder_type', 'title', 'notes', 'due_date']
        widgets = {
            'reminder_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['vet', 'pet', 'appointment_type', 'date', 'time', 'reason']
        widgets = {
            'vet': forms.Select(attrs={'class': 'form-select'}),
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)
        self.fields['vet'].queryset = CustomUser.objects.filter(role='vet')
        self.fields['vet'].label_from_instance = lambda obj: f"Dr. {obj.get_full_name() or obj.username}"


class AdoptionListingForm(forms.ModelForm):
    class Meta:
        model = AdoptionListing
        fields = ['animal', 'adoption_fee', 'adoption_description', 'vaccination_records', 'medical_notes']
        widgets = {
            'animal': forms.Select(attrs={'class': 'form-select'}),
            'adoption_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'adoption_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vaccination_records': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, shelter_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['animal'].empty_label = 'Select an animal in care'
        if shelter_user:
            self.fields['animal'].queryset = Animal.objects.filter(
                shelter=shelter_user,
                adoption_status='available',
            ).order_by('-created_at')


class AdoptionRequestForm(forms.ModelForm):
    class Meta:
        model = AdoptionRequest
        fields = ['message', 'living_situation', 'has_other_pets']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Why do you want to adopt this pet?'}),
            'living_situation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House/Apartment, yard/no yard...'}),
            'has_other_pets': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LostPetReportForm(forms.ModelForm):
    class Meta:
        model = LostPetReport
        exclude = ['reporter', 'is_resolved', 'created_at']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'pet_name': forms.TextInput(attrs={'class': 'form-control'}),
            'species': forms.TextInput(attrs={'class': 'form-control'}),
            'breed': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'date_lost_found': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PetStoreForm(forms.ModelForm):
    class Meta:
        model = PetStore
        exclude = ['owner', 'created_at', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'services': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'food,grooming,accessories'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        exclude = ['store', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class VetClinicForm(forms.ModelForm):
    class Meta:
        model = VetClinic
        exclude = ['vet', 'created_at']
        widgets = {
            'clinic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'is_emergency': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class SocialPostForm(forms.ModelForm):
    class Meta:
        model = SocialPost
        fields = ['content', 'pet', 'photo']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "What's your furry friend up to? 🐾"}),
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)
        self.fields['pet'].required = False
        self.fields['pet'].empty_label = "No specific pet"


class CommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write a comment...'})
        }


class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        exclude = ['owner', 'created_at', 'is_active', 'is_verified']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Business name'}),
            'provider_type': forms.Select(attrs={'class': 'form-select'}),
            'provider_id_file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your services...'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 XXXXX XXXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@email.com'}),
            'price_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹500 - ₹2000'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9 AM - 6 PM'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ServiceBookingForm(forms.ModelForm):
    class Meta:
        model = ServiceBooking
        fields = ['pet', 'service_type', 'date', 'time', 'duration_minutes', 'notes']
        widgets = {
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special instructions...'}),
        }

    def __init__(self, user=None, service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)
        if not service or service.provider_type != 'GROOMER':
            self.fields.pop('service_type', None)
            self.fields.pop('duration_minutes', None)


class GroomingSupplyForm(forms.ModelForm):
    class Meta:
        model = GroomingSupply
        fields = ['product_name', 'category', 'quantity', 'unit', 'supplier', 'price_per_unit', 'low_stock_threshold']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class GroomingBookingForm(ServiceBookingForm):
    pass


class GroomerInventoryForm(GroomingSupplyForm):
    pass


class ClientCareNoteForm(forms.ModelForm):
    class Meta:
        model = ClientCareNote
        fields = ['pet', 'appointment_time', 'note_text']
        widgets = {
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'note_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, groomer=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if groomer:
            self.fields['pet'].queryset = Pet.objects.filter(service_bookings__service__owner=groomer).distinct()


class MedicineInventoryForm(forms.ModelForm):
    class Meta:
        model = MedicineInventory
        fields = ['medicine_name', 'category', 'quantity', 'supplier_shop', 'price_per_unit', 'low_stock_threshold']
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'supplier_shop': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class VetPatientRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ['pet', 'date', 'diagnosis', 'medications', 'description', 'treatment', 'visit_status']
        widgets = {
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'treatment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'visit_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner__appointments__vet=user).distinct()


class AnimalIntakeForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['name', 'species', 'breed', 'age', 'gender', 'size', 'rescue_location', 'health_status', 'vaccination_status', 'intake_date', 'description', 'photo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'species': forms.Select(attrs={'class': 'form-select'}),
            'breed': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'rescue_location': forms.TextInput(attrs={'class': 'form-control'}),
            'health_status': forms.Select(attrs={'class': 'form-select'}),
            'vaccination_status': forms.Select(attrs={'class': 'form-select'}),
            'intake_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AdoptionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdoptionApplication
        fields = ['applicant_name', 'contact_info', 'living_situation', 'pet_experience', 'notes']
        widgets = {
            'applicant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control'}),
            'living_situation': forms.TextInput(attrs={'class': 'form-control'}),
            'pet_experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProductInventoryForm(forms.ModelForm):
    class Meta:
        model = ProductInventory
        fields = ['product_name', 'category', 'price_per_unit', 'stock_quantity', 'product_image']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'product_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AutoReorderForm(forms.Form):
    supplier_shop = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))


class VaccinationAppointmentForm(forms.ModelForm):
    class Meta:
        model = VaccinationAppointment
        fields = ['pet', 'vaccine_name', 'date', 'time', 'clinic', 'notes']
        widgets = {
            'pet': forms.Select(attrs={'class': 'form-select'}),
            'vaccine_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'clinic': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes / Reason'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clinic'].queryset = VetClinic.objects.all().select_related('vet').order_by('clinic_name')
        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)


class MedicalRecordFileForm(forms.ModelForm):
    class Meta:
        model = MedicalRecordFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }

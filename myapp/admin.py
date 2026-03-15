from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'city']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('fluffbud Profile', {'fields': ('role', 'phone', 'city', 'profile_photo', 'bio')}),
    )


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'owner', 'status']
    list_filter = ['species', 'gender', 'status']
    search_fields = ['name', 'breed', 'owner__username']


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['pet', 'title', 'date', 'vet']
    list_filter = ['date']


@admin.register(VaccinationReminder)
class VaccinationReminderAdmin(admin.ModelAdmin):
    list_display = ['pet', 'title', 'reminder_type', 'due_date', 'status']
    list_filter = ['reminder_type', 'status']


@admin.register(VetClinic)
class VetClinicAdmin(admin.ModelAdmin):
    list_display = ['clinic_name', 'vet', 'city', 'is_emergency', 'rating']
    list_filter = ['city', 'is_emergency']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['pet', 'owner', 'vet', 'date', 'time', 'status', 'appointment_type']
    list_filter = ['status', 'appointment_type', 'date']


@admin.register(AdoptionListing)
class AdoptionListingAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'shelter', 'status', 'location', 'created_at']
    list_filter = ['species', 'status', 'gender']


@admin.register(AdoptionRequest)
class AdoptionRequestAdmin(admin.ModelAdmin):
    list_display = ['listing', 'requester', 'status', 'created_at']
    list_filter = ['status']


@admin.register(LostPetReport)
class LostPetReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'species', 'location', 'reporter', 'is_resolved', 'created_at']
    list_filter = ['report_type', 'is_resolved']


@admin.register(PetStore)
class PetStoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'rating', 'is_active']
    list_filter = ['city', 'is_active']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'category', 'price', 'stock', 'is_available']
    list_filter = ['category', 'is_available']


@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ['author', 'pet', 'created_at']


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'provider_type', 'city', 'rating', 'is_verified', 'is_active']
    list_filter = ['provider_type', 'city', 'is_verified', 'is_active']
    search_fields = ['name', 'owner__username', 'city']


@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ['service', 'customer', 'pet', 'date', 'time', 'status']
    list_filter = ['status', 'date']


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'created_at']


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'content', 'created_at']

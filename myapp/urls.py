from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logout/service-provider/', views.logout_view, name='logout_service_provider'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),

    # Pets
    path('pets/', views.pet_list, name='pet_list'),
    path('pets/add/', views.add_pet, name='add_pet'),
    path('pets/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pk>/edit/', views.edit_pet, name='edit_pet'),
    path('pets/<int:pk>/delete/', views.delete_pet, name='delete_pet'),

    # Appointments
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/book/', views.book_appointment, name='book_appointment'),
    path('appointments/notifications/next/', views.next_booking_request, name='next_booking_request'),
    path('appointments/<int:pk>/keep-waiting/', views.keep_waiting_booking_request, name='keep_waiting_booking_request'),
    path('appointments/<int:pk>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointments/<int:pk>/<str:status>/', views.update_appointment_status, name='update_appointment'),
    path('clinic/medicine/add/', views.add_medicine_stock, name='add_medicine_stock'),
    path('clinic/reorder/preview/', views.reorder_supplies_preview, name='reorder_supplies_preview'),
    path('clinic/reorder/confirm/', views.reorder_supplies_confirm, name='reorder_supplies_confirm'),
    path('clinic/patient-record/add/', views.add_patient_record, name='add_patient_record'),
    path('clinic/patient-records/', views.all_patient_records, name='all_patient_records'),

    # Adoption
    path('adoption/', views.adoption, name='adoption'),
    path('adoption/add/', views.add_adoption_listing, name='add_adoption_listing'),
    path('adoption/<int:pk>/request/', views.adoption_request, name='adoption_request'),
    path('adoption/request/<int:pk>/<str:action>/', views.manage_adoption_request, name='manage_adoption_request'),
    path('adoption/applications/', views.view_all_applications, name='view_all_applications'),
    path('shelter/intake/log/', views.log_shelter_intake, name='log_shelter_intake'),

    # Lost & Found
    path('lost-found/', views.lost_found, name='lost_found'),
    path('lost-found/report/', views.report_lost_found, name='report_lost_found'),
    path('lost-found/<int:pk>/resolved/', views.mark_resolved, name='mark_resolved'),

    # Community
    path('community/', views.community, name='community'),
    path('community/post/<int:pk>/like/', views.like_post, name='like_post'),
    path('community/post/<int:pk>/comment/', views.comment_post, name='comment_post'),
    path('community/post/<int:pk>/delete/', views.delete_post, name='delete_post'),

    # Stores
    path('stores/', views.stores, name='stores'),
    path('api/stores', views.api_stores, name='api_stores'),
    path('stores/manage/', views.manage_store, name='manage_store'),
    path('stores/inventory/add/', views.add_inventory, name='add_inventory'),
    path('stores/inventory/<int:pk>/delete/', views.delete_inventory, name='delete_inventory'),
    path('stores/product/add/', views.add_product_inventory, name='add_product_inventory'),
    path('stores/reorder/preview/', views.reorder_low_stock_preview, name='reorder_low_stock_preview'),
    path('stores/reorder/confirm/', views.reorder_low_stock_confirm, name='reorder_low_stock_confirm'),
    path('stores/orders/api/', views.store_orders_api, name='store_orders_api'),
    path('stores/analytics/api/', views.store_analytics_api, name='store_analytics_api'),

    # Service Providers
    path('services/', views.services, name='services'),
    path('services/manage/', views.manage_service, name='manage_service'),
    path('services/book/<int:pk>/', views.book_service, name='book_service'),
    path('services/booking/<int:pk>/<str:status>/', views.update_service_booking, name='update_service_booking'),
    path('grooming/booking/<int:pk>/keep-waiting/', views.keep_waiting_grooming_booking, name='keep_waiting_grooming_booking'),
    path('grooming/booking/<int:pk>/accept/', views.accept_grooming_booking, name='accept_grooming_booking'),
    path('grooming/booking/<int:pk>/reschedule/', views.reschedule_grooming_booking, name='reschedule_grooming_booking'),
    path('grooming/supply/add/', views.add_grooming_supply, name='add_grooming_supply'),
    path('grooming/reorder/preview/', views.reorder_grooming_supplies_preview, name='reorder_grooming_supplies_preview'),
    path('grooming/reorder/confirm/', views.reorder_grooming_supplies_confirm, name='reorder_grooming_supplies_confirm'),
    path('grooming/care-note/add/', views.add_client_care_note, name='add_client_care_note'),

    # Vet Clinic
    path('clinic/manage/', views.manage_clinic, name='manage_clinic'),

    # Emergency
    path('emergency/', views.emergency, name='emergency'),

    # Service Provider Portal
    path('provider-portal/', views.provider_portal, name='provider_portal'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('notifications/', views.notifications, name='notifications'),
]

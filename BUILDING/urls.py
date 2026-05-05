# BUILDING/urls.py
from django.urls import path
from . import views

app_name = "BUILDING"

urlpatterns = [
    # ============= MAIN BUILDING URLS =============
    path('buildings/', views.building_list, name='building_list'),
    path('building/<int:id>/', views.building_detail, name='building_detail'),
    
    # ============= APARTMENT URLS =============
    path('apartments/', views.apartment_list, name='apartment_list'),
    
    # ============= RESIDENTIAL URLS =============
    path('residential/', views.residential_list, name='residential_list'),
    
    # ============= INDUSTRIAL URLS =============
    path('industrial/', views.industrial_list, name='industrial_list'),
    
    # ============= COMMERCIAL URLS =============
    path('commercial/', views.commercial_list, name='commercial_list'),
    
    # ============= UNIFIED PAYMENT URLS =============
    path('initiate/<int:building_id>/', views.initiate_payment, name='initiate_payment'),
    path('checkout/<int:payment_id>/', views.checkout, name='checkout'),
    path('verify/<int:payment_id>/', views.payment_verify, name='payment_verify'),
    path('thank-you/<int:building_id>/', views.thank_you, name='thank_you'),
    path('process-reservation/<int:payment_id>/', views.process_reservation, name='process_reservation'),
    
    # ============= API ENDPOINTS =============
    path('api/property/<int:pk>/status/', views.get_property_status, name='get_property_status'),
    
    # ============= LEGACY URLS (Backward Compatibility) =============
    # These redirect to new unified views but keep old names for existing templates
    path('initiate-house/<int:building_id>/', views.initiate_house_payment, name='initiate_house_payment'),
    path('checkout-house/<int:payment_id>/', views.checkout_for_house, name='checkout_for_house'),
    path('thank-you-house/<int:building_id>/', views.thank_you_house, name='thank_you_house'),
    
    # Legacy purchase URLs
    path('apartment/<int:pk>/purchase/', views.purchase_apartment, name='purchase_apartment'),
    path('residential/<int:pk>/purchase/', views.purchase_residential, name='purchase_residential'),
    path('industrial/<int:pk>/purchase/', views.purchase_industrial, name='purchase_industrial'),
    path('commercial/<int:pk>/purchase/', views.purchase_commercial, name='purchase_commercial'),
    
    # ============= ADMIN MANAGEMENT URLS =============
    path('admin/properties/', views.manage_properties, name='manage_properties'),
    path('admin/properties/<str:property_type>/', views.manage_properties, name='manage_properties_by_type'),
    path('admin/property/<int:pk>/toggle/', views.toggle_availability, name='toggle_availability'),
    
    # Legacy admin URLs (keep for backward compatibility)
    path('admin/apartments/', views.manage_apartments, name='manage_apartments'),
    path('admin/industrial/', views.manage_industrial, name='manage_industrial'),
]
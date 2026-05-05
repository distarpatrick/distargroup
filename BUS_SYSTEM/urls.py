from django.urls import path
from .views import acknowledge, submit_property, submit_vehicle
from . import views
from .models import Vehicleinformation, VehicleinformationImage
app_name = "BUS_SYSTEM"


app_name = "BUS_SYSTEM"

urlpatterns = [
    path('', views.mainpage, name='mainpage'),
    
    # Vehicles
    path('homecars/', views.homecars, name='homecars'),
    path('allvehicles/', views.allvehicles, name='allvehicles'),
    path('car/<int:id>/', views.vehicleinfo, name='car_detail'),
    #cars details
    
   
    path("vehicle/<int:id>/", views.vehicleinfo, name='car_detail'),
    path("car-for-sale/", views.car_for_sale, name="car_for_sale"),
    path('cars-by-price/', views.car_range_price, name='car_range_price'),
    path('cars-for-rent/', views.car_for_rent, name='car_for_rent'),
    path('used-cars/', views.car_used, name='car_used'),
   
    path('car-local-markets/', views.localmarketcar, name='car_local_markets'),
    path('vehicle/<int:vehicle_id>/payment/', views.vehicle_payment, name='vehicle_payment'),
    #motorcycle details
    path('moto-local-markets/', views.localmarketMoto, name='moto_local_markets'),

    # Houses
    path('houseproducts/', views.houseProducts, name='houseproducts'),
    path('apartment/', views.apartment, name="apartment"),
    path('house/<int:house_id>/', views.house_detail_view, name='house_detail'),
    
    path('submit_property/', submit_property, name='submit_property'),


    # Marketplace & products
    path('marketplace/', views.marketplace, name='marketplace'),
    path('bevarages/', views.drinks, name='bevarages'),
    path('clothesmarket/', views.clothesmarket, name="clothesmarket"),
    path('foodmarket/', views.foodmarket, name="foodmarket"),
    path('electronicsmarket/', views.electronics, name="electronicsmarket"),
    path('add-product/', views.add_product, name='add_product'),
    # Shoes
    path('shoesmarket/', views.shoesmarket, name="shoesmarket"),
    path('latestShoes/', views.latestshoes, name="latestShoes"),
    # Upload forms
    path('uploadfile/', views.uploadfile, name='uploadfile'),
    path('submit-vehicle/', submit_vehicle, name='submit_vehicle'),

    # Thank you pages
    path('global-search-api/', views.global_search_api, name='global_search_api'),
    path('thank-you/', acknowledge, name='acknowledge'),
    path('thank-you-vehicle/', views.thank_you, name='thank_you'),
    
    #cars details
    path("newcars/", views.newcars, name="newcars"),
    path("vehicle/<int:id>/", views.vehicle_detail, name="vehicle_detail"),
     path('vehicles/', views.allcars, name='allcars'),
    path('vehicles/car-for-sale/', views.car_for_sale, name='car_for_sale'),
    path('vehicles/car-for-rent/', views.car_for_rent, name='car_for_rent'),
    path('vehicles/new-cars/', views.newcars, name='newcars'),
    path('vehicles/used-cars/', views.car_used, name='car_used'),
    
    #motocycle details
     path('motorcycles/', views.allmotorcycles, name='allmotorcycles'),
     path('motorcycles/for-sale/', views.moto_for_sale, name='moto_for_sale'),
     path('motorcycles/for-rent/', views.moto_for_rent, name='moto_for_rent'),
     path('motorcycles/new/', views.new_motorcycles, name='new_motorcycles'),
     path('motorcycles/used/', views.used_motorcycles, name='used_motorcycles'),
     path('motorcycle/<int:pk>/', views.motorcycle_detail, name='motorcycle_detail'),
    
    
    path('search/', views.global_search, name='global_search'),
    
    #login and register
    path('auth/', views.auth_page, name='auth'),
    path('auth-system/', views.auth_system, name='auth_system'),
     path('logout/', views.logout_view, name='logout'),
    
    
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart_session, name="add_to_cart_session"),
    
    path('vehicle/initiate-payment/<int:vehicle_id>/', views.initiate_vehicle_payment, name='initiate_vehicle_payment'),
    path('vehicle/checkout/<int:payment_id>/', views.checkout_for_vehicle, name='checkout_for_vehicle'),
    path('vehicle/verify/<int:payment_id>/', views.payment_verify_vehicle, name='payment_verify_vehicle'),
    path('vehicle/success/<int:vehicle_id>/', views.thank_you_vehicle, name='thank_you_vehicle'),
    

    path('clothes/', views.clothes_view, name='clothes_list'),
    path('bags/', views.bags_view, name='bags_list'),
    path('all-fashion/', views.all_fashion_view, name='all_fashion'),
    # urls.py
    path('debug-roles/', views.debug_check_roles, name='debug_roles'),
    
]

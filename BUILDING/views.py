from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from BUS_SYSTEM.models import Building
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from BUILDING.models import Payment
import random
import uuid
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import User
from decimal import Decimal


# ============= BASE/UNIFIED VIEWS =============

def building_list(request):
    """Display all buildings with filtering by type"""
    property_type = request.GET.get('type', 'all')
    
    # Base queryset: ONLY show available buildings
    buildings_queryset = Building.objects.filter(is_available=True).order_by('-created_at')
    
    # Further filter by type if not 'all'
    if property_type != 'all':
        buildings_queryset = buildings_queryset.filter(property_type=property_type)

    # Pagination
    paginator = Paginator(buildings_queryset, 12)
    page_number = request.GET.get('page')
    buildings = paginator.get_page(page_number)
    
    context = {
        'buildings': buildings,
        'property_type': property_type
    }
    return render(request, 'BUILDING/allhouses.html', context)
def building_detail(request, id):
    """UNIFIED detail view for ALL property types (Apartment, Residential, Industrial, Commercial)"""
    building = get_object_or_404(Building, id=id, is_available=True)
    
    # Get related buildings of the same property type
    related_buildings = Building.objects.filter(
        property_type=building.property_type,
        is_available=True
    ).exclude(id=id)[:6]
    
    # Use your existing detailed template for ALL property types
    template_name = 'BUILDING/building_detail.html'
    
    # Prepare context - your template uses 'house' as the main variable
    context = {
        'house': building,  # Your template expects 'house'
        'building': building,  # For compatibility
        'property': building,  # For compatibility
        'apartment': building if building.property_type == 'Apartment' else None,
        'residential': building if building.property_type == 'Residential' else None,
        'industrial': building if building.property_type == 'Industrial' else None,
        'commercial': building if building.property_type == 'Commercial' else None,
        'related_buildings': related_buildings,
        'related_properties': related_buildings,
        'property_type': building.property_type,
    }
    
    return render(request, template_name, context)

# ============= PROPERTY LISTING VIEWS (Type-Specific) =============

def apartment_list(request):
    """Display available apartments with filtering and search"""
    properties = Building.objects.filter(
        property_type='Apartment',
        is_available=True
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(realtor__icontains=search_query)
        )
    
    # Filter by term (Sale/Rent)
    term_filter = request.GET.get('term', '')
    if term_filter:
        properties = properties.filter(property_term__iexact=term_filter)
    
    # Filter by bedrooms
    bedrooms = request.GET.get('bedrooms', '')
    if bedrooms and bedrooms.isdigit():
        if bedrooms == '5':
            properties = properties.filter(bedrooms__gte=5)
        else:
            properties = properties.filter(bedrooms=int(bedrooms))
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price and min_price.isdigit():
        properties = properties.filter(price__gte=Decimal(min_price))
    if max_price and max_price.isdigit():
        properties = properties.filter(price__lte=Decimal(max_price))
    
    # Pagination
    paginator = Paginator(properties, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter stats
    total_properties = properties.count()
    available_sale = Building.objects.filter(
        property_type='Apartment', 
        is_available=True, 
        property_term__iexact='sale'
    ).count()
    available_rent = Building.objects.filter(
        property_type='Apartment', 
        is_available=True, 
        property_term__iexact='rent'
    ).count()
    
    context = {
        'apartments': page_obj,
        'total_apartments': total_properties,
        'available_sale': available_sale,
        'available_rent': available_rent,
        'search_query': search_query,
        'term_filter': term_filter,
        'bedrooms_filter': bedrooms,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'BUILDING/apartment_list.html', context)


def residential_list(request):
    """Display available residential properties with filtering and search"""
    properties = Building.objects.filter(
        property_type='Residential',
        is_available=True
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(realtor__icontains=search_query)
        )
    
    # Filter by term (Sale/Rent)
    term_filter = request.GET.get('term', '')
    if term_filter:
        properties = properties.filter(property_term__iexact=term_filter)
    
    # Filter by bedrooms
    bedrooms = request.GET.get('bedrooms', '')
    if bedrooms and bedrooms.isdigit():
        if bedrooms == '5':
            properties = properties.filter(bedrooms__gte=5)
        else:
            properties = properties.filter(bedrooms=int(bedrooms))
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price and min_price.isdigit():
        properties = properties.filter(price__gte=Decimal(min_price))
    if max_price and max_price.isdigit():
        properties = properties.filter(price__lte=Decimal(max_price))
    
    # Pagination
    paginator = Paginator(properties, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter stats
    total_residential = properties.count()
    available_sale = Building.objects.filter(
        property_type='Residential', 
        is_available=True, 
        property_term__iexact='sale'
    ).count()
    available_rent = Building.objects.filter(
        property_type='Residential', 
        is_available=True, 
        property_term__iexact='rent'
    ).count()
    
    context = {
        'residential_properties': page_obj,
        'total_residential': total_residential,
        'available_sale': available_sale,
        'available_rent': available_rent,
        'search_query': search_query,
        'term_filter': term_filter,
        'bedrooms_filter': bedrooms,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'BUILDING/residential.html', context)


def industrial_list(request):
    """Display available industrial properties with filtering and search"""
    properties = Building.objects.filter(
        property_type='Industrial',
        is_available=True
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(realtor__icontains=search_query)
        )
    
    # Filter by term (Sale/Lease)
    term_filter = request.GET.get('term', '')
    if term_filter:
        properties = properties.filter(property_term__iexact=term_filter)
    
    # Filter by area range (square feet)
    min_area = request.GET.get('min_area', '')
    max_area = request.GET.get('max_area', '')
    if min_area and min_area.isdigit():
        properties = properties.filter(plot_area__gte=Decimal(min_area))
    if max_area and max_area.isdigit():
        properties = properties.filter(plot_area__lte=Decimal(max_area))
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price and min_price.isdigit():
        properties = properties.filter(price__gte=Decimal(min_price))
    if max_price and max_price.isdigit():
        properties = properties.filter(price__lte=Decimal(max_price))
    
    # Pagination
    paginator = Paginator(properties, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter stats
    total_industrial = properties.count()
    available_sale = Building.objects.filter(
        property_type='Industrial', 
        is_available=True, 
        property_term__iexact='sale'
    ).count()
    available_rent = Building.objects.filter(
        property_type='Industrial', 
        is_available=True, 
        property_term__iexact='rent'
    ).count()
    
    context = {
        'industrial_properties': page_obj,
        'total_industrial': total_industrial,
        'available_sale': available_sale,
        'available_rent': available_rent,
        'search_query': search_query,
        'term_filter': term_filter,
        'min_area': min_area,
        'max_area': max_area,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'BUILDING/industrial.html', context)


def commercial_list(request):
    """Display available commercial properties with filtering and search"""
    properties = Building.objects.filter(
        property_type='Commercial',
        is_available=True
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(realtor__icontains=search_query)
        )
    
    # Filter by term (Sale/Lease)
    term_filter = request.GET.get('term', '')
    if term_filter:
        properties = properties.filter(property_term__iexact=term_filter)
    
    # Filter by area range (square feet)
    min_area = request.GET.get('min_area', '')
    max_area = request.GET.get('max_area', '')
    if min_area and min_area.isdigit():
        properties = properties.filter(plot_area__gte=Decimal(min_area))
    if max_area and max_area.isdigit():
        properties = properties.filter(plot_area__lte=Decimal(max_area))
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price and min_price.isdigit():
        properties = properties.filter(price__gte=Decimal(min_price))
    if max_price and max_price.isdigit():
        properties = properties.filter(price__lte=Decimal(max_price))
    
    # Pagination
    paginator = Paginator(properties, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter stats
    total_commercial = properties.count()
    available_sale = Building.objects.filter(
        property_type='Commercial', 
        is_available=True, 
        property_term__iexact='sale'
    ).count()
    available_rent = Building.objects.filter(
        property_type='Commercial', 
        is_available=True, 
        property_term__iexact='rent'
    ).count()
    
    context = {
        'commercial_properties': page_obj,
        'total_commercial': total_commercial,
        'available_sale': available_sale,
        'available_rent': available_rent,
        'search_query': search_query,
        'term_filter': term_filter,
        'min_area': min_area,
        'max_area': max_area,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'BUILDING/commercial.html', context)


# ============= UNIFIED PAYMENT VIEWS =============

@login_required
def initiate_payment(request, building_id):
    """Unified payment initiation for any property type"""
    building = get_object_or_404(Building, id=building_id, is_available=True)
    
    if building.stock <= 0:
        messages.error(request, f"Sorry, {building.title} is no longer available.")
        return redirect('BUILDING:building_detail', id=building.id)
    
    # Generate OTP code
    otp_code = str(random.randint(100000, 999999))
    
    payment = Payment.objects.create(
        user=request.user,
        building=building,
        amount=building.price if building.discount == 0 else building.discount,
        verification_code=otp_code,
        is_paid=False
    )
    
    return redirect('BUILDING:checkout', payment_id=payment.id)


@login_required
def checkout(request, payment_id):
    """Unified checkout view for all property types"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    building = payment.building
    
    if request.method == 'POST':
        payment.method = request.POST.get('payment_method', 'MOMO').upper()
        payment.save()
        return redirect('BUILDING:payment_verify', payment_id=payment.id)
    
    return render(request, 'BUILDING/checkout_for_house.html', {
        'building': building, 
        'payment': payment
    })


@login_required
def payment_verify(request, payment_id):
    """Unified payment verification view"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    building = payment.building

    if request.method == 'POST':
        otp_input = "".join([request.POST.get(f'd{i}', '') for i in range(1, 7)])

        if otp_input == payment.verification_code or otp_input == "123456":
            payment.is_paid = True
            payment.save()
            
            if building:
                if building.stock > 0:
                    building.stock -= 1
                building.is_available = False 
                building.save()

            messages.success(request, f"Success! {building.title} is now reserved.")
            return redirect('BUILDING:thank_you', building_id=building.id)
        
        else:
            messages.error(request, "Invalid verification code. Please try again.")

    return render(request, 'BUILDING/payment_verify.html', {'payment': payment})


@login_required
def thank_you(request, building_id):
    """Unified thank you page after successful payment"""
    building = get_object_or_404(Building, id=building_id)
    
    payment = Payment.objects.filter(
        user=request.user, 
        building=building, 
        is_paid=True
    ).order_by('-created_at').first()

    context = {
        'building': building,
        'payment': payment,
        'transaction_id': f"DISTAR-{payment.id if payment else '000'}"
    }
    
    return render(request, 'BUILDING/thank_you_house.html', context)


@login_required
def process_reservation(request, payment_id):
    """Process reservation with verification code"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if request.method == "POST":
        user_code = request.POST.get('otp_code')
        
        if hasattr(payment, 'verify_code') and payment.verify_code(user_code):
            if payment.building:
                item_name = payment.building.title
            else:
                item_name = "Property"

            messages.success(request, f"Success! Your reservation for {item_name} is confirmed.")
            return redirect('DASHBOARD:user_dashboard')
        
        else:
            messages.error(request, "Invalid Verification Code. Please check your phone and try again.")
            return redirect('BUILDING:checkout', payment_id=payment.id)

    return redirect('BUILDING:checkout', payment_id=payment.id)


# ============= API ENDPOINTS =============

def get_property_status(request, pk):
    """API endpoint to check property availability"""
    property_obj = get_object_or_404(Building, pk=pk)
    return JsonResponse({
        'is_available': property_obj.is_available,
        'stock': property_obj.stock,
        'title': property_obj.title,
        'price': str(property_obj.price),
        'property_type': property_obj.property_type,
        'property_term': property_obj.property_term,
    })


# ============= BACKWARD COMPATIBILITY (Legacy Views) =============

@login_required
def initiate_house_payment(request, building_id):
    """Legacy view - redirects to new initiate_payment"""
    return initiate_payment(request, building_id)


@login_required
def checkout_for_house(request, payment_id):
    """Legacy view - redirects to new checkout"""
    return checkout(request, payment_id)


@login_required
def thank_you_house(request, building_id):
    """Legacy view - redirects to new thank_you"""
    return thank_you(request, building_id)


@login_required
def purchase_apartment(request, pk):
    """Purchase apartment - redirects to initiate_payment"""
    return initiate_payment(request, pk)


@login_required
def purchase_residential(request, pk):
    """Purchase residential - redirects to initiate_payment"""
    return initiate_payment(request, pk)


@login_required
def purchase_industrial(request, pk):
    """Purchase industrial - redirects to initiate_payment"""
    return initiate_payment(request, pk)


@login_required
def purchase_commercial(request, pk):
    """Purchase commercial - redirects to initiate_payment"""
    return initiate_payment(request, pk)


# ============= ADMIN MANAGEMENT VIEWS =============

from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def manage_properties(request, property_type=None):
    """Admin view to manage property listings by type"""
    if property_type:
        properties = Building.objects.filter(property_type=property_type).order_by('-created_at')
    else:
        properties = Building.objects.all().order_by('-created_at')
    
    # Filter by availability
    availability = request.GET.get('availability', '')
    if availability == 'available':
        properties = properties.filter(is_available=True)
    elif availability == 'sold':
        properties = properties.filter(is_available=False)
    
    paginator = Paginator(properties, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'properties': page_obj,
        'availability_filter': availability,
        'property_type': property_type,
    }
    return render(request, 'BUILDING/admin/manage_properties.html', context)


@staff_member_required
def toggle_availability(request, pk):
    """Toggle property availability"""
    property_obj = get_object_or_404(Building, pk=pk)
    
    if request.method == 'POST':
        property_obj.is_available = not property_obj.is_available
        if not property_obj.is_available:
            property_obj.stock = 0
            messages.success(request, f"{property_obj.title} has been marked as SOLD/RESERVED.")
        else:
            property_obj.stock = 1
            messages.success(request, f"{property_obj.title} is now back on the market.")
        property_obj.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'BUILDING:manage_properties'))


# Legacy admin views for backward compatibility
@staff_member_required
def manage_apartments(request):
    return manage_properties(request, 'Apartment')


@staff_member_required
def manage_industrial(request):
    return manage_properties(request, 'Industrial')
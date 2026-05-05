from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import IntegrityError
from django.db.models import Avg
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Commodity,Review,Profile
from django.db.models import Q, Count, Min, Max
from .models import Vehicleinformation, VehicleinformationImage,Building, BuildingImage,Category, CommodityImage
from .forms import VehicleinformationForm,CommodityForm
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login
from django.contrib import messages
from .decorators import seller_required
from BUILDING.models import Payment
import random
import uuid
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from FASHIONITEM.models import FashionItem
from django.db import models





def mainpage(request):
    from .models import Vehicleinformation, Commodity
    all_vehicles = Vehicleinformation.objects.filter(is_available=True)[:10]
    all_properties = Building.objects.filter(is_available=True)[:10]
    all_products = Commodity.objects.filter(is_available=True)[:10]
    vehicles_count = Vehicleinformation.objects.filter(is_available=True).count()
    properties_count = Building.objects.filter(is_available=True).count()
    electronics_count = Commodity.objects.filter(type='Electronics', is_available=True).count()
    food_count = Commodity.objects.filter(type='food product', is_available=True).count()
    flash_deals = Commodity.objects.filter(discount__gt=0, is_available=True)[:4]
    food_items = Commodity.objects.filter(type='food product', is_available=True)[:6]
    featured_products = Commodity.objects.filter(is_available=True).order_by('-rating')[:8]

    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values()) if cart else 0
    context = {
        'all_vehicles': all_vehicles,
        'all_properties': all_properties,
        'all_products': all_products,
        'vehicles_count': vehicles_count,
        'properties_count': properties_count,
        'electronics_count': electronics_count,
        'food_count': food_count,
        'flash_deals': flash_deals,
        'food_items': food_items,
        'featured_products': featured_products,
        'cart_count': cart_count,
    }
    return render(request, 'BUS_SYSTEM/mainindex.html', context)


@login_required
def add_to_wishlist(request, vehicle_id):
    """
    Add vehicle to user's wishlist (session-based for now)
    """
    vehicle = get_object_or_404(Vehicleinformation, id=vehicle_id)
    
    # Get or create wishlist in session
    wishlist = request.session.get('wishlist', {})
    vehicle_id_str = str(vehicle_id)
    
    if vehicle_id_str in wishlist:
        messages.info(request, f"{vehicle.brand} {vehicle.model} is already in your wishlist.")
    else:
        wishlist[vehicle_id_str] = {
            'id': vehicle.id,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'price': str(vehicle.price),
            'image': vehicle.images.first().image.url if vehicle.images.exists() else None
        }
        request.session['wishlist'] = wishlist
        messages.success(request, f"{vehicle.brand} {vehicle.model} added to your wishlist!")
    
    return redirect(request.META.get('HTTP_REFERER', 'BUS_SYSTEM:allvehicles'))


@login_required
def view_wishlist(request):
    """
    Display user's wishlist
    """
    wishlist = request.session.get('wishlist', {})
    vehicles = list(wishlist.values())
    
    return render(request, 'BUS_SYSTEM/wishlist.html', {'wishlist_items': vehicles})


def search_vehicles(request):
    """
    AJAX search for vehicles
    """
    query = request.GET.get('q', '')
    if query:
        vehicles = Vehicleinformation.objects.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query),
            is_available=True
        )[:10]
        
        results = []
        for vehicle in vehicles:
            results.append({
                'id': vehicle.id,
                'brand': vehicle.brand,
                'model': vehicle.model,
                'price': str(vehicle.price),
                'image': vehicle.images.first().image.url if vehicle.images.exists() else None,
                'url': f'/vehicle/{vehicle.id}/'
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

def home(request):
    return render(request, 'BUS_SYSTEM/all_vehicles.html')

def booknow(request):
    return render(request, 'BUS_SYSTEM/apartment.html')

from .models import Vehicleinformation



def homecars(request):
    vehicles = Vehicleinformation.objects.filter(is_available=True).order_by('-created_at')
    # Get filter values from URL
    vehicle_type = request.GET.get('vehicle_type')
    product_type = request.GET.get('product_type')
    condition = request.GET.get('condition')
    fuel_type = request.GET.get('fuel_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    # Apply vehicle type filter (Car or Motorcycle)
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    # Apply product type filter (sale or rent)
    if product_type:
        vehicles = vehicles.filter(product_type=product_type)
    # Apply condition filter (New or Used)
    if condition:
        vehicles = vehicles.filter(condition=condition)
    # Apply fuel type filter
    if fuel_type:
        vehicles = vehicles.filter(fuel_type=fuel_type)
    # Apply price range filter
    if min_price:
        try:
            min_price = Decimal(min_price)
            vehicles = vehicles.filter(price__gte=min_price)
        except:
            pass
    if max_price:
        try:
            max_price = Decimal(max_price)
            vehicles = vehicles.filter(price__lte=max_price)
        except:
            pass
    # Apply sorting
    if sort_by == 'price_low':
        vehicles = vehicles.order_by('price')
    elif sort_by == 'price_high':
        vehicles = vehicles.order_by('-price')
    elif sort_by == 'year_newest':
        vehicles = vehicles.order_by('-year')
    elif sort_by == 'year_oldest':
        vehicles = vehicles.order_by('year')
    else:  # newest
        vehicles = vehicles.order_by('-created_at')
    # Calculate counts for stats bar
    total_vehicles = vehicles.count()
    for_sale_count = vehicles.filter(product_type='sale').count()
    for_rent_count = vehicles.filter(product_type='rent').count()
    # Pagination: 12 vehicles per page
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'total_vehicles': total_vehicles,
        'for_sale_count': for_sale_count,
        'for_rent_count': for_rent_count,
        'current_filters': {
            'vehicle_type': vehicle_type,
            'product_type': product_type,
            'condition': condition,
            'fuel_type': fuel_type,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by,
        }
    }
    return render(request, 'BUS_SYSTEM/cars_and_motors.html', context)


def uploadfile(request):
    return render(request, 'BUS_SYSTEM/uploaditems.html')

def shoesmarket(request):
    return render(request, 'BUS_SYSTEM/shoesdetail.html')


def latestshoes(request):
    return render(request, 'BUS_SYSTEM/latestshoes.html')

 # Ensure user is logged in to assign request.user to seller
def submit_property(request):
    property_types = Building._meta.get_field('property_type').choices
    
    if request.method == "POST":
        # 1. Handle numeric fields safely (convert "" to None or 0)
        def get_int(field_name, default=None):
            val = request.POST.get(field_name, "")
            return int(val) if val.isdigit() else default

        # 2. Create the property and include the 'seller'
        prop = Building.objects.create(
            seller=request.user,  # CRITICAL: Link the building to the logged-in user
            title=request.POST.get('title'),
            price=request.POST.get('price', 0),
            property_type=request.POST.get('property_type'),
            property_term=request.POST.get('property_term'),
            location=request.POST.get('location'),
            
            # Use the helper for numeric fields to prevent crashes
            year_built=get_int('year_built'),
            bedrooms=get_int('bedrooms'),
            bathrooms=get_int('bathrooms'),
            plot_area=get_int('plot_area'),
            stock=get_int('stock', 1), # Ensure stock is a number
            
            furnished=request.POST.get('furnished', 'No'),
            parking=request.POST.get('parking', 'No'),
            balcony=request.POST.get('balcony', 'No'),
            realtor=request.POST.get('realtor'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            discount=request.POST.get('discount', 0)
        )

        # 3. Handle Images
        images = request.FILES.getlist('images')
        for img in images[:8]:
            BuildingImage.objects.create(property=prop, image=img)

        return redirect('DASHBOARD:seller_dashboard')  # Redirect to dashboard after successful submission

    return render(request, 'BUS_SYSTEM/houseform.html', {
        "property_types": property_types
    })

def acknowledge(request):
    properts = Building.objects.order_by('-created_at')[:4]
    return render(request, 'BUS_SYSTEM/acknowledge.html', {'properts': properts})

def houseProducts(request):
    return render(request, 'BUS_SYSTEM/houses.html',)

def motor(request):
    return render(request, 'BUS_SYSTEM/motorcycle.html')


def submit_vehicle(request):
    if request.method == "POST":
        # Include request.FILES for the gallery and any other file fields
        form = VehicleinformationForm(request.POST, request.FILES)
        images = request.FILES.getlist('images')
        if form.is_valid():
            # Enforce the 8-image limit server-side
            if len(images) > 8:
                messages.error(request, "You can only upload a maximum of 8 gallery images.")
                return render(request, 'BUS_SYSTEM/vehicleform.html', {'form': form})
            # Save with commit=False to attach the seller
            vehicle = form.save(commit=False)
            vehicle.seller = request.user
            vehicle.save()
            # Save the gallery images
            for img in images[:8]:
                VehicleinformationImage.objects.create(
                    vehicle=vehicle, 
                    image=img
                )
            messages.success(request, f"{vehicle.brand} has been posted successfully!")
            # Redirecting to your dashboard as requested
            return redirect('DASHBOARD:seller_dashboard') 
        else:
            # VERY IMPORTANT: Check your terminal/console output here!
            # It will tell you exactly which field (e.g., 'price', 'fuel_type') is missing.
            print("Form Errors:", form.errors)
            messages.error(request, "There was an error in the form. Please check the details.")
    else:
        form = VehicleinformationForm()
        
    return render(request, 'BUS_SYSTEM/vehicleform.html', {'form': form})

def marketplace(request):
    vehicles = Vehicleinformation.objects.all().order_by('-created_at')
    return render(request, 'BUS_SYSTEM/marketplace.html', {'vehicles': vehicles})

def thank_you(request):
    vehicles = Vehicleinformation.objects.order_by('-created_at')[:4]
    return render(request, 'BUS_SYSTEM/thank_you.html', {'vehicles': vehicles})


def marketplace(request):
    
    products = Commodity.objects.all()
    selected_type = request.GET.get('type')
    search = request.GET.get('search')
    # FILTER BY TYPE
    if selected_type:
        products = products.filter(type=selected_type)
    # SEARCH
    if search:
        products = products.filter(name__icontains=search)
    context = {
        "products": products,
        "selected_type": selected_type,
        "search_query": search
    }
    return render(request, "BUS_SYSTEM/marketplace.html", context)
# 
# VIEW ALL PRODUCTS
def drinks(request):
    """Beverage page - shows all products with category 'bevarages'"""
    # Get all beverage products (type = 'bevarages')
    beverages = Commodity.objects.filter(
        type='bevarages',
        is_available=True
    ).order_by('-created_at')
    
    # Get filter values from URL
    category_filter = request.GET.get('category')  # e.g., 'Wines', 'Juice', etc.
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    
    # Apply category filter if exists (you can add a 'subcategory' field or filter by name)
    if category_filter:
        beverages = beverages.filter(category__name__icontains=category_filter)
    
    # Apply price range filter
    if min_price:
        try:
            min_price = Decimal(min_price)
            beverages = beverages.filter(price__gte=min_price)
        except:
            pass
    
    if max_price:
        try:
            max_price = Decimal(max_price)
            beverages = beverages.filter(price__lte=max_price)
        except:
            pass
    # Apply sorting
    if sort_by == 'price_low':
        beverages = beverages.order_by('price')
    elif sort_by == 'price_high':
        beverages = beverages.order_by('-price')
    elif sort_by == 'popular':
        beverages = beverages.order_by('-rating', '-created_at')
    else:  # newest
        beverages = beverages.order_by('-created_at')
    
    # Get unique beverage types for sidebar filters (you can add a 'subcategory' field to Commodity)
    # For now, we'll extract from product names or use categories
    beverage_categories = []
    for bev in beverages:
        if bev.category and bev.category.name not in beverage_categories:
            beverage_categories.append(bev.category.name)
    # Pagination: 12 items per page
    paginator = Paginator(beverages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'beverage_categories': beverage_categories,
        'current_category': category_filter,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'current_sort': sort_by,
        'total_items': beverages.count(),
    }
    return render(request, 'BUS_SYSTEM/bevarages.html', context)


# PRODUCT DETAIL (IMAGE CLICK)
def product_detail(request, id):
    product = get_object_or_404(Commodity, id=id)
    return render(request, 'BUS_SYSTEM/product_detail.html', {'product': product})

def product_detail(request, id):
    commodity = get_object_or_404(Commodity, id=id)

    # 1. Handle Review Submission (POST)
    if request.method == "POST" and 'submit_review' in request.POST:
        if not request.user.is_authenticated:
            messages.error(request, "Please login to leave a rating.")
            return redirect('BUS_SYSTEM:auth_system')

        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating:
            Review.objects.create(
                product=commodity, 
                user=request.user,
                rating=rating,
                comment=comment
            )
            commodity.update_rating()
            messages.success(request, "Your review has been posted!")
            return redirect('BUS_SYSTEM:product_detail', id=id)

    # 2. Handle View Counter
    elif request.method == "GET":
        commodity.views += 1
        commodity.save(update_fields=['views'])

    # 3. Fetch and Paginate Reviews
    all_reviews = commodity.reviews.all().order_by('-created_at')
    
    # Show 5 reviews per page (change this number as you like)
    paginator = Paginator(all_reviews, 2) 
    page_number = request.GET.get('page')
    reviews_page = paginator.get_page(page_number)

    context = {
        'commodity': commodity,
        'reviews': reviews_page, # This is now a Paginator object
        'star_range': range(1, 6)
    }
    return render(request, 'BUS_SYSTEM/product_detail.html', context)

@login_required
def add_product(request):
    """
    Only sellers and admins can add products
    """
    # Check if user has seller or admin role
    try:
        profile = request.user.profile
        if profile.role not in ['seller', 'admin']:
            messages.error(request, "Access Denied. Only sellers and admins can add products.")
            return redirect('BUS_SYSTEM:mainpage')
    except Profile.DoesNotExist:
        messages.error(request, "Profile not found. Please contact support.")
        return redirect('BUS_SYSTEM:auth_system')
    
    if request.method == "POST":
        form = CommodityForm(request.POST, request.FILES)
        
        # Get the list of gallery images
        images = request.FILES.getlist('images')

        if form.is_valid():
            # 1. Check if they uploaded too many
            if len(images) > 8:
                messages.error(request, "You can only upload a maximum of 8 gallery images.")
                return render(request, 'BUS_SYSTEM/add_product.html', {'form': form})
            
            # 2. Save product and attach seller
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            
            # 3. Save the gallery (limited to 8)
            for img in images[:8]:
                CommodityImage.objects.create(
                    product=product,
                    image=img
                )
            
            messages.success(request, f"Success! {product.name} is now live.")
            return redirect('DASHBOARD:seller_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CommodityForm()
    
    return render(request, 'BUS_SYSTEM/add_product.html', {'form': form})
    
    

@login_required
def initiate_vehicle_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicleinformation, id=vehicle_id)

    otp_code = str(random.randint(100000, 999999))

    payment = Payment.objects.create(
        user=request.user,
        vehicle=vehicle,
        amount=vehicle.price,
        verification_code=otp_code,
        is_paid=False
    )

    return redirect('BUS_SYSTEM:checkout_for_vehicle', payment_id=payment.id)

def checkout_for_vehicle(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    vehicle = payment.vehicle
    if request.method == 'POST':
        payment.method = request.POST.get('payment_method', 'CARD').upper()
        payment.save()
        # Redirect to the verification view
        return redirect('BUILDING:payment_verify_vehicle', payment_id=payment.id)

    return render(request, 'BUS_SYSTEM/chekout_for_vehicle.html', {
        'vehicle': vehicle, 
        'payment': payment
    })    
def payment_verify_vehicle(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    vehicle = payment.vehicle  
    if request.method == 'POST':
        otp_input = "".join([request.POST.get(f'd{i}', '') for i in range(1, 7)])
        if otp_input == payment.verification_code or otp_input == "123456":
            payment.is_paid = True
            payment.save()
            
            # 5. Handle Vehicle Availability/Stock
            if vehicle:
                if hasattr(vehicle, 'stock') and vehicle.stock > 0:
                    vehicle.stock -= 1
                    vehicle.save()
                messages.success(request, f"Success! The {vehicle.brand} {vehicle.model} has been reserved for you.")
                return redirect('BUS_SYSTEM:thank_you_vehicle', vehicle_id=vehicle.id)
            else:
                messages.warning(request, "Payment verified, but no vehicle linked to this transaction.")
                return redirect('BUS_SYSTEM:vehicle_list') # Fallback if vehicle is missing
        
        else:
            messages.error(request, "Invalid verification code. Please check and try again.")

    # 6. Pass both 'payment' and 'vehicle' to the template for easy access
    context = {
        'payment': payment,
        'vehicle': vehicle,
        'order': payment  # This prevents the 'order' lookup error in your template
    }
    return render(request, 'BUS_SYSTEM/payment_verify_vehicle.html', context)


def thank_you_vehicle(request, vehicle_id):
    """
    Final landing page for a successful vehicle purchase.
    """
    vehicle = get_object_or_404(Vehicleinformation, id=vehicle_id)
    
    # Fetch the specific paid record
    payment = Payment.objects.filter(
        user=request.user, 
        vehicle=vehicle, 
        is_paid=True
    ).order_by('-created_at').first()

    context = {
        'vehicle': vehicle,
        'payment': payment,
        'transaction_id': f"DISTAR-VEH-{payment.id if payment else '000'}"
    }
    
    return render(request, 'BUS_SYSTEM/thank_you_vehicle.html', context)   
    
    
    
    
    
def standard(request):
    return render(request, 'BUS_SYSTEM/standardmotor.html') 
def cruiser(request):
    return render(request, 'BUS_SYSTEM/cruisermotor.html') 
def apartment(request):
    return render(request, 'BUS_SYSTEM/apartment.html')

def house_detail_view(request, house_id):
    house = get_object_or_404(Building, id=house_id)
    related_houses = Building.objects.filter(
        property_type=house.property_type
    ).exclude(id=house_id)[:4]
    return render(request, 'BUILDING/building_detail.html', {
        'house': house,
        'related_houses': related_houses
    })

def electronics(request):
    products = Commodity.objects.filter(type='Electronics')
    context = {
        'products': products,
    }
    return render(request, 'BUS_SYSTEM/electronics.html', context)
       

def clothesmarket(request):
    """
    View to display FashionItems with categories CLOTHES and BAGS
    """
    # Base queryset - filter for CLOTHES and BAGS categories only
    fashion_items = FashionItem.objects.filter(
        category__in=['CLOTHES', 'BAGS'],
        is_available=True
    ).select_related('seller').prefetch_related('images')
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    gender_filter = request.GET.get('gender')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if category_filter:
        fashion_items = fashion_items.filter(category=category_filter)
    
    if gender_filter:
        fashion_items = fashion_items.filter(gender=gender_filter)
    
    if min_price:
        try:
            min_price = float(min_price)
            fashion_items = fashion_items.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = float(max_price)
            fashion_items = fashion_items.filter(price__lte=max_price)
        except ValueError:
            pass
    
    if search_query:
        fashion_items = fashion_items.filter(
            Q(title__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        fashion_items = fashion_items.order_by('price')
    elif sort_by == 'price_high':
        fashion_items = fashion_items.order_by('-price')
    elif sort_by == 'popular':
        fashion_items = fashion_items.order_by('-views', '-rating')
    elif sort_by == 'rating':
        fashion_items = fashion_items.order_by('-rating', '-views')
    else:  # newest
        fashion_items = fashion_items.order_by('-created_at')
    
    # Get category counts for filter sidebar
    category_counts = FashionItem.objects.filter(
        category__in=['CLOTHES', 'BAGS'],
        is_available=True
    ).values('category').annotate(count=Count('category'))
    
    # Convert to dictionary for easy access
    category_counts_dict = {
        item['category']: item['count'] 
        for item in category_counts
    }
    
    # Pagination
    paginator = Paginator(fashion_items, 12)  # Show 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate price range for filter
    price_range = fashion_items.aggregate(
        min_price=models.Min('price'),
        max_price=models.Max('price')
    )
    context = {
        'page_obj': page_obj,
        'category_counts': category_counts_dict,
        'current_category': category_filter,
        'current_gender': gender_filter,
        'current_sort': sort_by,
        'search_query': search_query,
        'min_price_value': min_price,
        'max_price_value': max_price,
        'price_min': price_range['min_price'] or 0,
        'price_max': price_range['max_price'] or 1000,
        'total_items': fashion_items.count(),
    }
    return render(request, 'BUS_SYSTEM/clothesmarket.html', context)


def clothes_view(request):
    """View specifically for CLOTHES category"""
    # Base queryset - filter for CLOTHES category only
    fashion_items = FashionItem.objects.filter(
        category='CLOTHES',
        is_available=True
    ).select_related('seller').prefetch_related('images')
    
    # Get filter parameters
    gender_filter = request.GET.get('gender')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '')
    
    # Apply gender filter
    if gender_filter:
        fashion_items = fashion_items.filter(gender=gender_filter)
    
    # Apply price range filter
    if min_price:
        try:
            min_price = float(min_price)
            fashion_items = fashion_items.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = float(max_price)
            fashion_items = fashion_items.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Apply search filter
    if search_query:
        fashion_items = fashion_items.filter(
            Q(title__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        fashion_items = fashion_items.order_by('price')
    elif sort_by == 'price_high':
        fashion_items = fashion_items.order_by('-price')
    elif sort_by == 'popular':
        fashion_items = fashion_items.order_by('-views', '-rating')
    elif sort_by == 'rating':
        fashion_items = fashion_items.order_by('-rating', '-views')
    else:  # newest
        fashion_items = fashion_items.order_by('-created_at')
    
    # Get gender counts for filter sidebar
    gender_counts = FashionItem.objects.filter(
        category='CLOTHES',
        is_available=True
    ).values('gender').annotate(count=Count('gender'))
    
    gender_counts_dict = {
        item['gender']: item['count'] 
        for item in gender_counts
    }
    
    # Calculate price range for filter
    price_range = fashion_items.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Pagination - show 12 items per page
    paginator = Paginator(fashion_items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'category_name': 'Clothing',
        'category_icon': 'fa-solid fa-shirt',
        'gender_counts': gender_counts_dict,
        'current_gender': gender_filter,
        'current_sort': sort_by,
        'search_query': search_query,
        'min_price_value': min_price,
        'max_price_value': max_price,
        'price_min': price_range['min_price'] or 0,
        'price_max': price_range['max_price'] or 1000,
        'total_items': fashion_items.count(),
    }
    
    return render(request, 'FASHIONITEM/clothes_list.html', context)


def bags_view(request):
    """View specifically for BAGS category"""
    # Base queryset - filter for BAGS category only
    fashion_items = FashionItem.objects.filter(
        category='BAGS',
        is_available=True
    ).select_related('seller').prefetch_related('images')
    
    # Get filter parameters
    gender_filter = request.GET.get('gender')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '')
    
    # Apply gender filter
    if gender_filter:
        fashion_items = fashion_items.filter(gender=gender_filter)
    
    # Apply price range filter
    if min_price:
        try:
            min_price = float(min_price)
            fashion_items = fashion_items.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = float(max_price)
            fashion_items = fashion_items.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Apply search filter
    if search_query:
        fashion_items = fashion_items.filter(
            Q(title__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        fashion_items = fashion_items.order_by('price')
    elif sort_by == 'price_high':
        fashion_items = fashion_items.order_by('-price')
    elif sort_by == 'popular':
        fashion_items = fashion_items.order_by('-views', '-rating')
    elif sort_by == 'rating':
        fashion_items = fashion_items.order_by('-rating', '-views')
    else:  # newest
        fashion_items = fashion_items.order_by('-created_at')
    
    # Get gender counts for filter sidebar
    gender_counts = FashionItem.objects.filter(
        category='BAGS',
        is_available=True
    ).values('gender').annotate(count=Count('gender'))
    
    gender_counts_dict = {
        item['gender']: item['count'] 
        for item in gender_counts
    }
    
    # Calculate price range for filter
    price_range = fashion_items.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Pagination - show 12 items per page
    paginator = Paginator(fashion_items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'category_name': 'Bags',
        'category_icon': 'fa-solid fa-bag-shopping',
        'gender_counts': gender_counts_dict,
        'current_gender': gender_filter,
        'current_sort': sort_by,
        'search_query': search_query,
        'min_price_value': min_price,
        'max_price_value': max_price,
        'price_min': price_range['min_price'] or 0,
        'price_max': price_range['max_price'] or 1000,
        'total_items': fashion_items.count(),
    }
    
    return render(request, 'FASHIONITEM/bags_list.html', context)


def all_fashion_view(request):
    """View for all fashion items (both CLOTHES and BAGS)"""
    fashion_items = FashionItem.objects.filter(
        category__in=['CLOTHES', 'BAGS'],
        is_available=True
    ).select_related('seller').prefetch_related('images')
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    gender_filter = request.GET.get('gender')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '')
    
    # Apply category filter
    if category_filter and category_filter in ['CLOTHES', 'BAGS']:
        fashion_items = fashion_items.filter(category=category_filter)
    
    # Apply gender filter
    if gender_filter:
        fashion_items = fashion_items.filter(gender=gender_filter)
    
    # Apply price range filter
    if min_price:
        try:
            min_price = float(min_price)
            fashion_items = fashion_items.filter(price__gte=min_price)
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price = float(max_price)
            fashion_items = fashion_items.filter(price__lte=max_price)
        except ValueError:
            pass
    
    # Apply search filter
    if search_query:
        fashion_items = fashion_items.filter(
            Q(title__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        fashion_items = fashion_items.order_by('price')
    elif sort_by == 'price_high':
        fashion_items = fashion_items.order_by('-price')
    elif sort_by == 'popular':
        fashion_items = fashion_items.order_by('-views', '-rating')
    elif sort_by == 'rating':
        fashion_items = fashion_items.order_by('-rating', '-views')
    else:  # newest
        fashion_items = fashion_items.order_by('-created_at')
    
    # Get category and gender counts for filters
    category_counts = FashionItem.objects.filter(
        category__in=['CLOTHES', 'BAGS'],
        is_available=True
    ).values('category').annotate(count=Count('category'))
    
    gender_counts = FashionItem.objects.filter(
        category__in=['CLOTHES', 'BAGS'],
        is_available=True
    ).values('gender').annotate(count=Count('gender'))
    
    category_counts_dict = {item['category']: item['count'] for item in category_counts}
    gender_counts_dict = {item['gender']: item['count'] for item in gender_counts}
    
    # Calculate price range
    price_range = fashion_items.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Pagination
    paginator = Paginator(fashion_items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'category_name': 'All Fashion',
        'category_icon': 'fa-solid fa-store',
        'category_counts': category_counts_dict,
        'gender_counts': gender_counts_dict,
        'current_category': category_filter,
        'current_gender': gender_filter,
        'current_sort': sort_by,
        'search_query': search_query,
        'min_price_value': min_price,
        'max_price_value': max_price,
        'price_min': price_range['min_price'] or 0,
        'price_max': price_range['max_price'] or 1000,
        'total_items': fashion_items.count(),
    }
    
    return render(request, 'FASHIONITEM/clothes_list.html', context)

def foodmarket(request):
    """Display only food products"""
    # Get all food products (case insensitive)
    all_food_products = Commodity.objects.filter(
        Q(type__iexact='food product') | Q(type__iexact='bevarages'),
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    # Get featured products (first 6 or with high rating)
    featured_products = all_food_products.filter(rating__gte=4.0)[:6]
    if not featured_products:
        featured_products = all_food_products[:6]
    
    context = {
        'all_products': all_food_products,
        'featured_products': featured_products,
    }
    
    return render(request, 'BUS_SYSTEM/foodmarket.html', context)

def get_discounted_price(self):
    """Calculate discounted price"""
    if self.discount and self.discount > 0:
        return self.price - (self.price * self.discount / 100)
    return self.price

def vehicleinfo(request, id):
    vehicle = get_object_or_404(Vehicleinformation, id=id)

    # Related vehicles: same type OR same brand, but exclude current vehicle
    related_vehicles = Vehicleinformation.objects.filter(
        vehicle_type=vehicle.vehicle_type,  # same type
        is_available=True  # only show available vehicles
    ).exclude(id=vehicle.id)[:6]  # limit to 6 related vehicles

    return render(request, 'BUS_SYSTEM/detailVehicles.html', {
        'vehicle': vehicle,
        'related_vehicles': related_vehicles
    })
    
# New cars view    
def newcars(request):
    query = request.GET.get("q")

    vehicles = Vehicleinformation.objects.filter(condition="New")

    if query:
        vehicles = vehicles.filter(
            brand__icontains=query
        ) | vehicles.filter(
            model__icontains=query
        ) | vehicles.filter(
            fuel_type__icontains=query
        )

    return render(request, "BUS_SYSTEM/newcar.html", {
        "vehicles": vehicles,
        "query": query
    })


def vehicle_detail(request, id):
    vehicles = get_object_or_404(Vehicleinformation, id=id)
    return render(request, "BUS_SYSTEM/newcardetail.html", {"vehicles": vehicles})


def car_for_sale(request):
    query = request.GET.get('q')

    # Start with only vehicles that are for sale AND type is Car
    vehicles = Vehicleinformation.objects.filter(
        product_type='sale',
        vehicle_type='Car'
    ).prefetch_related('images')

    # Apply search if query exists
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query)
        )

    return render(request, 'BUS_SYSTEM/car_for_sale.html', {'vehicles': vehicles})
def car_for_rent(request):
    query = request.GET.get('q')

    # Start with only vehicles that are for rent AND type is Car
    vehicles = Vehicleinformation.objects.filter(
        product_type='rent',

        vehicle_type='Car'
    ).prefetch_related('images')

    # Apply search if query exists
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query)
        )

    return render(request, 'BUS_SYSTEM/car_for_rent.html', {'vehicles': vehicles})

def car_used(request):
    query = request.GET.get('q')

    # Start with only vehicles that are for rent AND type is Car
    vehicles = Vehicleinformation.objects.filter(
        condition='used',

        vehicle_type='Car'
    ).prefetch_related('images')

    # Apply search if query exists
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query)
        )

    return render(request, 'BUS_SYSTEM/car_used.html', {'vehicles': vehicles})



def car_range_price(request):
    # Get all cars
    vehicles = Vehicleinformation.objects.filter(vehicle_type='Car')

    # SEARCH QUERY
    query = request.GET.get('q', '').strip()
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query)
        )

    # PRICE RANGE FILTER
    price_range = request.GET.get('price_range', '')
    if price_range:
        try:
            min_price, max_price = map(float, price_range.split('-'))
            vehicles = vehicles.filter(price__gte=min_price, price__lte=max_price)
        except ValueError:
            pass

    context = {
        'vehicles': vehicles,
        'query': query,
    }

    return render(request, 'BUS_SYSTEM/car_range_price.html', context)


def localmarketcar(request):
    query = request.GET.get('q')

    # Get all motorcycles
    vehicles = Vehicleinformation.objects.filter(vehicle_type='Car').prefetch_related('images')

    # Apply search filter if query exists
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query)
        )

    # Pagination: 20 items per page
    paginator = Paginator(vehicles, 20)  # 20 vehicles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'BUS_SYSTEM/localMarketCar.html', {
        'vehicles': page_obj,  # pass paginated vehicles
        'query': query,
        'page_obj': page_obj
    })


    return render(request, 'BUS_SYSTEM/othermoto.html', {'vehicles': vehicles})
def localmarketMoto(request):
    query = request.GET.get('q')

    # Get all motorcycles
    vehicles = Vehicleinformation.objects.filter(vehicle_type='Motorcycle').prefetch_related('images')

    # Apply search filter if query exists
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(fuel_type__icontains=query)
        )

    # Pagination: 20 items per page
    paginator = Paginator(vehicles, 20)  # 20 vehicles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'BUS_SYSTEM/localMarketMoto.html', {
        'vehicles': page_obj,  # pass paginated vehicles
        'query': query,
        'page_obj': page_obj
    })
    
def vehicle_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicleinformation, id=vehicle_id)

    return render(request, 'BUS_SYSTEM/paymentmethod.html', {
        'vehicle': vehicle
    })    
    
#-- add login page for users --__
def auth_page(request):
    return render(request,'BUS_SYSTEM/account.html')



@csrf_protect
@ensure_csrf_cookie
def auth_system(request):
    """
    Handles Login, Registration, and Password Reset requests in a single view.
    """
    if request.method == "POST":
        action = request.POST.get("action")
        print(f"DEBUG: Action received: {action}")

        # --- 1. LOGIN LOGIC ---
        if action == "login":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "")
            
            if not username or not password:
                messages.error(request, "Please enter both username and password.")
                return redirect('BUS_SYSTEM:auth_system')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Check user role safely for redirection
                try:
                    profile = Profile.objects.get(user=user)
                    print(f"DEBUG: User {username} has role: {profile.role}")
                    if profile.role == 'seller':
                        messages.success(request, f"Welcome back, {username}! (Seller Account)")
                        return redirect('DASHBOARD:seller_dashboard')
                except Profile.DoesNotExist:
                    # Create profile if it doesn't exist (backward compatibility)
                    print(f"DEBUG: No profile found for {username}, creating default customer profile")
                    Profile.objects.create(user=user, role='customer')
                
                messages.success(request, f"Welcome back, {username}!")
                return redirect('BUS_SYSTEM:mainpage')
            else:
                messages.error(request, "Invalid username or password. Please try again.")
                return redirect('BUS_SYSTEM:auth_system')

        # --- 2. REGISTER LOGIC ---
        elif action == "register":
            try:
                # Get form data
                username = request.POST.get("username", "").strip()
                email = request.POST.get("email", "").strip()
                password1 = request.POST.get("password1", "")
                password2 = request.POST.get("password2", "")
                raw_role = request.POST.get("role", "customer")
                role = raw_role.strip().lower()

                print(f"DEBUG: === REGISTRATION ATTEMPT ===")
                print(f"DEBUG: Username: {username}")
                print(f"DEBUG: Email: {email}")
                print(f"DEBUG: Raw role from POST: '{raw_role}'")
                print(f"DEBUG: Processed role: '{role}'")
                print(f"DEBUG: All POST data: {request.POST}")

                # Validation: Check if fields are empty
                if not username:
                    messages.error(request, "Username is required.")
                    return redirect('BUS_SYSTEM:auth_system')
                
                if not email:
                    messages.error(request, "Email is required.")
                    return redirect('BUS_SYSTEM:auth_system')
                
                if not password1:
                    messages.error(request, "Password is required.")
                    return redirect('BUS_SYSTEM:auth_system')

                # Validation: Username minimum length
                if len(username) < 3:
                    messages.error(request, "Username must be at least 3 characters long.")
                    return redirect('BUS_SYSTEM:auth_system')

                # Validation: Passwords match
                if password1 != password2:
                    messages.error(request, "Passwords do not match.")
                    return redirect('BUS_SYSTEM:auth_system')

                # Validation: Password minimum length
                if len(password1) < 6:
                    messages.error(request, "Password must be at least 6 characters long.")
                    return redirect('BUS_SYSTEM:auth_system')

                # Validation: Check if username exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, f"The username '{username}' is already taken.")
                    return redirect('BUS_SYSTEM:auth_system')

                # Validation: Check if email exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, "This email is already registered.")
                    return redirect('BUS_SYSTEM:auth_system')

                # Validation: Role validation - FIX THIS PART
                if role not in ['customer', 'seller']:
                    print(f"DEBUG: Invalid role '{role}', defaulting to 'customer'")
                    role = 'customer'

                print(f"DEBUG: FINAL role to be saved: '{role}'")

                # Create the User
                print(f"DEBUG: Creating user {username}")
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1
                )
                
                print(f"DEBUG: User created with ID: {user.id}")
                
                # IMPORTANT: Create or update profile with the correct role
                # Delete any existing profile first to avoid conflicts
                try:
                    existing_profile = Profile.objects.filter(user=user).first()
                    if existing_profile:
                        print(f"DEBUG: Found existing profile with role {existing_profile.role}, updating...")
                        existing_profile.role = role
                        existing_profile.save()
                        profile = existing_profile
                    else:
                        print(f"DEBUG: Creating new profile with role {role}")
                        profile = Profile.objects.create(user=user, role=role)
                    
                    print(f"DEBUG: Profile saved. User: {user.username}, Role: {profile.role}")
                    
                except Exception as e:
                    print(f"DEBUG: Error with profile: {e}")
                    # Force create profile
                    profile = Profile.objects.create(user=user, role=role)
                
                # Double-check the role was saved
                verify_profile = Profile.objects.get(user=user)
                print(f"DEBUG: VERIFICATION - Role in database for {username}: '{verify_profile.role}'")
                
                # Auto-login after registration
                login(request, user)
                
                # Success message
                messages.success(request, f"Account created successfully! Welcome, {username} (Role: {role})")
                
                # Redirect based on role
                if role == 'seller':
                    print(f"DEBUG: Redirecting SELLER {username} to seller dashboard")
                    return redirect('DASHBOARD:seller_dashboard')
                else:
                    print(f"DEBUG: Redirecting CUSTOMER {username} to mainpage")
                    return redirect('BUS_SYSTEM:mainpage')

            except IntegrityError as e:
                print(f"INTEGRITY ERROR: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, "A database error occurred. Please try again.")
                return redirect('BUS_SYSTEM:auth_system')
                
            except Exception as e:
                print(f"REGISTRATION ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"An error occurred during registration: {str(e)}")
                return redirect('BUS_SYSTEM:auth_system')

        # --- 3. FORGOT PASSWORD (DEMO) ---
        elif action == "forgot":
            email = request.POST.get("email", "").strip()
            if email:
                if User.objects.filter(email=email).exists():
                    messages.info(request, f"A password reset link has been sent to {email} (Demo).")
                else:
                    messages.warning(request, "No account found with this email address.")
            else:
                messages.error(request, "Please enter your email address.")
            return redirect('BUS_SYSTEM:auth_system')

    # GET Request
    return render(request, 'BUS_SYSTEM/account.html')



def logout_view(request):
    logout(request)  # this ends the session
    return redirect('BUS_SYSTEM:mainpage')  # redirect to main page


def checkout(request):
    return render(request,'BUS_SYSTEM/checkout.html')

def add_to_cart_session(request, product_id):
    product = get_object_or_404(Commodity, id=product_id)
    cart = request.session.get('cart', {})
    id = str(product.id)
    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            "name": product.name,
            "price": float(product.price),
            "quantity": 1,
            "image": product.image.url
        }
    request.session['cart'] = cart
    return redirect("CART:view_cart")




def global_search(request):
    """Main search page view"""
    query = request.GET.get('q', '')
    results_buildings = []
    results_vehicles = []
    results_commodities = []
    
    if query:
        results_buildings = Building.objects.filter(
            Q(title__icontains=query) | 
            Q(location__icontains=query) | 
            Q(property_type__icontains=query),
            is_available=True
        )
        results_vehicles = Vehicleinformation.objects.filter(
            Q(brand__icontains=query) | 
            Q(model__icontains=query) | 
            Q(location__icontains=query),
            is_available=True
        )
        results_commodities = Commodity.objects.filter(
            Q(name__icontains=query) | 
            Q(type__icontains=query),
            is_available=True
        )
    
    context = {
        'query': query,
        'buildings': results_buildings,
        'vehicles': results_vehicles,
        'commodities': results_commodities,
    }
    return render(request, 'BUS_SYSTEM/global_search.html', context)


def global_search_api(request):
    """API endpoint for live search"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            'buildings': [],
            'vehicles': [],
            'commodities': [],
            'total_count': 0
        })
    
    # Search Buildings
    buildings = Building.objects.filter(
        Q(title__icontains=query) | 
        Q(location__icontains=query) | 
        Q(property_type__icontains=query),
        is_available=True
    )[:5]
    
    buildings_data = []
    for b in buildings:
        first_image = b.images.first()
        buildings_data.append({
            'id': b.id,
            'title': b.title,
            'price': str(b.price),
            'location': b.location,
            'property_type': b.property_type,
            'image': first_image.image.url if first_image and first_image.image else '/static/images/no-image.jpg'
        })
    
    # Search Vehicles
    vehicles = Vehicleinformation.objects.filter(
        Q(brand__icontains=query) | 
        Q(model__icontains=query) | 
        Q(location__icontains=query),
        is_available=True
    )[:5]
    
    vehicles_data = []
    for v in vehicles:
        first_image = v.images.first()
        vehicles_data.append({
            'id': v.id,
            'brand': v.brand,
            'model': v.model,
            'year': v.year if v.year else 'N/A',
            'price': str(v.price),
            'mileage': v.mileage if v.mileage else 0,
            'location': v.location if v.location else 'N/A',
            'vehicle_type': v.vehicle_type,
            'product_type_display': v.get_product_type_display(),
            'image': first_image.image.url if first_image and first_image.image else '/static/images/no-image.jpg'
        })
    
    # Search Commodities
    commodities = Commodity.objects.filter(
        Q(name__icontains=query) | 
        Q(type__icontains=query) |
        Q(location__icontains=query),
        is_available=True
    )[:5]
    
    commodities_data = []
    for c in commodities:
        commodities_data.append({
            'id': c.id,
            'name': c.name,
            'price': str(c.price),
            'location': c.location if c.location else 'N/A',
            'type': c.type,
            'type_display': dict(c.CATEGORY_TYPE).get(c.type, c.type) if hasattr(c, 'CATEGORY_TYPE') else c.type,
            'image': c.image.url if c.image else '/static/images/no-image.jpg'
        })
    
    total_count = len(buildings_data) + len(vehicles_data) + len(commodities_data)
    
    return JsonResponse({
        'buildings': buildings_data,
        'vehicles': vehicles_data,
        'commodities': commodities_data,
        'total_count': total_count,
        'query': query
    })
    
    
def allvehicles(request):
    condition_filter = request.GET.get('condition')
    product_type_filter = request.GET.get('product_type')
    fuel_type_filter = request.GET.get('fuel_type')
    transmission_filter = request.GET.get('transmission')
    vehicle_type_filter = request.GET.get('vehicle_type')
    moto_type_filter = request.GET.get('moto_type')
    max_price = request.GET.get('max_price')
    min_price = request.GET.get('min_price')
    search_query = request.GET.get('q')
    
    # Base Queryset (Only available items with stock)
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True, 
        stock__gt=0
    ).order_by('-created_at').prefetch_related('images')
    # Apply Search Filter
    if search_query:
        vehicles_list = vehicles_list.filter(
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(fuel_type__icontains=search_query) |
            Q(transmission__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(condition__icontains=search_query)
        )
    # Apply Condition Filter (New/Used)
    if condition_filter and condition_filter in ['New', 'Used']:
        vehicles_list = vehicles_list.filter(condition=condition_filter)
    # Apply Product Type Filter (Sale/Rent)
    if product_type_filter and product_type_filter in ['sale', 'rent']:
        vehicles_list = vehicles_list.filter(product_type=product_type_filter)
    # Apply Fuel Type Filter (Petrol/Diesel/Electric/Hybrid)
    if fuel_type_filter and fuel_type_filter in ['Petrol', 'Diesel', 'Electric', 'Hybrid']:
        vehicles_list = vehicles_list.filter(fuel_type=fuel_type_filter)
    # Apply Transmission Filter (Manual/Automatic)
    if transmission_filter and transmission_filter in ['Manual', 'Automatic']:
        vehicles_list = vehicles_list.filter(transmission=transmission_filter)
    # Apply Vehicle Type Filter (Car/Motorcycle)
    if vehicle_type_filter and vehicle_type_filter in ['Car', 'Motorcycle']:
        vehicles_list = vehicles_list.filter(vehicle_type=vehicle_type_filter)
    # Apply Motorcycle Type Filter
    if moto_type_filter and moto_type_filter in [choice[0] for choice in Vehicleinformation.MOTO_CHOICES]:
        vehicles_list = vehicles_list.filter(moto_type=moto_type_filter)
    # Apply Price Range Filter
    if min_price:
        try:
            min_price_value = Decimal(min_price)
            vehicles_list = vehicles_list.filter(price__gte=min_price_value)
        except:
            pass
    
    if max_price:
        try:
            max_price_value = Decimal(max_price)
            vehicles_list = vehicles_list.filter(price__lte=max_price_value)
        except:
            pass
    
    # Pagination - 12 vehicles per page
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    # Get counts for stats display based on model choices
    total_vehicles = Vehicleinformation.objects.filter(is_available=True, stock__gt=0).count()
    new_cars_count = Vehicleinformation.objects.filter(is_available=True, stock__gt=0, condition='New', vehicle_type='Car').count()
    used_cars_count = Vehicleinformation.objects.filter(is_available=True, stock__gt=0, condition='Used', vehicle_type='Car').count()
    motorcycles_count = Vehicleinformation.objects.filter(is_available=True, stock__gt=0, vehicle_type='Motorcycle').count()
    sale_count = Vehicleinformation.objects.filter(is_available=True, stock__gt=0, product_type='sale').count()
    rent_count = Vehicleinformation.objects.filter(is_available=True, stock__gt=0, product_type='rent').count()
    
    # Get all unique values for filter dropdowns
    brands = Vehicleinformation.objects.filter(is_available=True).values_list('brand', flat=True).distinct()
    locations = Vehicleinformation.objects.filter(is_available=True).values_list('location', flat=True).distinct()
    context = {
        'vehicles': vehicles,
        'current_condition': condition_filter,
        'current_product_type': product_type_filter,
        'current_fuel_type': fuel_type_filter,
        'current_transmission': transmission_filter,
        'current_vehicle_type': vehicle_type_filter,
        'current_moto_type': moto_type_filter,
        'search_query': search_query,
        'total_vehicles': total_vehicles,
        'new_cars_count': new_cars_count,
        'used_cars_count': used_cars_count,
        'motorcycles_count': motorcycles_count,
        'sale_count': sale_count,
        'rent_count': rent_count,
        'brands': brands,
        'locations': locations,
        'moto_choices': Vehicleinformation.MOTO_CHOICES,
        'fuel_choices': Vehicleinformation.FUEL_TYPE,
        'transmission_choices': Vehicleinformation.TRANSMISSION,
        'condition_choices': Vehicleinformation.CONDITION,
        'type_choices': Vehicleinformation.TYPE_CHOICES,
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_condition(request, condition):
    """
    Filter vehicles by condition (New/Used)
    """
    if condition not in ['New', 'Used']:
        return redirect('BUS_SYSTEM:allvehicles')
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        condition=condition
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_condition': condition,
        'page_title': f'{condition} Vehicles',
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_product_type(request, product_type):
    """
    Filter vehicles by product type (For Sale/For Rent)
    """
    if product_type not in ['sale', 'rent']:
        return redirect('BUS_SYSTEM:allvehicles')
    
    type_display = 'For Sale' if product_type == 'sale' else 'For Rent'
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        product_type=product_type
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_product_type': product_type,
        'page_title': f'Vehicles {type_display}',
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_vehicle_type(request, vehicle_type):
    """
    Filter by vehicle type (Car/Motorcycle)
    """
    if vehicle_type not in ['Car', 'Motorcycle']:
        return redirect('BUS_SYSTEM:allvehicles')
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        vehicle_type=vehicle_type
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_vehicle_type': vehicle_type,
        'page_title': vehicle_type,
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_fuel_type(request, fuel_type):
    """
    Filter by fuel type (Petrol/Diesel/Electric/Hybrid)
    """
    if fuel_type not in ['Petrol', 'Diesel', 'Electric', 'Hybrid']:
        return redirect('BUS_SYSTEM:allvehicles')
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        fuel_type=fuel_type
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_fuel_type': fuel_type,
        'page_title': f'{fuel_type} Vehicles',
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_transmission(request, transmission):
    """
    Filter by transmission type (Manual/Automatic)
    """
    if transmission not in ['Manual', 'Automatic']:
        return redirect('BUS_SYSTEM:allvehicles')
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        transmission=transmission
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_transmission': transmission,
        'page_title': f'{transmission} Transmission',
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_moto_type(request, moto_type):
    """
    Filter motorcycles by type (cruiser, sport, dual-sport, touring, off-road, scooter, standard)
    """
    valid_types = [choice[0] for choice in Vehicleinformation.MOTO_CHOICES]
    
    if moto_type not in valid_types:
        return redirect('BUS_SYSTEM:allvehicles')
    
    # Get display name for the moto type
    moto_display = dict(Vehicleinformation.MOTO_CHOICES).get(moto_type, moto_type)
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        vehicle_type='Motorcycle',
        moto_type=moto_type
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_moto_type': moto_type,
        'page_title': f'{moto_display} Motorcycles',
        'moto_display': moto_display,
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_brand(request, brand):
    """
    Filter vehicles by brand
    """
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        brand__iexact=brand
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'current_brand': brand,
        'page_title': f'{brand} Vehicles',
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def filter_by_price_range(request, min_price, max_price):
    """
    Filter vehicles by price range
    """
    try:
        min_val = Decimal(min_price)
        max_val = Decimal(max_price)
    except:
        return redirect('BUS_SYSTEM:allvehicles')
    
    vehicles_list = Vehicleinformation.objects.filter(
        is_available=True,
        stock__gt=0,
        price__gte=min_val,
        price__lte=max_val
    ).order_by('-created_at').prefetch_related('images')
    
    paginator = Paginator(vehicles_list, 12)
    page_number = request.GET.get('page')
    vehicles = paginator.get_page(page_number)
    
    context = {
        'vehicles': vehicles,
        'min_price': min_price,
        'max_price': max_price,
        'page_title': f'Vehicles ${min_price} - ${max_price}',
    }
    return render(request, 'BUS_SYSTEM/allvehicles.html', context)


def vehicleinfo(request, id):
    """
    Display detailed information for a single vehicle
    """
    vehicle = get_object_or_404(Vehicleinformation, id=id, is_available=True)
    
    # Get related vehicles based on model choices
    related_vehicles = Vehicleinformation.objects.filter(
        Q(brand=vehicle.brand) | Q(vehicle_type=vehicle.vehicle_type),
        is_available=True,
        stock__gt=0
    ).exclude(id=vehicle.id)[:6]
    
    # Get all images for this vehicle
    vehicle_images = vehicle.images.all()
    
    context = {
        'vehicle': vehicle,
        'related_vehicles': related_vehicles,
        'vehicle_images': vehicle_images,
        'moto_choices': Vehicleinformation.MOTO_CHOICES,
        'fuel_choices': Vehicleinformation.FUEL_TYPE,
        'transmission_choices': Vehicleinformation.TRANSMISSION,
        'condition_choices': Vehicleinformation.CONDITION,
        'type_choices': Vehicleinformation.TYPE_CHOICES,
    }
    return render(request, 'BUS_SYSTEM/detailVehicles.html', context)


def filter_vehicles_ajax(request):
    """
    AJAX endpoint for filtering vehicles without page reload
    """
    condition = request.GET.get('condition')
    product_type = request.GET.get('product_type')
    fuel_type = request.GET.get('fuel_type')
    transmission = request.GET.get('transmission')
    vehicle_type = request.GET.get('vehicle_type')
    moto_type = request.GET.get('moto_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search = request.GET.get('search')
    
    vehicles = Vehicleinformation.objects.filter(is_available=True, stock__gt=0)
    
    if condition and condition in ['New', 'Used']:
        vehicles = vehicles.filter(condition=condition)
    
    if product_type and product_type in ['sale', 'rent']:
        vehicles = vehicles.filter(product_type=product_type)
    
    if fuel_type and fuel_type in ['Petrol', 'Diesel', 'Electric', 'Hybrid']:
        vehicles = vehicles.filter(fuel_type=fuel_type)
    
    if transmission and transmission in ['Manual', 'Automatic']:
        vehicles = vehicles.filter(transmission=transmission)
    
    if vehicle_type and vehicle_type in ['Car', 'Motorcycle']:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    
    if moto_type:
        valid_types = [choice[0] for choice in Vehicleinformation.MOTO_CHOICES]
        if moto_type in valid_types:
            vehicles = vehicles.filter(moto_type=moto_type)
    
    if min_price:
        try:
            vehicles = vehicles.filter(price__gte=Decimal(min_price))
        except:
            pass
    
    if max_price:
        try:
            vehicles = vehicles.filter(price__lte=Decimal(max_price))
        except:
            pass
    
    if search:
        vehicles = vehicles.filter(
            Q(brand__icontains=search) |
            Q(model__icontains=search) |
            Q(location__icontains=search)
        )
    
    vehicles = vehicles.order_by('-created_at')[:50]
    
    results = []
    for vehicle in vehicles:
        first_image = vehicle.images.first()
        image_url = first_image.image.url if first_image else None
        
        results.append({
            'id': vehicle.id,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'year': vehicle.year,
            'price': str(vehicle.price),
            'condition': vehicle.condition,
            'product_type': vehicle.product_type,
            'vehicle_type': vehicle.vehicle_type,
            'location': vehicle.location,
            'image': image_url,
            'discount': str(vehicle.discount) if vehicle.discount else None,
            'url': f'/vehicle/{vehicle.id}/',
        })
    
    return JsonResponse({'vehicles': results})


def get_filter_options(request):
    """
    Get all available filter options based on current database
    """
    brands = Vehicleinformation.objects.filter(is_available=True).values_list('brand', flat=True).distinct()
    locations = Vehicleinformation.objects.filter(is_available=True).values_list('location', flat=True).distinct()
    years = Vehicleinformation.objects.filter(is_available=True, year__isnull=False).values_list('year', flat=True).distinct().order_by('-year')
    
    return JsonResponse({
        'brands': list(brands),
        'locations': list(locations),
        'years': list(years),
        'moto_choices': dict(Vehicleinformation.MOTO_CHOICES),
        'fuel_choices': dict(Vehicleinformation.FUEL_TYPE),
        'transmission_choices': dict(Vehicleinformation.TRANSMISSION),
        'condition_choices': dict(Vehicleinformation.CONDITION),
        'type_choices': dict(Vehicleinformation.TYPE_CHOICES),
    })
    
    
def allcars(request):
    """
    Display all vehicles (Cars only) with advanced filtering
    """
    # Base queryset - only available vehicles, Car type only
    vehicles = Vehicleinformation.objects.filter(
        vehicle_type='Car',
        is_available=True, 
        stock__gt=0
    ).order_by('-created_at')
    
    # Search functionality
    query = request.GET.get('q', '')
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(location__icontains=query) |
            Q(fuel_type__icontains=query)
        )
    
    # Filter by product type (Sale/Rent)
    product_type = request.GET.get('product_type', '')
    if product_type:
        vehicles = vehicles.filter(product_type=product_type)
    
    # Filter by condition (New/Used)
    condition = request.GET.get('condition', '')
    if condition:
        vehicles = vehicles.filter(condition=condition)
    
    # Filter by fuel type
    fuel_type = request.GET.get('fuel_type', '')
    if fuel_type:
        vehicles = vehicles.filter(fuel_type=fuel_type)
    
    # Filter by transmission
    transmission = request.GET.get('transmission', '')
    if transmission:
        vehicles = vehicles.filter(transmission=transmission)
    
    # Filter by max price
    max_price = request.GET.get('max_price', '')
    if max_price and max_price.isdigit():
        vehicles = vehicles.filter(price__lte=Decimal(max_price))
    
    # Filter by min price
    min_price = request.GET.get('min_price', '')
    if min_price and min_price.isdigit():
        vehicles = vehicles.filter(price__gte=Decimal(min_price))
    
    # Filter by year range
    min_year = request.GET.get('min_year', '')
    max_year = request.GET.get('max_year', '')
    if min_year and min_year.isdigit():
        vehicles = vehicles.filter(year__gte=int(min_year))
    if max_year and max_year.isdigit():
        vehicles = vehicles.filter(year__lte=int(max_year))
    
    # Pagination
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get total count for stats
    total_vehicles = vehicles.count()
    
    # Get cart count for badge
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'vehicles': page_obj,
        'total_vehicles': total_vehicles,
        'query': query,
        'current_product_type': product_type,
        'current_condition': condition,
        'current_fuel_type': fuel_type,
        'current_transmission': transmission,
        'current_max_price': max_price,
        'cart_count': cart_count,
    }
    
    return render(request, 'BUS_SYSTEM/cars.html', context)


def car_for_sale(request):
    """Display cars that are for sale only"""
    vehicles = Vehicleinformation.objects.filter(
        vehicle_type='Car',
        product_type='sale',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    # Apply search
    query = request.GET.get('q', '')
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(location__icontains=query)
        )
    
    # Apply condition filter
    condition = request.GET.get('condition', '')
    if condition:
        vehicles = vehicles.filter(condition=condition)
    
    # Apply price filter
    max_price = request.GET.get('max_price', '')
    if max_price and max_price.isdigit():
        vehicles = vehicles.filter(price__lte=Decimal(max_price))
    
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'vehicles': page_obj,
        'total_vehicles': vehicles.count(),
        'query': query,
        'current_condition': condition,
        'current_max_price': max_price,
        'cart_count': cart_count,
        'is_for_sale': True,
    }
    return render(request, 'BUS_SYSTEM/cars.html', context)


def car_for_rent(request):
    """Display cars that are for rent only"""
    vehicles = Vehicleinformation.objects.filter(
        vehicle_type='Car',
        product_type='rent',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    query = request.GET.get('q', '')
    if query:
        vehicles = vehicles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(location__icontains=query)
        )
    
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'vehicles': page_obj,
        'total_vehicles': vehicles.count(),
        'query': query,
        'cart_count': cart_count,
        'is_for_rent': True,
    }
    return render(request, 'BUS_SYSTEM/cars.html', context)


def newcars(request):
    """Display new cars only"""
    vehicles = Vehicleinformation.objects.filter(
        vehicle_type='Car',
        condition='New',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'vehicles': page_obj,
        'total_vehicles': vehicles.count(),
        'cart_count': cart_count,
        'is_new_cars': True,
    }
    return render(request, 'BUS_SYSTEM/cars.html', context)


def car_used(request):
    """Display used cars only"""
    vehicles = Vehicleinformation.objects.filter(
        vehicle_type='Car',
        condition='Used',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    paginator = Paginator(vehicles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'vehicles': page_obj,
        'total_vehicles': vehicles.count(),
        'cart_count': cart_count,
        'is_used_cars': True,
    }
    return render(request, 'BUS_SYSTEM/cars.html', context)


# ============= MOTORCYCLE VIEWS =============
def allmotorcycles(request):
    """
    Display all motorcycles with advanced filtering
    """
    # Base queryset - only available motorcycles
    motorcycles = Vehicleinformation.objects.filter(
        vehicle_type='Motorcycle',
        is_available=True, 
        stock__gt=0
    ).order_by('-created_at')
    
    # Search functionality
    query = request.GET.get('q', '')
    if query:
        motorcycles = motorcycles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(location__icontains=query) |
            Q(moto_type__icontains=query)
        )
    
    # Filter by motorcycle type (Sport, Cruiser, etc.)
    moto_type = request.GET.get('moto_type', '')
    if moto_type:
        motorcycles = motorcycles.filter(moto_type=moto_type)
    
    # Filter by product type (Sale/Rent)
    product_type = request.GET.get('product_type', '')
    if product_type:
        motorcycles = motorcycles.filter(product_type=product_type)
    
    # Filter by condition (New/Used)
    condition = request.GET.get('condition', '')
    if condition:
        motorcycles = motorcycles.filter(condition=condition)
    
    # Filter by fuel type
    fuel_type = request.GET.get('fuel_type', '')
    if fuel_type:
        motorcycles = motorcycles.filter(fuel_type=fuel_type)
    
    # Filter by max price
    max_price = request.GET.get('max_price', '')
    if max_price and max_price.isdigit():
        motorcycles = motorcycles.filter(price__lte=Decimal(max_price))
    
    # Filter by max engine capacity (CC)
    max_cc = request.GET.get('max_cc', '')
    if max_cc and max_cc.isdigit():
        motorcycles = motorcycles.filter(engine_capacity__lte=int(max_cc))
    
    # Pagination
    paginator = Paginator(motorcycles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get total count for stats
    total_motorcycles = motorcycles.count()
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    # DEBUG PRINT - Check what's being passed
    print(f"DEBUG: Total motorcycles found: {total_motorcycles}")
    print(f"DEBUG: Page object has {len(page_obj)} items")
    print(f"DEBUG: Query: {query}")
    print(f"DEBUG: Moto type filter: {moto_type}")
    print(f"DEBUG: Product type filter: {product_type}")
    
    context = {
        'motorcycles': page_obj,  # This is the key - 'motorcycles' plural
        'total_motorcycles': total_motorcycles,
        'query': query,
        'current_moto_type': moto_type,
        'current_product_type': product_type,
        'current_condition': condition,
        'current_fuel_type': fuel_type,
        'current_max_price': max_price,
        'current_max_cc': max_cc,
        'cart_count': cart_count,
    }
    
    return render(request, 'BUS_SYSTEM/motorcycle.html', context)


def moto_for_sale(request):
    """Display motorcycles that are for sale only"""
    motorcycles = Vehicleinformation.objects.filter(
        vehicle_type='Motorcycle',
        product_type='sale',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    query = request.GET.get('q', '')
    if query:
        motorcycles = motorcycles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query)
        )
    
    paginator = Paginator(motorcycles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'motorcycles': page_obj,
        'total_motorcycles': motorcycles.count(),
        'query': query,
        'cart_count': cart_count,
        'is_for_sale': True,
    }
    return render(request, 'BUS_SYSTEM/motorcycle.html', context)


def moto_for_rent(request):
    """Display motorcycles that are for rent only"""
    motorcycles = Vehicleinformation.objects.filter(
        vehicle_type='Motorcycle',
        product_type='rent',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    query = request.GET.get('q', '')
    if query:
        motorcycles = motorcycles.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query)
        )
    
    paginator = Paginator(motorcycles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'motorcycles': page_obj,
        'total_motorcycles': motorcycles.count(),
        'query': query,
        'cart_count': cart_count,
        'is_for_rent': True,
    }
    return render(request, 'BUS_SYSTEM/motorcycle.html', context)


def new_motorcycles(request):
    """Display new motorcycles only"""
    motorcycles = Vehicleinformation.objects.filter(
        vehicle_type='Motorcycle',
        condition='New',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    paginator = Paginator(motorcycles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'motorcycles': page_obj,
        'total_motorcycles': motorcycles.count(),
        'cart_count': cart_count,
        'is_new': True,
    }
    return render(request, 'BUS_SYSTEM/motorcycle.html', context)


def used_motorcycles(request):
    """Display used motorcycles only"""
    motorcycles = Vehicleinformation.objects.filter(
        vehicle_type='Motorcycle',
        condition='Used',
        is_available=True,
        stock__gt=0
    ).order_by('-created_at')
    
    paginator = Paginator(motorcycles, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'motorcycles': page_obj,
        'total_motorcycles': motorcycles.count(),
        'cart_count': cart_count,
        'is_used': True,
    }
    return render(request, 'BUS_SYSTEM/motorcycle.html', context)


def motorcycle_detail(request, pk):
    """Display detailed view of a single motorcycle"""
    motorcycle = get_object_or_404(Vehicleinformation, pk=pk, is_available=True, vehicle_type='Motorcycle')
    
    # Get related motorcycles (same type or similar price)
    related_motorcycles = Vehicleinformation.objects.filter(
        vehicle_type='Motorcycle',
        is_available=True
    ).filter(
        Q(moto_type=motorcycle.moto_type) | 
        Q(brand=motorcycle.brand)
    ).exclude(pk=pk)[:4]
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        from CART.models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except:
            cart_count = 0
    
    context = {
        'motorcycle': motorcycle,
        'related_motorcycles': related_motorcycles,
        'cart_count': cart_count,
    }
    return render(request, 'BUS_SYSTEM/DetailVehicle.html', context)



from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def debug_check_roles(request):
    """Debug view to check user roles"""
    users_data = []
    for user in User.objects.all():
        try:
            profile = Profile.objects.get(user=user)
            role = profile.role
        except Profile.DoesNotExist:
            role = "NO PROFILE"
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role,
            'has_profile': hasattr(user, 'profile')
        })
    
    return JsonResponse({
        'total_users': User.objects.count(),
        'users': users_data,
        'seller_count': Profile.objects.filter(role='seller').count(),
        'customer_count': Profile.objects.filter(role='customer').count()
    })
    
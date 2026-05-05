from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Count
from django.utils.timezone import now
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from BUS_SYSTEM.models import Building, Vehicleinformation, Commodity, Orders
from django.core.paginator import Paginator
from .forms import SellerNotificationForm
from DASHBOARD.models import Notification
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F,Q
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from decimal import Decimal
import json
from django.core.exceptions import PermissionDenied
from BUS_SYSTEM.models import Commodity, Vehicleinformation, Building, Orders, Profile
from FASHIONITEM.models import FashionItem




def is_seller_or_staff(user):
    """Check if user is staff OR has the seller role."""
    if not user.is_authenticated:
        return False
    # Admins/Staff always pass
    if user.is_staff:
        return True
    try:
        return user.profile.role == 'seller'
    except (AttributeError, Profile.DoesNotExist):
        return False
def seller_staff_required(view_func):
    
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if is_seller_or_staff(request.user):
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Access restricted to Sellers and Admin only.")
        return redirect('DASHBOARD:buyer_dashboard') 
    return _wrapped_view
#To allow buyer to upgrate to the 
@login_required
def upgrade_to_seller(request):
    profile = request.user.profile
    if profile.role == 'customer':
        profile.role = 'seller'
        profile.save()
        messages.success(request, "Congratulations! You are now a registered seller.")
        return redirect('DASHBOARD:seller_dashboard')
    else:
        messages.info(request, "You are already a seller.")
        return redirect('DASHBOARD:seller_dashboard')



#
def dashboard_home(request):
    # 1. Product Counts (Including the new FashionItem)
    fashion_count = FashionItem.objects.count()
    commodity_count = Commodity.objects.count()
    vehicle_count = Vehicleinformation.objects.count()
    building_count = Building.objects.count()
    
    total_products = fashion_count + commodity_count + vehicle_count + building_count
    
    # 2. Order Statistics
    all_orders = Orders.objects.all()
    total_orders = all_orders.count()
    pending_orders = all_orders.filter(status='pending').count()
    delivered_orders = all_orders.filter(status='delivered').count()
    
    # 3. Financials (Total Revenue from all paid orders)
    # If your Orders model uses 'total_price' as the field name:
    total_revenue = all_orders.aggregate(total=Sum('total_price'))['total'] or 0
    
    # 4. Total Stock available across ALL models
    total_stock = (
        (Commodity.objects.aggregate(s=Sum('stock'))['s'] or 0) +
        (FashionItem.objects.aggregate(s=Sum('stock'))['s'] or 0) +
        (Vehicleinformation.objects.aggregate(s=Sum('stock'))['s'] or 0) +
        (Building.objects.aggregate(s=Sum('stock'))['s'] or 0)
    )

    context = {
        "total_products": total_products,
        "total_revenue": total_revenue,
        "total_stock": total_stock,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        
        # Data for the Doughnut Chart (Categories)
        "cat_fashion": fashion_count,
        "cat_commodity": commodity_count,
        "cat_vehicle": vehicle_count,
        "cat_building": building_count,
        
        # Placeholder for 14-day spending (Logic can be added later)
        "spending_data": [0, 0, 10, 50, 20, 100, 40, 20, 10, 30, 90, 10, 5, 15], 
    }
    return render(request, "DASHBOARD/index.html", context)


# --- 4. ORDER & USER MANAGEMENT -

@seller_staff_required
def update_order_status(request, order_id):
    order = get_object_or_404(Orders, id=order_id)
    if request.method == "POST":
        order.status = request.POST.get("status")
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {order.status}")
    return redirect("DASHBOARD:manage_orders")



# --- 5. SELLER/PERSONAL DASHBOARD (For the logged-in user) ---
@login_required
def user_personal_dashboard(request):
    # Get profile (create if missing to avoid 500 errors)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Orders specifically made by this user
    my_orders = Orders.objects.filter(buyer=request.user).order_by('-created_at')
    
    context = {
        "profile": profile,
        "total_orders": my_orders.count(),
        "recent_orders": my_orders[:5],
        "notifications": [
            {"message": "Welcome to your Distar Dashboard!", "status": "info"}
        ],
    }
    return render(request, "DASHBOARD/buyer_dashboard.html", context)
@login_required
def buyer_dashboard(request):
    buyer = request.user
    today = timezone.now().date()
    personal_orders = Orders.objects.filter(buyer=buyer)
    
    # 1. Generate 14-Day Spending Trend
    spending_data = []
    days_labels = []
    for i in range(13, -1, -1):
        target_date = today - timedelta(days=i)
        daily_sum = personal_orders.filter(
            created_at__date=target_date
        ).aggregate(total=Sum('total_price'))['total'] or 0
        spending_data.append(float(daily_sum))
        days_labels.append(target_date.strftime('%d %b'))

    # 2. Category Counts (Handling GenericForeignKey)
    def get_count_for_category(cat_name):
        # Gather IDs from all models that have a 'category' field
        b_ids = Building.objects.filter(category=cat_name).values_list('id', flat=True)
        f_ids = FashionItem.objects.filter(category=cat_name).values_list('id', flat=True)
        # v_ids = Vehicle.objects.filter(category=cat_name).values_list('id', flat=True)
        
        combined_ids = list(b_ids) + list(f_ids)
        return personal_orders.filter(object_id__in=combined_ids).count()

    counts = {
        'Commodity': get_count_for_category('Commodity'),
        'Vehicle': get_count_for_category('Vehicle'),
        'Building': get_count_for_category('Building')
    }
    
    # 3. Determine Favorite Category
    fav_category = max(counts, key=counts.get) if any(counts.values()) else "None"

    # 4. Final Context (Must match your HTML variable names)
    context = {
        'order_count': personal_orders.count(),
        'total_spent': personal_orders.aggregate(Sum('total_price'))['total__sum'] or 0,
        'recent_purchases': personal_orders.order_by('-created_at')[:5],
        'spending_data': spending_data,
        'days_labels': days_labels,
        'fav_category': fav_category,
    }
    
    return render(request, 'DASHBOARD/buyer_dashboard.html', context)

@seller_staff_required
def seller_dashboard(request):
    user = request.user
    # 1. Fetch only items belonging to THIS seller
    my_buildings = Building.objects.filter(seller=user)
    my_vehicles = Vehicleinformation.objects.filter(seller=user)
    my_commodities = Commodity.objects.filter(seller=user)
    # 2. Get all orders for items belonging to this seller
    # We filter Orders where the 'product' is one of the seller's items
    all_orders = Orders.objects.all()
    seller_orders = [o for o in all_orders if hasattr(o.product, 'seller') and o.product.seller == user]
    # 3. Calculate Financials
    total_sales = sum(o.total_price for o in seller_orders if o.is_paid)
    platform_fees = sum(o.get_commission() for o in seller_orders if o.is_paid)
    net_earnings = total_sales - platform_fees
    # 4. Stock Summary
    total_stock = (my_buildings.aggregate(Sum('stock'))['stock__sum'] or 0) + \
                  (my_vehicles.aggregate(Sum('stock'))['stock__sum'] or 0) + \
                  (my_commodities.aggregate(Sum('stock'))['stock__sum'] or 0)
    context = {
        'orders': seller_orders,
        'total_sales': total_sales,
        'platform_fees': platform_fees,
        'net_earnings': net_earnings,
        'total_stock': total_stock,
        'items_count': my_buildings.count() + my_vehicles.count() + my_commodities.count(),
    }
    return render(request, 'DASHBOARD/seller_dashboard.html', context)

@seller_staff_required
def notify_buyer(request, order_id):
    order = get_object_or_404(Orders, id=order_id)
    if request.method == 'POST':
        form = SellerNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.user = order.buyer  # Send to the buyer
            notification.save()
            messages.success(request, "Notification sent to buyer!")
            return redirect('seller_dashboard')

@seller_staff_required
def confirm_order_delivery(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Orders, id=order_id)

        # Security check: Ensure the seller owns the product
        if order.product.seller != request.user:
            messages.error(request, "Access Denied: You do not own this product.")
            return redirect('marketplace:seller_dashboard')

        # Run your model method: reduces stock & changes status to 'confirmed'
        if order.confirm_and_reduce_stock():
            messages.success(request, f"Order #{order.id} confirmed! Stock updated.")
            
            # Auto-notify buyer that item is confirmed
            Notification.objects.create(
                user=order.buyer,
                title="Order Confirmed",
                message=f"Seller has confirmed your order for {order.product}. It is now being prepared."
            )
        else:
            messages.error(request, "Error: Not enough stock to fulfill this order.")
            
    return redirect('marketplace:seller_dashboard')

@seller_staff_required
def notify_buyer_action(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        message_text = request.POST.get('message')
        order = get_object_or_404(Orders, id=order_id)

        if order.product.seller == request.user:
            Notification.objects.create(
                user=order.buyer,
                title=f"Message from Seller regarding Order #{order.id}",
                message=message_text
            )
            messages.success(request, "Your message has been sent to the buyer.")
        else:
            messages.error(request, "Unauthorized action.")

    return redirect('DASHBOARD:seller_dashboard')  



@login_required
def seller_inventory(request):
    """
    Displays the seller's inventory across four categories: 
    Buildings, Vehicles, General Commodities, and Fashion.
    """
    
    buildings_list = Building.objects.filter(seller=request.user).order_by('-created_at')
    vehicles_list = Vehicleinformation.objects.filter(seller=request.user).order_by('-created_at')
    fashion_list = FashionItem.objects.filter(seller=request.user).order_by('-created_at')
    commodities_list = Commodity.objects.filter(seller=request.user).order_by('-id')

    # Reusable Pagination Helper
    def get_paginated_page(queryset, request, param_name, items_per_page=12):
        paginator = Paginator(queryset, items_per_page)
        page_number = request.GET.get(param_name)
        return paginator.get_page(page_number)

    context = {
        'buildings': get_paginated_page(buildings_list, request, 'page_build'),
        'vehicles': get_paginated_page(vehicles_list, request, 'page_veh'),
        'fashion': get_paginated_page(fashion_list, request, 'page_fash'),
        'commodities': get_paginated_page(commodities_list, request, 'page_com'),
    }
    return render(request, 'DASHBOARD/inventory.html', context)


@login_required
def seller_edit_item(request, item_type, item_id):
    """Edit an item in the seller's inventory"""
    model_map = {
        'vehicle': Vehicleinformation,
        'building': Building,
        'fashion': FashionItem,
        'commodity': Commodity,
    }
    
    model = model_map.get(item_type)
    if not model:
        return redirect('DASHBOARD:seller_inventory')
    
    item = get_object_or_404(model, id=item_id, seller=request.user)
    
    if request.method == 'POST':
        try:
            # Update basic fields
            if item_type == 'vehicle':
                item.brand = request.POST.get('brand', item.brand)
                item.model = request.POST.get('model', item.model)
                item.year = request.POST.get('year', item.year)
                item.price = request.POST.get('price', item.price)
                item.condition = request.POST.get('condition', item.condition)
                item.fuel_type = request.POST.get('fuel_type', item.fuel_type)
                item.mileage = request.POST.get('mileage', item.mileage)
                item.stock = request.POST.get('stock', item.stock)
                item.description = request.POST.get('description', item.description)
                
            elif item_type == 'building':
                item.title = request.POST.get('title', item.title)
                item.price = request.POST.get('price', item.price)
                item.location = request.POST.get('location', item.location)
                item.bedrooms = request.POST.get('bedrooms', item.bedrooms)
                item.bathrooms = request.POST.get('bathrooms', item.bathrooms)
                item.plot_area = request.POST.get('plot_area', item.plot_area)
                item.property_type = request.POST.get('property_type', item.property_type)
                item.stock = request.POST.get('stock', item.stock)
                item.description = request.POST.get('description', item.description)
                
            elif item_type == 'fashion':
                item.title = request.POST.get('title', item.title)
                item.price = request.POST.get('price', item.price)
                item.discount = request.POST.get('discount', item.discount)
                item.brand = request.POST.get('brand', item.brand)
                item.size = request.POST.get('size', item.size)
                item.gender = request.POST.get('gender', item.gender)
                item.stock = request.POST.get('stock', item.stock)
                item.description = request.POST.get('description', item.description)
                
            elif item_type == 'commodity':
                item.name = request.POST.get('name', item.name)
                item.price = request.POST.get('price', item.price)
                item.discount = request.POST.get('discount', item.discount)
                item.stock = request.POST.get('stock', item.stock)
                item.description = request.POST.get('description', item.description)
            
            item.save()
            
            # Handle image upload if present
            if request.FILES.get('image'):
                # You'll need to implement image handling based on your model structure
                pass
            
            return JsonResponse({'success': True, 'message': 'Item updated successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - return item data for editing
    item_data = {
        'id': item.id,
        'type': item_type,
    }
    
    if item_type == 'vehicle':
        item_data.update({
            'brand': item.brand,
            'model': item.model,
            'year': item.year,
            'price': float(item.price),
            'condition': item.condition,
            'fuel_type': item.fuel_type,
            'mileage': item.mileage,
            'stock': item.stock,
            'description': item.description or '',
        })
    elif item_type == 'building':
        item_data.update({
            'title': item.title,
            'price': float(item.price),
            'location': item.location,
            'bedrooms': item.bedrooms,
            'bathrooms': item.bathrooms,
            'plot_area': item.plot_area,
            'property_type': item.property_type,
            'stock': item.stock,
            'description': item.description or '',
        })
    elif item_type == 'fashion':
        item_data.update({
            'title': item.title,
            'price': float(item.price),
            'discount': float(item.discount) if item.discount else 0,
            'brand': item.brand or '',
            'size': item.size,
            'gender': item.gender,
            'stock': item.stock,
            'description': item.description or '',
        })
    elif item_type == 'commodity':
        item_data.update({
            'name': item.name,
            'price': float(item.price),
            'discount': float(item.discount) if item.discount else 0,
            'stock': item.stock,
            'description': item.description or '',
        })
    
    return JsonResponse(item_data)


@login_required
def seller_delete_item(request, item_type, item_id):
    """Delete an item from seller's inventory"""
    model_map = {
        'vehicle': Vehicleinformation,
        'building': Building,
        'fashion': FashionItem,
        'commodity': Commodity,
    }
    
    model = model_map.get(item_type)
    if not model:
        return JsonResponse({'success': False, 'error': 'Invalid item type'})
    
    item = get_object_or_404(model, id=item_id, seller=request.user)
    
    try:
        item_name = str(item)
        item.delete()
        return JsonResponse({'success': True, 'message': f'{item_name} has been deleted.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
  
@staff_member_required
@require_http_methods(["GET"])
def admin_advanced_dashboard(request):
    """
    Advanced admin dashboard with analytics and management features
    """
    # 1. Financial Data (Global Totals)
    paid_orders = Orders.objects.filter(is_paid=True).order_by('-created_at')
    total_revenue = paid_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    platform_earnings = float(total_revenue) * 0.02

    # 2. Time-Series Data for Bar Chart
    sales_by_month = (
        Orders.objects.filter(is_paid=True)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(monthly_total=Sum('total_price'))
        .order_by('month')
    )

    chart_labels = [item['month'].strftime("%b %Y") for item in sales_by_month]
    chart_data = [float(item['monthly_total']) for item in sales_by_month]

    # 3. Users with their listing counts
    users = User.objects.all().select_related('profile').annotate(
        item_count=Count('building_items', distinct=True) + 
                   Count('vehicleinformation_items', distinct=True) + 
                   Count('commodity_items', distinct=True) +
                   Count('fashion_items', distinct=True)
    )

    # 4. All inventory items
    buildings = Building.objects.all().order_by('-created_at')
    vehicles = Vehicleinformation.objects.all().order_by('-created_at')
    commodities = Commodity.objects.all().order_by('-created_at')
    fashion_items = FashionItem.objects.all().order_by('-created_at')
    
    total_items = buildings.count() + vehicles.count() + commodities.count() + fashion_items.count()

    context = {
        'total_revenue': total_revenue,
        'platform_earnings': platform_earnings,
        'users': users,
        'buildings': buildings,
        'vehicles': vehicles,
        'commodities': commodities,
        'fashion_items': fashion_items,
        'paid_orders': paid_orders,
        'total_items': total_items,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'buildings_count': buildings.count(),
        'vehicles_count': vehicles.count(),
        'commodities_count': commodities.count(),
        'fashion_count': fashion_items.count(),
    }
    return render(request, 'DASHBOARD/admin_dashboard.html', context)


@staff_member_required
@require_http_methods(["POST"])
def admin_delete_user(request, user_id):
    """
    Delete a user (admin only)
    Supports both AJAX and regular POST requests
    """
    try:
        # Prevent admin from deleting themselves
        if request.user.id == int(user_id):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'You cannot delete your own account'}, status=400)
            messages.error(request, 'You cannot delete your own account')
            return redirect('DASHBOARD:admin_advanced_dashboard')
        
        user = get_object_or_404(User, id=user_id)
        username = user.username
        email = user.email
        
        # Optional: Check if user has important data before deletion
        # You can add logic here to handle related data
        
        user.delete()
        
        success_message = f'User "{username}" ({email}) has been deleted successfully'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_message})
        
        messages.success(request, success_message)
        return redirect('DASHBOARD:admin_advanced_dashboard')
        
    except Exception as e:
        error_message = f'Error deleting user: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_message}, status=500)
        messages.error(request, error_message)
        return redirect('DASHBOARD:admin_advanced_dashboard')


@staff_member_required
@require_http_methods(["POST"])
def admin_delete_item(request, item_type, item_id):
    """
    Unified delete view for all inventory items (admin only)
    Supports both AJAX and regular POST requests
    """
    # Define model mapping
    model_map = {
        'building': Building,
        'vehicle': Vehicleinformation,
        'commodity': Commodity,
        'fashion': FashionItem,
    }
    
    # Define name extraction functions
    def get_item_name(item, item_type):
        if item_type == 'building':
            return item.title
        elif item_type == 'vehicle':
            return f"{item.brand} {item.model} ({item.year})"
        elif item_type == 'fashion':
            return f"{item.title} (Size: {item.size})"
        elif item_type == 'commodity':
            return item.name
        return str(item)
    
    try:
        # Validate item type
        model = model_map.get(item_type.lower())
        if not model:
            error_message = f'Invalid item type: {item_type}. Allowed types: building, vehicle, commodity, fashion'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message}, status=400)
            messages.error(request, error_message)
            return redirect('DASHBOARD:admin_advanced_dashboard')
        
        # Get the item
        item = get_object_or_404(model, id=item_id)
        
        # Get item name for response
        item_name = get_item_name(item, item_type.lower())
        
        # Optional: Add additional security checks here
        # For example, check if admin has permission to delete this specific item
        # You could add logging here to track deletions
        
        # Perform the deletion
        item.delete()
        
        success_message = f'{item_name} has been deleted successfully'
        
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'deleted_id': item_id,
                'deleted_type': item_type
            })
        
        # Handle regular POST request
        messages.success(request, success_message)
        return redirect('DASHBOARD:admin_advanced_dashboard')
        
    except Exception as e:
        error_message = f'Error deleting item: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_message}, status=500)
        
        messages.error(request, error_message)
        return redirect('DASHBOARD:admin_advanced_dashboard')


# Optional: Add a bulk delete view if needed
@staff_member_required
@require_http_methods(["POST"])
def admin_bulk_delete_items(request):
    """
    Bulk delete multiple items at once
    Expects JSON: {"items": [{"type": "building", "id": 1}, ...]}
    """
    try:
        data = json.loads(request.body)
        items_to_delete = data.get('items', [])
        
        deleted_count = 0
        errors = []
        
        model_map = {
            'building': Building,
            'vehicle': Vehicleinformation,
            'commodity': Commodity,
            'fashion': FashionItem,
        }
        
        for item_info in items_to_delete:
            item_type = item_info.get('type')
            item_id = item_info.get('id')
            
            model = model_map.get(item_type.lower())
            if not model:
                errors.append(f'Invalid type: {item_type}')
                continue
            
            try:
                item = get_object_or_404(model, id=item_id)
                item.delete()
                deleted_count += 1
            except Exception as e:
                errors.append(f'Failed to delete {item_type} {item_id}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def get_count_for_category(category_name):
    """
    Get count of purchases for a specific category by mapping to property_type
    """
    try:
        # Map display categories to actual property_type values in your Building model
        category_mapping = {
            'House': 'Residential',
            'Appartment': 'Apartment',  # Note: 'Apartment' (your model uses this spelling)
            'Land': 'Industrial',  # Map Land to Industrial (or adjust as needed)
            'Commercial': 'Commercial',
            'Commodity': 'Commercial',  # Map Commodity to Commercial
        }
        
        # Get the actual property_type from mapping, default to original if not found
        property_type_value = category_mapping.get(category_name, category_name)
        
        # Filter buildings by property_type
        b_ids = Building.objects.filter(property_type=property_type_value).values_list('id', flat=True)
        
        # Count FashionItems for these buildings (no buyer field, so count all items)
        count = FashionItem.objects.filter(building_id__in=b_ids).count()
        return count
        
    except Exception as e:
        print(f"Error in get_count_for_category for {category_name}: {e}")
        return 0


def buyer_dashboard(request):
    """
    Dashboard for buyers/customers to see their activity
    Note: Since FashionItem doesn't have a buyer field, we're showing all items
    """
    # Since there's no buyer field, we need to adjust the queries
    # You might need to create a separate Purchase or Order model to track buyer purchases
    
    context = {
        # These will need to be adjusted based on your actual data model
        'total_purchases': 0,  # Placeholder - no buyer field exists
        'total_spent': 0,  # Placeholder - no buyer field exists
        'pending_purchases': 0,  # Placeholder - no buyer field exists
        'completed_purchases': 0,  # Placeholder - no buyer field exists
        
        # Property type counts (works since it doesn't depend on buyer)
        'House': get_count_for_category('House'),
        'Appartment': get_count_for_category('Appartment'),
        'Land': get_count_for_category('Land'),
        'Commercial': get_count_for_category('Commercial'),
        'Commodity': get_count_for_category('Commodity'),
        
        # Recent items (all items since no buyer field)
        'recent_purchases': FashionItem.objects.all().order_by('-created_at')[:10],
    }
    
    return render(request, 'DASHBOARD/buyer_dashboard.html', context)
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
import json
from django.db import transaction
from BUS_SYSTEM.models import Orders
from .models import CartItem, Payment
from .forms import PaymentForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Notification
from django.contrib.auth.models import User
from FASHIONITEM.models import FashionItem, FashionImage
from BUS_SYSTEM.models import Building


def get_cart(request):
    if 'cart' not in request.session:
        request.session['cart'] = {}
    return request.session['cart']


# -------------------------------
# Add item to cart
# -------------------------------
# CART/views.py
# -------------------------------
# Add item to cart (with AJAX support - no page reload)
# -------------------------------
def add_to_cart(request, model_name, product_id):
    cart = request.session.get("cart", {})
    key = f"{model_name}_{product_id}"
    
    # First, get the product and check stock availability
    ct_queryset = ContentType.objects.filter(model=model_name.lower())
    
    # Find the one that actually has a model class
    content_type = None
    for ct in ct_queryset:
        if ct.model_class() is not None:
            content_type = ct
            break
    
    if not content_type:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Product category is incorrectly registered in the database.'}, status=400)
        messages.error(request, "Product category is incorrectly registered in the database.")
        return redirect("BUS_SYSTEM:marketplace")
    
    # Safely fetch the product
    try:
        product = content_type.get_object_for_this_type(id=product_id)
    except Exception:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Product no longer exists.'}, status=404)
        messages.error(request, "Product no longer exists.")
        return redirect("BUS_SYSTEM:marketplace")
    
    # Check if product is available and has stock
    stock_available = getattr(product, 'stock', 0)
    if stock_available <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': f'{product.title if hasattr(product, "title") else product.name} is out of stock.'}, status=400)
        messages.error(request, f"{product.title if hasattr(product, 'title') else product.name} is out of stock.")
        return redirect("BUS_SYSTEM:marketplace")
    
    # Get current quantity in cart
    current_quantity = cart.get(key, {}).get('quantity', 0)
    
    # Check if adding one more would exceed stock
    if current_quantity + 1 > stock_available:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': f'Cannot add more. Only {stock_available} item(s) available in stock.'
            }, status=400)
        messages.error(request, f"Cannot add more. Only {stock_available} item(s) available in stock.")
        return redirect("CART:view_cart")
    
    # Proceed with adding/updating cart
    if key in cart:
        cart[key]["quantity"] += 1
    else:
        # Handle Price Logic
        current_price = float(product.price)
        
        # Apply discount if it exists
        if hasattr(product, 'discount') and product.discount:
            current_price = float(product.price - product.discount)
        
        # Handle Image Logic
        image_url = ""
        
        if model_name.lower() == 'fashionitem':
            first_media = product.images.first()
            if first_media and first_media.image:
                image_url = first_media.image.url
        elif hasattr(product, "image") and product.image:
            image_url = product.image.url
        elif hasattr(product, "images") and product.images.exists():
            image_url = product.images.first().image.url
        
        # Save to Cart
        cart[key] = {
            "name": getattr(product, "title", getattr(product, "name", "Product")),
            "price": current_price,
            "quantity": 1,
            "image": image_url,
            "model_type": model_name.lower(),
            "product_id": product_id,
            "stock_limit": stock_available  # Store stock limit for later reference
        }
    
    request.session["cart"] = cart
    request.session.modified = True
    
    # Calculate new cart count
    cart_count = sum(item['quantity'] for item in cart.values())
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added {cart[key]['name']} to your cart.",
            'cart_count': cart_count,
            'item_name': cart[key]['name'],
            'new_quantity': cart[key]['quantity'],
            'stock_limit': stock_available
        })
    
    # Regular form submission (redirect)
    messages.success(request, f"Added {cart[key]['name']} to your cart.")
    return redirect("CART:view_cart")
# -------------------------------
# View cart page
# -------------------------------
def view_cart(request):
    cart = get_cart(request)
    cart_items = []
    total = 0
    cart_count = 0

    for key, item in cart.items():
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_count += item['quantity']
        
        # Ensure image URL is valid - use placeholder if missing
        image_url = item.get('image', '')
        if not image_url or image_url == '' or image_url == '/static/default.jpg':
            # Use a data URL placeholder (no file needed)
            image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-family='Arial' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E"
        
        cart_items.append({
            'id': key,
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'image': image_url,
            'images': item.get('images', [image_url]),
            'stock_limit': item.get('stock_limit', 999)  # Add stock limit to cart items
        })
    
    # Get recommended products (you may like)
    recommended_products = []
    
    # Import models from their actual locations
    try:
        from FASHIONITEM.models import FashionItem
        from BUS_SYSTEM.models import Building, Commodity
        from BUS_SYSTEM.models import Vehicleinformation
    except ImportError:
        # If VEHICLE doesn't exist, try alternative name
        try:
            from BUS_SYSTEM.models import Vehicleinformation
        except ImportError:
            # Create empty placeholder if vehicle app doesn't exist
            Vehicleinformation = None
    
    # Get cart item IDs to exclude them (extract numeric IDs)
    cart_item_numeric_ids = []
    for item_id in cart_items:
        # Extract numeric ID from keys like 'fashionitem_1' or 'commodity_5'
        try:
            if '_' in item_id['id']:
                numeric_id = int(item_id['id'].split('_')[-1])
            else:
                numeric_id = int(item_id['id'])
            cart_item_numeric_ids.append(numeric_id)
        except (ValueError, IndexError):
            pass
    
    try:
        # Get Fashion Items
        if FashionItem:
            fashion_items = FashionItem.objects.filter(is_available=True, stock__gt=0)
            if cart_item_numeric_ids:
                fashion_items = fashion_items.exclude(id__in=cart_item_numeric_ids)
            fashion_items = fashion_items[:4]
            
            for item in fashion_items:
                first_image = item.images.first()
                if first_image and hasattr(first_image, 'image') and first_image.image:
                    image_url = first_image.image.url
                else:
                    # Use data URL placeholder instead of default.jpg
                    image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-family='Arial' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E"
                
                recommended_products.append({
                    'id': item.id,
                    'name': item.title,
                    'price': str(item.price),
                    'image': image_url,
                    'type': 'fashion',
                    'model_name': 'FashionItem',
                    'stock': item.stock  # Include stock info
                })
    except Exception as e:
        print(f"Error fetching fashion items: {e}")
    
    try:
        # Get Buildings/Properties
        buildings = Building.objects.filter(is_available=True, stock__gt=0)
        if cart_item_numeric_ids:
            buildings = buildings.exclude(id__in=cart_item_numeric_ids)
        buildings = buildings[:4]
        
        for item in buildings:
            first_image = item.images.first()
            if first_image and hasattr(first_image, 'image') and first_image.image:
                image_url = first_image.image.url
            else:
                # Use data URL placeholder
                image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-family='Arial' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E"
            
            recommended_products.append({
                'id': item.id,
                'name': item.title,
                'price': str(item.price),
                'image': image_url,
                'type': 'property',
                'model_name': 'Building',
                'stock': item.stock  # Include stock info
            })
    except Exception as e:
        print(f"Error fetching buildings: {e}")
    
    try:
        # Get Vehicles if the model exists
        if Vehicleinformation:
            vehicles = Vehicleinformation.objects.filter(is_available=True, stock__gt=0)
            if cart_item_numeric_ids:
                vehicles = vehicles.exclude(id__in=cart_item_numeric_ids)
            vehicles = vehicles[:4]
            
            for item in vehicles:
                first_image = item.images.first()
                if first_image and hasattr(first_image, 'image') and first_image.image:
                    image_url = first_image.image.url
                else:
                    # Use data URL placeholder
                    image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-family='Arial' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E"
                
                recommended_products.append({
                    'id': item.id,
                    'name': f"{item.brand} {item.model}",
                    'price': str(item.price),
                    'image': image_url,
                    'type': 'vehicle',
                    'model_name': 'Vehicleinformation',
                    'stock': item.stock  # Include stock info
                })
    except Exception as e:
        print(f"Error fetching vehicles: {e}")
    
    try:
        # Get Commodities
        commodities = Commodity.objects.filter(is_available=True, stock__gt=0)
        if cart_item_numeric_ids:
            commodities = commodities.exclude(id__in=cart_item_numeric_ids)
        commodities = commodities[:4]
        
        for item in commodities:
            first_image = item.images.first()
            if first_image and hasattr(first_image, 'image') and first_image.image:
                image_url = first_image.image.url
            else:
                # Use data URL placeholder
                image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-family='Arial' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E"
            
            recommended_products.append({
                'id': item.id,
                'name': item.name,
                'price': str(item.price),
                'image': image_url,
                'type': 'commodity',
                'model_name': 'Commodity',
                'stock': item.stock  # Include stock info
            })
    except Exception as e:
        print(f"Error fetching commodities: {e}")
    
    # Shuffle and limit to 8 products
    import random
    random.shuffle(recommended_products)
    recommended_products = recommended_products[:8]

    return render(request, 'CART/viewcart.html', {
        'cart_items': cart_items,
        'cart_total': total,
        'cart_count': cart_count,
        'recommended_products': recommended_products
    })
# -------------------------------
# Update quantity (AJAX)
# -------------------------------
def update_cart(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        change = data.get('change', 0)
        cart = get_cart(request)
        
        if id not in cart:
            return JsonResponse({'error': 'Item not in cart'}, status=404)
        
        # Get current quantity and product info
        current_quantity = cart[id]['quantity']
        new_quantity = current_quantity + change
        
        # If removing item completely
        if new_quantity <= 0:
            del cart[id]
            removed = True
            quantity = 0
        else:
            # Need to check stock limits when increasing quantity
            if change > 0:  # Only check stock when adding
                # Get the actual product to check available stock
                model_type = cart[id].get('model_type')
                product_id = cart[id].get('product_id')
                
                if model_type and product_id:
                    try:
                        # Get ContentType for the model
                        ct_queryset = ContentType.objects.filter(model=model_type.lower())
                        content_type = None
                        for ct in ct_queryset:
                            if ct.model_class() is not None:
                                content_type = ct
                                break
                        
                        if content_type:
                            product = content_type.get_object_for_this_type(id=product_id)
                            stock_available = getattr(product, 'stock', 0)
                            
                            # Check if new quantity exceeds stock
                            if new_quantity > stock_available:
                                return JsonResponse({
                                    'error': f'Cannot add more. Only {stock_available} item(s) available in stock.',
                                    'max_reached': True,
                                    'max_quantity': stock_available,
                                    'current_quantity': current_quantity
                                }, status=400)
                    except Exception as e:
                        print(f"Error checking stock: {e}")
            
            cart[id]['quantity'] = new_quantity
            removed = False
            quantity = new_quantity
        
        # Recalculate totals
        total = sum(float(v['price']) * int(v['quantity']) for v in cart.values())
        count = sum(int(v['quantity']) for v in cart.values())
        
        request.session.modified = True
        
        return JsonResponse({
            'removed': removed,
            'quantity': quantity,
            'cart_total': total,
            'cart_count': count
        })

# -------------------------------
# Remove item from cart (AJAX)
# -------------------------------
def remove_cart(request, id):
    cart = get_cart(request)
    if id in cart:
        del cart[id]
        request.session.modified = True

    total = sum(v['price'] * v['quantity'] for v in cart.values())
    count = sum(v['quantity'] for v in cart.values())

    return JsonResponse({'cart_total': total, 'cart_count': count})

@login_required
def order_history(request):
    query = request.GET.get('q', '').strip() # Clean the query
    orders = Orders.objects.filter(buyer=request.user).order_by('-created_at')
    
    if query:
        orders = orders.filter(
            Q(location__icontains=query) | 
            Q(status__icontains=query) |
            Q(phone__icontains=query) |
            Q(id__icontains=query) #
        )

    context = {
        'orders': orders,
        'search_query': query
    }
    return render(request, 'CART/orders.html', context)

def mark_as_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    notification.is_read = True
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))




@login_required(login_url='/auth/')
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('CART:view_cart')

    # Prepare cart items for display
    cart_items = []
    total = 0
    for item_id, item_data in cart.items():
        subtotal = item_data['price'] * item_data['quantity']
        total += subtotal
        cart_items.append({
            'id': item_id, # This is still 'commodity_1' for the template
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'image': item_data.get('image'),
            'model': item_data.get('model_type', 'commodity')
        })

    if request.method == 'POST':
        method = request.POST.get('payment_method')
        phone = request.POST.get('phone')
        location = request.POST.get('address')
        full_name = request.POST.get('full_name', request.user.get_full_name())

        if not method:
            messages.error(request, "Please select a payment method.")
            return render(request, 'CART/checkout.html', {'cart_items': cart_items, 'cart_total': total})

        try:
            with transaction.atomic():
                # STEP 1: Create Payment Instance
                payment = Payment.objects.create(
                    user=request.user,
                    cart_total=total,
                    method=method
                )
                payment.generate_verification_code()

                # STEP 2: Create Orders
                for item in cart_items:
                    # Get the ContentType (e.g., 'commodity')
                    c_type = ContentType.objects.get(model=item['model'].lower())
                    
                    # FIX: Extract numeric ID from string like 'commodity_1'
                    # We split by '_' and take the last part, then convert to int
                    try:
                        raw_id = str(item['id']).split('_')[-1]
                        numeric_id = int(raw_id)
                    except (ValueError, IndexError):
                        # Fallback if the ID was already a numeric string
                        numeric_id = int(item['id'])

                    Orders.objects.create(
                        buyer=request.user,
                        content_type=c_type,
                        object_id=numeric_id,  # Now a valid Integer
                        quantity=item['quantity'],
                        full_name=full_name,
                        phone=phone,
                        location=location,
                        payment_id=payment.id, # Pass the ID directly
                        status='pending'
                    )

                # Clear cart after successful order creation
                request.session['cart'] = {}
                
                messages.success(request, f"Transaction initialized. Please verify your {method} payment.")
                return redirect('CART:payment_verify', payment_id=payment.id)

        except Exception as e:
            # This will catch the 'Field id expected a number' error if it persists
            messages.error(request, f"Transaction failed: {str(e)}")
            return redirect('CART:checkout')

    return render(request, 'CART/checkout.html', {
        'cart_items': cart_items,
        'cart_total': total
    })
@login_required
def payment_verify(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if request.method == 'POST':
        # Collect the 6-digit OTP from the form
        otp_digits = [request.POST.get(f'd{i}', '') for i in range(1, 7)]
        entered_code = "".join(otp_digits)

        if len(entered_code) < 6:
            messages.error(request, "Please enter all 6 digits.")
            return render(request, 'CART/payment_verify.html', {'payment': payment})

        if entered_code == payment.verification_code:
            try:
                with transaction.atomic():
                    # 1. Mark payment as paid
                    payment.is_paid = True
                    payment.save()

                    # 2. Get all related orders for this payment
                    orders = Orders.objects.filter(payment_id=payment.id)
                    
                    if not orders.exists():
                        messages.warning(request, "Payment successful but no orders were linked.")
                        return redirect('BUS_SYSTEM:marketplace')
                    # 3. STOCK REDUCTION LOOP
                    for order in orders:
                        # Identify the product via GenericForeignKey
                        product = order.product 
                        model_name = order.content_type.model.lower()
                        # --- Logic for FashionItem (Your new app) ---
                        if model_name == 'fashionitem':
                            if product.stock >= order.quantity:
                                product.stock -= order.quantity
                                product.save()
                            else:
                                messages.warning(request, f"Note: {product.title} was low on stock.")
                        # --- Logic for existing models (Building/Vehicle/Commodity) ---
                        elif model_name == 'building' or model_name == 'vehicleinformation':
                            product.is_available = False
                            product.save()            
                        elif model_name == 'commodity':
                            if product.stock >= order.quantity:
                                product.stock -= order.quantity
                                product.save()
                    # 4. Update order statuses to confirmed
                    orders.update(status='confirmed', is_paid=True)
                    # 5. Notify the User
                    Notification.objects.create(
                        user=request.user,
                        title="Order Confirmed ✅",
                        message=f"Your payment of ${payment.cart_total} for Order #{orders.first().id} was successful."
                    )

                    # 6. Clear session cart
                    request.session.pop('cart', None)
                    messages.success(request, "Payment verified! Your fashion items are ready for shipping.")
                    return redirect('CART:thank_you')
            except Exception as e:
                messages.error(request, f"Processing Error: {str(e)}")
                return redirect('CART:view_cart')
        else:
            messages.error(request, "Invalid verification code. Please try again.")
    return render(request, 'CART/payment_verify.html', {'payment': payment})


@login_required(login_url='/account/login/')
def thank_you(request, order_id=None):
    """
    Display order confirmation page after successful purchase
    """
    # Try to get order_id from URL parameter or session
    if not order_id:
        order_id = request.session.get('last_order_id')
    
    if order_id:
        try:
            # Get the specific order and ensure it belongs to the logged-in buyer
            order = Orders.objects.get(id=order_id, buyer=request.user)
            context = {
                'order': order
            }
            return render(request, 'CART/thaank_you.html', context)
        except Orders.DoesNotExist:
            messages.error(request, "Order not found or you don't have permission to view it.")
            return redirect('BUS_SYSTEM:marketplace')
    else:
        # If no order_id provided, get the most recent order for the user
        try:
            latest_order = Orders.objects.filter(buyer=request.user).latest('created_at')
            context = {
                'order': latest_order
            }
            return render(request, 'CART/thaank_you.html', context)
        except Orders.DoesNotExist:
            messages.error(request, "No orders found. Please make a purchase first.")
            return redirect('BUS_SYSTEM:marketplace')


@login_required
def order_success_view(request, order_id):
    # Fetch the order and ensure the logged-in user is the owner
    order = get_object_or_404(Orders, id=order_id, buyer=request.user)
    # Identify the type of product for specialized messaging
    product_type = order.content_type.model  # returns 'building', 'vehicleinformation', or 'commodity'
    context = {
        'order': order,
        'product_type': product_type,
        'is_real_estate': product_type == 'building',
        'is_vehicle': product_type == 'vehicleinformation',
    }
    
    return render(request, 'CART/thaank_you.html', context)


@login_required
def confirm_order(request, order_id):
    order = get_object_or_404(Orders, id=order_id, buyer=request.user)
# Get the latest payment related to this user (or better: link it to order)
    payment = Payment.objects.filter(user=request.user).order_by('-created_at').first()
    if request.method == 'POST':
        otp_digits = [request.POST.get(f'digit{i}', '') for i in range(1, 7)]
        submitted_otp = "".join(otp_digits)
        if len(submitted_otp) < 6:
            messages.error(request, "Please fill in all 6 digits of the code.")
        elif payment and payment.verify_code(submitted_otp):
            order.status = 'paid'
            if hasattr(order, 'is_paid'):
                order.is_paid = True
            order.save()
            messages.success(request, f"Payment for Order #{order.id} Verified Successfully!")
            return redirect('DASHBOARD:buyer_dashboard')
        else:
            messages.error(request, "Invalid verification code. Please check and try again.")
    return render(request, 'CART/confirm_order.html', {'order': order})



def product_detail(request, model_name, id):
    """
    View to display product details based on model name and ID
    """
    from FASHIONITEM.models import FashionItem
    from BUS_SYSTEM.models import Building, Commodity
    
    # Try to import Vehicleinformation (adjust import path as needed)
    try:
        from BUS_SYSTEM.models import Vehicleinformation
    except ImportError:
        Vehicleinformation = None
    
    product = None
    template_name = 'BUS_SYSTEM/product_detail.html'
    
    # Determine which model to use based on model_name
    if model_name == 'FashionItem':
        product = get_object_or_404(FashionItem, id=id, is_available=True)
        template_name = 'FASHIONITEM/shoesdetail.html'
        context = {
            'product': product,  # FashionItem template expects 'product'
            'model_name': model_name,
        }
        
    elif model_name == 'Building':
        product = get_object_or_404(Building, id=id, is_available=True)
        template_name = 'BUILDING/building_detail.html'
        context = {
            'house': product,  # Building template expects 'house'
            'model_name': model_name,
        }
        
    elif model_name == 'Vehicleinformation' and Vehicleinformation:
        product = get_object_or_404(Vehicleinformation, id=id, is_available=True)
        template_name = 'BUS_SYSTEM/vehicle_detail.html'
        context = {
            'vehicle': product,  # Vehicle template expects 'vehicle'
            'model_name': model_name,
        }
        
    elif model_name == 'Commodity':
        product = get_object_or_404(Commodity, id=id, is_available=True)
        template_name = 'BUS_SYSTEM/product_detail.html'
        context = {
            'commodity': product,  # Commodity template expects 'commodity'
            'model_name': model_name,
        }
        
    else:
        from django.http import Http404
        raise Http404(f"Product type '{model_name}' not found")
    
    return render(request, template_name, context)
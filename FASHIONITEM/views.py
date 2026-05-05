from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Avg,Sum, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from decimal import Decimal

from FASHIONITEM.forms import FashionItemForm, FashionImageFormSet
from .models import FashionImage, FashionItem
from BUS_SYSTEM.models import Review
from CART.models import Notification
from django.contrib.contenttypes.models import ContentType

# Helper function to get category counts for sidebar
def get_category_counts():
    """Get count of items in each category"""
    categories = ['SHOES', 'CLOTHES', 'BAGS', 'ACCESSORIES', 'OTHER']
    counts = {}
    for cat in categories:
        counts[cat] = FashionItem.objects.filter(category=cat, is_available=True).count()
    return counts

def shoesplace(request):
    """Main marketplace view with filters, sorting, and pagination"""
    # Base queryset - only show available items
    items = FashionItem.objects.filter(is_available=True).order_by('-created_at')
    
    # Get filter values from URL
    category_filter = request.GET.get('category')
    gender_filter = request.GET.get('gender')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    
    # Apply category filter
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Apply gender filter
    if gender_filter:
        items = items.filter(gender=gender_filter)
    
    # Apply price range filter
    if min_price:
        try:
            min_price = Decimal(min_price)
            items = items.filter(price_after_discount__gte=min_price)
        except:
            pass
    
    if max_price:
        try:
            max_price = Decimal(max_price)
            items = items.filter(price_after_discount__lte=max_price)
        except:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        items = items.order_by('price_after_discount')
    elif sort_by == 'price_high':
        items = items.order_by('-price_after_discount')
    elif sort_by == 'popular':
        # Use a different approach - order by rating or number of reviews
        items = items.annotate(num_reviews=Count('reviews')).order_by('-num_reviews', '-created_at')
    else:  # newest
        items = items.order_by('-created_at')
    
    # Get category counts for sidebar
    category_counts = get_category_counts()
    
    # Calculate total items count (remove the views aggregation since it doesn't exist)
    total_items = items.count()
    
    # Pagination: 12 items per page
    paginator = Paginator(items, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'category_counts': category_counts,
        'total_items': total_items,
        'current_filters': {
            'category': category_filter,
            'gender': gender_filter,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by,
        }
    }
    return render(request, 'FASHIONITEM/shoesmarket.html', context)

def submit_fashion_item(request):
    """Upload new fashion item"""
    if request.method == 'POST':
        form = FashionItemForm(request.POST)
        formset = FashionImageFormSet(
            request.POST,
            request.FILES,
            queryset=FashionImage.objects.none()
        )

        if form.is_valid() and formset.is_valid():
            fashion_item = form.save(commit=False)
            fashion_item.seller = request.user
            fashion_item.is_available = True  # New items are available by default
            fashion_item.save()

            # Save images
            for f in formset:
                if f.cleaned_data:
                    image = f.save(commit=False)
                    image.fashion_item = fashion_item
                    image.save()

            messages.success(request, "Item uploaded successfully ✅")
            return redirect('BUS_SYSTEM:mainpage')
        else:
            messages.error(request, "Fix errors below ❌")

    else:
        form = FashionItemForm()
        formset = FashionImageFormSet(queryset=FashionImage.objects.none())

    return render(request, 'FASHIONITEM/upload_items.html', {
        'form': form,
        'formset': formset
    })

@login_required
@require_POST
def add_to_cart_ajax(request):
    """AJAX endpoint to add item to cart without page reload"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        item_type = data.get('item_type', 'fashionitem')
        quantity = int(data.get('quantity', 1))
        
        # Get the item
        if item_type == 'fashionitem':
            item = get_object_or_404(FashionItem, id=item_id, is_available=True)
        else:
            return JsonResponse({'success': False, 'message': 'Invalid item type'}, status=400)
        
        # Check stock
        if item.stock < quantity:
            return JsonResponse({'success': False, 'message': 'Not enough stock available'})
        
        # Get or create cart - you'll need to import your Cart model
        from CART.models import Cart, CartItem
        
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        
        # Add to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            content_type=ContentType.objects.get_for_model(item),
            object_id=item.id,
            defaults={'quantity': quantity, 'price': item.price_after_discount or item.price}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Get updated cart count
        cart_count = cart.items.count()
        
        return JsonResponse({
            'success': True,
            'message': f'{item.title} added to cart',
            'cart_count': cart_count,
            'item_name': item.title
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def buy_now_ajax(request, item_id):
    """AJAX endpoint to handle direct purchase with automatic removal"""
    try:
        with transaction.atomic():
            item = get_object_or_404(FashionItem, id=item_id, is_available=True)
            
            # Check if in stock
            if item.stock <= 0:
                return JsonResponse({
                    'success': False, 
                    'message': 'Item is out of stock'
                })
            
            # Import Orders model
            from CART.models import Orders
            
            # Create order immediately
            order = Orders.objects.create(
                buyer=request.user,
                content_object=item,
                quantity=1,
                total_price=item.price_after_discount or item.price,
                full_name=request.user.get_full_name() or request.user.username,
                phone=request.user.profile.phone if hasattr(request.user, 'profile') else '',
                location='Kigali',  # Default location
                is_paid=False,  # Will be paid at checkout
                status='pending'
            )
            
            # Reduce stock
            item.stock -= 1
            
            # If stock becomes 0, mark as unavailable
            if item.stock == 0:
                item.is_available = False
            
            item.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title="Order Initiated",
                message=f"Your order for {item.title} has been initiated. Complete payment to confirm."
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Item reserved! Redirecting to checkout...',
                'checkout_url': f'/cart/checkout/?order_id={order.id}'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def toggle_wishlist_ajax(request, item_id):
    """AJAX endpoint to toggle wishlist status"""
    try:
        item = get_object_or_404(FashionItem, id=item_id)
        
        # Import Wishlist model if exists, or create notification only
        # Since Wishlist might not exist, let's just use notifications
        try:
            from CART.models import Wishlist
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                content_type=ContentType.objects.get_for_model(item),
                object_id=item.id
            )
            
            if not created:
                wishlist_item.delete()
                is_wishlisted = False
                message = "Removed from wishlist"
            else:
                is_wishlisted = True
                message = "Added to wishlist"
        except ImportError:
            # If Wishlist model doesn't exist, just show notification
            is_wishlisted = True
            message = "Added to wishlist (notification saved)"
        
        # Create notification for wishlist
        Notification.objects.create(
            user=request.user,
            title="Item Wishlisted" if is_wishlisted else "Item Removed",
            message=f"You've {message.lower()} {item.title}"
        )
        
        return JsonResponse({
            'success': True,
            'message': message,
            'is_wishlisted': is_wishlisted
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_POST
def track_view_ajax(request, item_id):
    """Track product views"""
    try:
        item = get_object_or_404(FashionItem, id=item_id)
        
        # Use session to prevent multiple counts from same session
        session_key = f'viewed_item_{item_id}'
        if not request.session.get(session_key, False):
            request.session[session_key] = True
            item.views += 1
            item.save()
            
            # Get total views across all items
            total_views = FashionItem.objects.aggregate(total=Sum('views'))['total'] or 0
            
            return JsonResponse({
                'success': True,
                'item_views': item.views,
                'total_views': total_views
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Already viewed in this session',
                'total_views': 0
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
def fashion_detail(request, pk):
    """Product detail page with session-based view tracking"""
    item = get_object_or_404(FashionItem, pk=pk)
    
    # Track view using session
    session_key = f'viewed_item_{item.id}'
    if not request.session.get(session_key, False):
        request.session[session_key] = True
    
    # Get related items (same category or brand)
    related_items = FashionItem.objects.filter(
        Q(category=item.category) | Q(brand=item.brand),
        is_available=True
    ).exclude(id=item.id)[:8]
    
    # Safely get reviews - handle if related_name is different
    try:
        reviews = item.reviews.all().order_by('-created_at')
    except AttributeError:
        # If reviews doesn't exist, try with a different related_name or set empty
        from BUS_SYSTEM.models import Review
        reviews = Review.objects.filter(product_id=item.id).order_by('-created_at')
    
    # Check if user has purchased this item (for review eligibility)
    has_purchased = False
    if request.user.is_authenticated:
        try:
            from CART.models import Orders
            from django.contrib.contenttypes.models import ContentType
            
            has_purchased = Orders.objects.filter(
                buyer=request.user,
                object_id=item.id,
                content_type=ContentType.objects.get_for_model(item),
                status='delivered'
            ).exists()
        except:
            has_purchased = False
    
    context = {
        'item': item,
        'related_items': related_items,
        'reviews': reviews,
        'has_purchased': has_purchased,
    }
    return render(request, 'FASHIONITEM/shoesdetail.html', context)    
@login_required
def payment_verify(request, item_id):
    """Simulates payment verification and reduces stock"""
    item = get_object_or_404(FashionItem, id=item_id)
    
    with transaction.atomic():
        if item.stock > 0:
            item.stock -= 1
            if item.stock == 0:
                item.is_available = False
            item.save()
            
            # Create order record
            from CART.models import Orders
            order = Orders.objects.create(
                buyer=request.user,
                content_object=item,
                quantity=1,
                total_price=item.price_after_discount or item.price,
                full_name=request.user.get_full_name() or request.user.username,
                phone=request.user.profile.phone if hasattr(request.user, 'profile') else '',
                location='Kigali',
                is_paid=True,
                status='confirmed'
            )
            
            return render(request, 'BUS_SYSTEM/payment_success.html', {'item': item, 'order': order})
        else:
            return render(request, 'BUS_SYSTEM/out_of_stock.html', {'item': item})

@login_required
@require_POST
def add_review(request, item_id):
    """Add a review for a purchased item"""
    if request.method == "POST":
        item = get_object_or_404(FashionItem, id=item_id)
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Check if user has purchased this item
        from CART.models import Orders
        
        has_purchased = Orders.objects.filter(
            buyer=request.user,
            object_id=item.id,
            content_type=ContentType.objects.get_for_model(item),
            status='delivered'
        ).exists()
        
        if not has_purchased:
            messages.error(request, "You can only review items you've purchased and received.")
            return redirect('FASHIONITEM:detail', pk=item.id)
        
        # Check if user already reviewed
        existing_review = Review.objects.filter(
            product=item,
            user=request.user
        ).first()
        
        if existing_review:
            messages.error(request, "You've already reviewed this item.")
            return redirect('FASHIONITEM:detail', pk=item.id)
        
        # Create the review
        Review.objects.create(
            product=item,
            user=request.user,
            rating=rating_value,
            comment=comment
        )
        
        # Update the average rating on the FashionItem
        item.update_rating()
        
        messages.success(request, "Thank you for your review!")
        return redirect('FASHIONITEM:detail', pk=item.id)

@login_required
def get_cart_count(request):
    """API endpoint to get current cart count"""
    try:
        from CART.models import Cart
        cart = Cart.objects.get(user=request.user, is_active=True)
        count = cart.items.count()
        return JsonResponse({'count': count})
    except:
        return JsonResponse({'count': 0})
    
    
    
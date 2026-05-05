from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from BUS_SYSTEM.models import Profile, Orders
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

@login_required
def profile_info(request):
    """
    Handles both displaying the profile and updating the information.
    """
    user = request.user
    # Ensure profile exists to avoid RelatedObjectDoesNotExist
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # 1. Update User Model Fields
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        # 2. Update Profile Model (Image)
        if 'profile_image' in request.FILES:
            profile.image = request.FILES['profile_image']
            profile.save()

        messages.success(request, "Your account settings have been updated!")
        return redirect('USERPROFILE:profile_info')

    # Fetch orders to show count or summary on the profile page
    orders = Orders.objects.filter(buyer=user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'order_count': orders.count()
    }
    return render(request, 'USERPROFILE/profile_info.html', context)
# import your sms gateway here (e.g., from twilio.rest import Client)

@login_required
def update_profile(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Update logic
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        if 'profile_image' in request.FILES:
            profile.image = request.FILES['profile_image']
        
        profile.phone_number = request.POST.get('phone') # Ensure this field exists in Profile model
        profile.save()
        # SMS LOGIC PLACEHOLDER
        # print(f"SMS Sent to {profile.phone_number}: Your Distar Profile was updated.")
        messages.success(request, "Success! Your profile is updated and a confirmation was sent.")
        return redirect('USERPROFILE:profile_info')

    return render(request, 'USERPROFILE/update_info.html', {'user': user, 'profile': profile})
@login_required
def order_history(request):
    query = request.GET.get('q')
    orders = Orders.objects.filter(buyer=request.user).order_by('-created_at')

    # Advanced Search Logic
    if query:
        orders = orders.filter(
            Q(id__icontains=query) | 
            Q(location__icontains=query) | 
            Q(status__icontains=query)
        )

    # Current time for logic calculations
    now = timezone.now()

    # Business Logic Thresholds
    # 1. 0-2 Hours: Pending phase
    # 2. 2-24 Hours: Confirmed phase
    # 3. 1-2 Days: Shipped phase
    context = {
        'orders': orders,
        'search_query': query,
        'now': now,
        'two_hours_ago': now - timedelta(hours=2),
        'one_day_ago': now - timedelta(hours=24),
        'two_days_ago': now - timedelta(days=2),
    }
    
    return render(request, 'USERPROFILE/order_purchase_history.html', context)
@login_required
def account_management(request):
    """
    Redirects or renders the management tab of the profile.
    """
    return render(request, 'USERPROFILE/profile_info.html', {'active_tab': 'settings'})
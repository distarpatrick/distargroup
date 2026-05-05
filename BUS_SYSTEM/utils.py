# utils.py (create this file in your BUS_SYSTEM folder)
from django.shortcuts import redirect
from django.contrib import messages
from BUS_SYSTEM.models import Profile

def check_seller_or_admin(view_func):
    """
    Decorator to check if user has seller or admin role
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect('BUS_SYSTEM:auth_system')
        
        try:
            profile = request.user.profile
            if profile.role in ['seller', 'admin']:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Access Denied. Seller or Admin privileges required.")
                return redirect('BUS_SYSTEM:mainpage')
        except Profile.DoesNotExist:
            messages.error(request, "Profile not found. Please contact support.")
            return redirect('BUS_SYSTEM:auth_system')
    
    return wrapper


def is_seller_or_admin(user):
    """
    Helper function to check if user is seller or admin
    """
    if not user.is_authenticated:
        return False
    
    try:
        profile = user.profile
        return profile.role in ['seller', 'admin']
    except Profile.DoesNotExist:
        return False
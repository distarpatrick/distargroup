from django.shortcuts import redirect
from django.contrib import messages

def seller_required(view_func):
    """
    Decorator to check if user has seller OR admin role
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect('BUS_SYSTEM:auth_system')
        
        try:
            # Check if user has profile and role is seller or admin
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                if profile.role in ['seller', 'admin']:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "Access Denied. Seller or Admin privileges required.")
                    return redirect('BUS_SYSTEM:mainpage')
            else:
                messages.error(request, "Profile not found. Please contact support.")
                return redirect('BUS_SYSTEM:auth_system')
        except Exception as e:
            print(f"Decorator error: {e}")
            messages.error(request, "Access Denied. Please contact support.")
            return redirect('BUS_SYSTEM:auth_system')
    
    return wrapper


def admin_required(view_func):
    """
    Decorator for admin-only access
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please login first.")
            return redirect('BUS_SYSTEM:auth_system')
        
        try:
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                if profile.role == 'admin':
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "Admin access required.")
                    return redirect('BUS_SYSTEM:mainpage')
            else:
                messages.error(request, "Profile not found.")
                return redirect('BUS_SYSTEM:auth_system')
        except Exception as e:
            print(f"Admin decorator error: {e}")
            messages.error(request, "Access Denied.")
            return redirect('BUS_SYSTEM:auth_system')
    
    return wrapper
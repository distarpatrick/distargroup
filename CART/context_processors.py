from .models import Notification
from django.db.models import Q

def notification_system(request):
    if request.user.is_authenticated:
        # Show: 1. Notifications for HIM + 2. Admin Broadcasts
        notifications = Notification.objects.filter(
            Q(user=request.user) | Q(is_broadcast=True)
        ).order_by('-created_at')
    else:
        # Show: ONLY Admin Broadcasts (for guests/logged out)
        notifications = Notification.objects.filter(is_broadcast=True).order_by('-created_at')
    
    return {
        'all_notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count()
    }
from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # This makes the code visible in the table list
    list_display = ('id', 'user', 'building', 'verification_code', 'is_paid', 'created_at')
    
    # Optional: Adds filters on the right side
    list_filter = ('is_paid', 'created_at')
    
    # Optional: Allows you to search by user or building title
    search_fields = ('user__username', 'building__title', 'verification_code')
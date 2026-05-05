from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import get_random_string
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Cart"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey("content_type", "object_id")
    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product}"
# Create your models here.

PAYMENT_METHODS = [
    ('card', 'Credit/Debit Card'),
    ('mobile', 'Mobile Money'),
    ('paypal', 'PayPal'),
    ('bank', 'Bank Transfer'),
    ('crypto', 'Cryptocurrency'),
]

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart_total = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50)
    is_paid = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_verification_code(self):
        import random
        self.verification_code = str(random.randint(100000, 999999))
        self.save()
    
    def verify_code(self, code):
        if self.verification_code == code:
            self.is_paid = True
            self.save()
            return True
        return False
        

class Notification(models.Model):
    # Link to the User model (from BUS_SYSTEM or Django default)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_broadcast = models.BooleanField(default=False) # True for Admin SMS-style
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title      

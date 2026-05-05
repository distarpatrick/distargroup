from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.contrib.auth.models import User
    
class FashionItem(models.Model):
    CATEGORY_CHOICES = [
        ('CLOTHES', 'Clothing'),
        ('SHOES', 'Shoes'),
        ('BAGS', 'Bags'),
        ('ACCESSORIES', 'Accessories'),
        ('OTHER', 'Other'),
    ]
    
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('UNISEX', 'Unisex'),
        ('KIDS', 'Kids'),
    ]

    title = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='UNISEX')
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    # Fashion specific details
    size = models.CharField(max_length=50, help_text="e.g., XL, 42, 10-inch")
    color = models.CharField(max_length=50)
    material = models.CharField(max_length=100, blank=True)
    views = models.PositiveIntegerField(default=0, help_text="Number of times this item has been viewed")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fashion_items")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.size})"    
    
class FashionImage(models.Model):
    fashion_item = models.ForeignKey(FashionItem, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="fashion/images/")
    video = models.FileField(upload_to="fashion/videos/", blank=True, null=True)
    
    def __str__(self):
        return f"Media for {self.fashion_item.title}"  
    
    @property
    def price_after_discount(self):
        if self.discount:
            return self.price - self.discount
        return self.price
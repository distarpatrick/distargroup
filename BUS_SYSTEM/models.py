from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.fields import GenericRelation

class Building(models.Model):
    _CHOICES = [
        ('Residential', 'Residential'),
        ('Apartment', 'Apartment'),
        ('Industrial', 'Industrial'),
        ('Commercial', 'Commercial')
    ]
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    property_type = models.CharField(max_length=50, choices=_CHOICES)
    property_term = models.CharField(max_length=50)
    year_built = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=200)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    plot_area = models.IntegerField(null=True, blank=True)
    furnished = models.CharField(max_length=10)
    parking = models.CharField(max_length=10)
    balcony = models.CharField(max_length=10)
    realtor = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    discount=models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_items")
    def __str__(self):
        return self.title


class BuildingImage(models.Model):
    property = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/")
    video = models.FileField(upload_to='building/videos/', blank=True, null=True)
    
    def __str__(self):
        return f"Image for {self.property.title}"

class Vehicleinformation(models.Model):
    MOTO_CHOICES = [
        ('cruiser moto', 'Cruiser Moto'),
        ('sport', 'Sport'),
        ('dual-sport', 'Dual-Sport'),
        ('touring moto', 'Touring Moto'),
        ('off-road moto', 'Off-Road Moto'),
        ('scooter', 'Scooter'),
        ('standard moto', 'Standard Moto'),
        ('other', 'other'),
    ]
    VEHICLE_TYPE = [('Car','Car'), ('Motorcycle','Motorcycle')]
    CONDITION = [('New','New'), ('Used','Used')]
    TRANSMISSION = [('Manual','Manual'), 
                    ('Automatic','Automatic')
                    ]
    FUEL_TYPE = [('Petrol','Petrol'), ('Diesel','Diesel'), ('Electric','Electric'), ('Hybrid','Hybrid')]
    
    SALE = 'sale'
    RENT = 'rent'
    
    TYPE_CHOICES = [
        (SALE, 'For Sale'),
        (RENT, 'For Rent')
    ]
    stock = models.IntegerField(default=1, blank=True)
    product_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=SALE)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION, blank=True, null=True)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION, blank=True, null=True)
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE, blank=True, null=True)
    mileage = models.IntegerField(blank=True, null=True)
    engine_capacity = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(max_length=300, blank=True)
    moto_type = models.CharField(max_length=20, choices=MOTO_CHOICES, blank=True, null=True)
    seller_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_items")
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.brand} {self.model}"

class VehicleinformationImage(models.Model):
    vehicle = models.ForeignKey(Vehicleinformation, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicles/')
    video = models.FileField(upload_to='vehicles/videos/', blank=True, null=True)

    def __str__(self):
        return f"Image for {self.vehicle.brand} {self.vehicle.model}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )

    def __str__(self):
        return self.name


class Commodity(models.Model):
    CATEGORY_TYPE = [
        ('Agricultural product', 'Agricultural Product'),
        ('food product', 'food product'),
        ('Consumer goods', 'consumer goods'),
        ('food product', 'food product'),
        ('manufactured good', 'goods'),
        ('bevarages', 'bevarages'),
        ('Electronics', 'Electronics'),
    ]

    name = models.CharField(max_length=200)
    views = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=CATEGORY_TYPE)
    discount=models.DecimalField(max_digits=20, decimal_places=2)
    location=models.CharField(max_length=50)
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_items")
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return self.name
    
    def update_rating(self):
        """Method to recalculate average rating whenever a new review is added"""
        reviews = self.reviews.all()
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = avg
            self.save()
            
            
class Review(models.Model):
    """
    Review model for Commodity products
    """
    product = models.ForeignKey(
        'Commodity', 
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commodity_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Prevent duplicate reviews

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}⭐)"            
  
    
    
class Profile(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profiles/', default='default.png')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    



class CommodityImage(models.Model):
    product = models.ForeignKey(
        Commodity,
        related_name='images',
        on_delete=models.CASCADE
        )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    video = models.FileField(upload_to='product/videos/', blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.name}"
    
from django.contrib.auth.models import User

class Orders(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')

    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    full_name = models.CharField(max_length=200)
    city = models.CharField(max_length=100, default="Kigali")
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100)

    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    order_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate total price if product has price
        if self.product and hasattr(self.product, 'price'):
            self.total_price = self.quantity * self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.buyer.username}"
    
    def get_commission(self):
        """Calculates 2% platform fee"""
        if self.total_price:
            return self.total_price * Decimal('0.02')
        return 0

    def get_seller_earning(self):
        """Calculates what the seller actually gets (98%)"""
        if self.total_price:
            return self.total_price * Decimal('0.98')
        return 0

    def confirm_and_reduce_stock(self):
        """Call this when seller confirms the order"""
        if self.product and self.product.stock >= self.quantity:
            self.product.stock -= self.quantity
            self.product.save()
            self.status = 'confirmed'
            self.save()
            return True
        return False
    
    def get_real_time_status(self):
        """
        Returns the status based on time passed if still 'pending'.
        """
        now = timezone.now()
        if self.status == 'pending':
            if now > self.created_at + timedelta(hours=24):
                return "Confirmed" # Logic: Auto-confirm after 24h
            elif now > self.created_at + timedelta(hours=2):
                return "Processing" # Logic: In review after 2h
        return self.get_status_display()


# Register your models here.
# admin.py
from django.contrib import admin
from .models import Building,Category
from .models import Vehicleinformation, VehicleinformationImage,Commodity

class ImageInline(admin.TabularInline):
    model = VehicleinformationImage
    extra = 1

@admin.register(Vehicleinformation)
class VehicleAdmin(admin.ModelAdmin):
    inlines = [ImageInline]
    list_display = ("brand","model","price","condition","created_at")
    

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'property_type', 'location')
# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    
@admin.register(Commodity)   
class CommodityAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    
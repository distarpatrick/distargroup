from django import forms
from .models import Commodity
from .models import Vehicleinformation

class VehicleinformationForm(forms.ModelForm):
    class Meta:
        model = Vehicleinformation
        # Select all fields except 'created_at' and 'available'
        exclude = ['seller', 'approved', 'available', 'created_at']
        

        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Color'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Discount'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'transmission': forms.Select(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-control'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mileage'}),
            'engine_capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Engine Capacity'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the vehicle...', 'maxlength': 4000}),
            'seller_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seller Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),
        }

class CommodityForm(forms.ModelForm):
    class Meta:
        model = Commodity
        fields = ['name', 'price', 'type', 'category', 'location', 'discount', 'stock', 'image']
        exclude = ['seller', 'approved', 'available', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter stock quantity'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
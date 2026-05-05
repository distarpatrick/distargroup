# CART/forms.py
from django import forms
from .models import PAYMENT_METHODS

class PaymentForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Full Name', 'class': 'form-control'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Email Address', 'class': 'form-control'
    }))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'placeholder': 'Phone Number', 'class': 'form-control'
    }))
    address = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Delivery Address', 'class': 'form-control', 'rows': 3
    }))
    payment_method = forms.ChoiceField(choices=PAYMENT_METHODS, widget=forms.Select(attrs={
        'class': 'form-select'
    }))
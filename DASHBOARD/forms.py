from django import forms
from .models import Notification

class SellerNotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message']
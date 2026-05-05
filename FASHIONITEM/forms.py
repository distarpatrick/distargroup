from django import forms
from django.forms import modelformset_factory
from .models import FashionItem, FashionImage


class FashionItemForm(forms.ModelForm):
    class Meta:
        model = FashionItem
        fields = [
            'title', 'brand', 'category', 'price',
            'gender', 'size', 'color', 'material',
            'description', 'stock', 'discount'
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'fashion-input', 'required': True}),
            'brand': forms.TextInput(attrs={'class': 'fashion-input'}),
            'category': forms.Select(attrs={'class': 'fashion-input'}),
            'price': forms.NumberInput(attrs={'class': 'fashion-input'}),
            'gender': forms.Select(attrs={'class': 'fashion-input'}),
            'size': forms.TextInput(attrs={'class': 'fashion-input'}),
            'color': forms.TextInput(attrs={'class': 'fashion-input'}),
            'material': forms.TextInput(attrs={'class': 'fashion-input'}),
            'description': forms.Textarea(attrs={'class': 'fashion-input'}),
            'stock': forms.NumberInput(attrs={'class': 'fashion-input'}),
            'discount': forms.NumberInput(attrs={'class': 'fashion-input'}),
        }


class FashionImageForm(forms.ModelForm):
    class Meta:
        model = FashionImage
        fields = ['image', 'video']


FashionImageFormSet = modelformset_factory(
    FashionImage,
    form=FashionImageForm,
    extra=8,
    max_num=8
)
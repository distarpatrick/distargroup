from django.urls import path
from . import views

app_name = 'USERPROFILE'

urlpatterns = [
    path('my-profile/', views.profile_info, name='profile_info'),
    path('order-history/', views.order_history, name='order_history'),
    path('account-settings/', views.account_management, name='account_management'),
    path('update-profile/', views.update_profile, name='update_profile'),
]
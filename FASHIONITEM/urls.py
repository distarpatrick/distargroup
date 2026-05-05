from django.urls import path
from . import views
app_name = 'FASHIONITEM'

urlpatterns = [
    path('submit-fashion/', views.submit_fashion_item, name='submit_fashion'),
    path('shoesplace/', views.shoesplace, name="shoesplace"),
    path('product/<int:pk>/', views.fashion_detail, name='detail'),
    path('add-ajax/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('product/<int:item_id>/review/', views.add_review, name='add_review'),
    path('buy-now/<int:item_id>/', views.buy_now_ajax, name='buy_now_ajax'),
    path('toggle-wishlist/<int:item_id>/', views.toggle_wishlist_ajax, name='toggle_wishlist_ajax'),
]
from django.urls import path
from . import views

app_name = "CART"

urlpatterns = [
    path("view/", views.view_cart, name="view_cart"),
    path("update/<str:id>/", views.update_cart, name="update_cart"),
    path("remove/<str:id>/", views.remove_cart, name="remove_cart"),
    # REMOVE THIS LINE BELOW - it's causing the error:
    # path('ajax/add/', views.ajax_add_to_cart, name='ajax_add_to_cart'), 

    # Single clean add_to_cart URL (this one handles both regular and AJAX requests)
    path('add/<str:model_name>/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-verify/<int:payment_id>/', views.payment_verify, name='payment_verify'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('thank-you/<int:order_id>/', views.order_success_view, name='thank_you'),
    path('my-orders/', views.order_history, name='order_history'),
    path('mark-read/<int:notif_id>/', views.mark_as_read, name='mark_read'),
    path('confirm-order/<int:order_id>/', views.confirm_order, name='confirm_order'),
    
    path('product/<str:model_name>/<int:id>/', views.product_detail, name='product_detail'),
]
from django.urls import path
from . import views

app_name = 'DASHBOARD'

urlpatterns = [
    # --- Main Dashboard ---
    path('home/', views.dashboard_home, name='dashboard_home'),
    path('orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    
    # --- Buyer Dashboards ---
    path('buyer/', views.buyer_dashboard, name='buyer_dashboard'),
    path('buyer-activity/', views.buyer_dashboard, name='buyer_dashboard_admin'), 
    path('my-dashboard/', views.user_personal_dashboard, name='user_personal_dashboard'),
    
    # --- Seller Dashboard & Inventory ---
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('my-inventory/', views.seller_inventory, name='seller_inventory'),
    
    # Seller Edit/Delete (for seller's own items)
    path('inventory/edit/<str:item_type>/<int:item_id>/', views.seller_edit_item, name='seller_edit_item'),
    path('inventory/delete/<str:item_type>/<int:item_id>/', views.seller_delete_item, name='seller_delete_item'),
    
    # --- Order Management ---
    path('order/<int:order_id>/confirm/', views.confirm_order_delivery, name='confirm_order'),
    path('order/notify/', views.notify_buyer_action, name='notify_buyer_action'),
    
    # --- Admin Advanced Dashboard ---
    path('admin-panel/', views.admin_advanced_dashboard, name='admin_dashboard'),
    
    # Admin Delete URLs (for admin to delete any user or item)
    path('admin-panel/delete/user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/delete/<str:item_type>/<int:item_id>/', views.admin_delete_item, name='admin_delete_item'),
    
    # Alternative shorter URLs (redirects or same views)
    path('admin/delete/user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user_short'),
    path('delete/user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user_shortest'),
    path('delete/<str:item_type>/<int:item_id>/', views.admin_delete_item, name='admin_delete_item_short'),
    
     
     
]
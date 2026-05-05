from django.urls import path
from . import views
app_name = 'ANALYSIS'
urlpatterns = [
    path('dashboard/', views.report_dashboard, name='report_dashboard'),
    path('download/pdf/', views.download_pdf_report, name='download_pdf_report'),
    path('export/orders/', views.export_orders_csv, name='export_orders_csv'),
    path('api/stats/', views.platform_stats_api, name='platform_stats_api'),
    path('reset-stats/', views.reset_platform_stats, name='reset_platform_stats'),
]
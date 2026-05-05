from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

# Import your models
from BUS_SYSTEM.models import Building, Vehicleinformation, Commodity, Orders
from CART.models import Payment as BUSPayment
from BUILDING.models import Payment as BuildingPayment
from FASHIONITEM.models import FashionItem

# Middleware to track views using cache (no database needed)
class PlatformViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        today = timezone.now().date().isoformat()
        cache_key_views = f'platform_views_{today}'
        cache_key_unique = f'unique_visitors_{today}'
        
        # Increment total views
        total_views = cache.get(cache_key_views, 0)
        cache.set(cache_key_views, total_views + 1, 86400)  # 24 hours
        
        # Track unique visitors
        if not request.session.get('visited_today', False):
            unique_views = cache.get(cache_key_unique, 0)
            cache.set(cache_key_unique, unique_views + 1, 86400)
            request.session['visited_today'] = True
        
        return response

# Helper function to check if user is admin/staff
def is_admin(user):
    return user.is_staff or user.is_superuser

# Helper function to get stats from cache
def get_platform_stats(start_date, end_date=None):
    """Get platform stats from cache"""
    if end_date is None:
        end_date = timezone.now().date()
    
    stats = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.isoformat()
        views = cache.get(f'platform_views_{date_str}', 0)
        unique = cache.get(f'unique_visitors_{date_str}', 0)
        stats.append({
            'date': date_str,
            'views': views,
            'unique': unique
        })
        current_date += timedelta(days=1)
    
    return stats

# Main Report View
@login_required
@user_passes_test(is_admin)
def report_dashboard(request):
    """Main report dashboard with all statistics"""
    
    # Date range filtering
    date_range = request.GET.get('range', '30')
    today = timezone.now().date()
    
    if date_range == 'today':
        start_date = today
    elif date_range == 'week':
        start_date = today - timedelta(days=7)
    elif date_range == 'month':
        start_date = today - timedelta(days=30)
    elif date_range == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    # Platform View Statistics from cache (NO DATABASE!)
    platform_stats_data = get_platform_stats(start_date, today)
    total_views = sum(stat['views'] for stat in platform_stats_data)
    total_unique = sum(stat['unique'] for stat in platform_stats_data)
    days_with_data = len([s for s in platform_stats_data if s['views'] > 0])
    daily_avg_views = total_views / days_with_data if days_with_data > 0 else 0
    
    # Order Statistics
    orders = Orders.objects.filter(order_date__gte=start_date)
    total_orders = orders.count()
    total_revenue = orders.filter(is_paid=True).aggregate(Sum('total_price'))['total_price__sum'] or 0
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    delivered_orders = orders.filter(status='delivered').count()
    
    # Platform Commission (2% fee)
    platform_commission = total_revenue * Decimal('0.02')
    seller_earnings = total_revenue * Decimal('0.98')
    
    # Product Statistics
    total_buildings = Building.objects.count()
    total_vehicles = Vehicleinformation.objects.count()
    total_commodities = Commodity.objects.count()
    total_fashion = FashionItem.objects.count()
    total_products = total_buildings + total_vehicles + total_commodities + total_fashion
    
    # Top Selling Products
    top_products = []
    order_items = orders.values('content_type', 'object_id').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('total_price')
    ).order_by('-total_quantity')[:10]
    
    for item in order_items:
        try:
            ct = ContentType.objects.get(id=item['content_type'])
            model_class = ct.model_class()
            if model_class:
                product = model_class.objects.get(id=item['object_id'])
                top_products.append({
                    'name': str(product)[:50],
                    'type': ct.model,
                    'quantity': item['total_quantity'],
                    'sales': item['total_sales']
                })
        except:
            pass
    
    # User Statistics
    total_users = User.objects.count()
    total_sellers = User.objects.filter(
        Q(building_items__isnull=False) | 
        Q(vehicleinformation_items__isnull=False) | 
        Q(commodity_items__isnull=False) |
        Q(fashion_items__isnull=False)
    ).distinct().count()
    total_customers = total_users - total_sellers
    
    # Payment Statistics
    total_payments = BUSPayment.objects.filter(created_at__gte=start_date).count()
    successful_payments = BUSPayment.objects.filter(is_paid=True, created_at__gte=start_date).count()
    building_payments = BuildingPayment.objects.filter(is_paid=True, created_at__gte=start_date).count()
    
    # Recent Activities
    recent_orders = orders.order_by('-order_date')[:10]
    recent_payments = BUSPayment.objects.filter(created_at__gte=start_date).order_by('-created_at')[:10]
    
    # Sales by category
    sales_by_category = {
        'Buildings': orders.filter(content_type__model='building').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'Vehicles': orders.filter(content_type__model='vehicleinformation').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'Commodities': orders.filter(content_type__model='commodity').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'Fashion': orders.filter(content_type__model='fashionitem').aggregate(Sum('total_price'))['total_price__sum'] or 0,
    }
    
    context = {
        'date_range': date_range,
        'start_date': start_date,
        'end_date': today,
        'total_views': total_views,
        'total_unique_visitors': total_unique,
        'daily_avg_views': round(daily_avg_views, 2),
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'platform_commission': platform_commission,
        'seller_earnings': seller_earnings,
        'total_products': total_products,
        'total_buildings': total_buildings,
        'total_vehicles': total_vehicles,
        'total_commodities': total_commodities,
        'total_fashion': total_fashion,
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_customers': total_customers,
        'total_payments': total_payments,
        'successful_payments': successful_payments,
        'building_payments': building_payments,
        'payment_success_rate': (successful_payments / total_payments * 100) if total_payments > 0 else 0,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'sales_by_category': sales_by_category,
        'views_chart_data': platform_stats_data,
    }
    
    return render(request, 'ANALYSIS/report.html', context)

# PDF Report Generation
@login_required
@user_passes_test(is_admin)
def download_pdf_report(request):
    """Generate and download PDF report"""
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="platform_report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    title = Paragraph("E-Commerce Platform Report", title_style)
    elements.append(title)
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    date_text = Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
    elements.append(date_text)
    elements.append(Spacer(1, 20))
    
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    platform_stats_data = get_platform_stats(start_date, today)
    total_views = sum(stat['views'] for stat in platform_stats_data)
    total_unique = sum(stat['unique'] for stat in platform_stats_data)
    
    orders = Orders.objects.filter(order_date__gte=start_date)
    total_orders = orders.count()
    total_revenue = orders.filter(is_paid=True).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    sales_by_category = {
        'Buildings': orders.filter(content_type__model='building').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'Vehicles': orders.filter(content_type__model='vehicleinformation').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'Commodities': orders.filter(content_type__model='commodity').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'Fashion': orders.filter(content_type__model='fashionitem').aggregate(Sum('total_price'))['total_price__sum'] or 0,
    }
    
    overview_data = [
        ['Metric', 'Value'],
        ['Total Platform Views', f'{total_views:,}'],
        ['Unique Visitors', f'{total_unique:,}'],
        ['Total Orders', f'{total_orders:,}'],
        ['Total Revenue', f'${total_revenue:,.2f}'],
        ['Total Products', f'{Building.objects.count() + Vehicleinformation.objects.count() + Commodity.objects.count() + FashionItem.objects.count():,}'],
        ['Total Users', f'{User.objects.count():,}'],
    ]
    
    overview_table = Table(overview_data, colWidths=[200, 200])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Sales by Category", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    category_data = [['Category', 'Total Sales']]
    category_data.append(['Buildings', f'${sales_by_category["Buildings"]:,.2f}'])
    category_data.append(['Vehicles', f'${sales_by_category["Vehicles"]:,.2f}'])
    category_data.append(['Commodities', f'${sales_by_category["Commodities"]:,.2f}'])
    category_data.append(['Fashion', f'${sales_by_category["Fashion"]:,.2f}'])
    
    category_table = Table(category_data, colWidths=[200, 200])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(category_table)
    
    doc.build(elements)
    return response

# CSV Export View
@login_required
@user_passes_test(is_admin)
def export_orders_csv(request):
    """Export orders to CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'Buyer', 'Product Type', 'Product Name', 
        'Quantity', 'Total Price', 'Status', 'Is Paid', 'Order Date'
    ])
    
    orders = Orders.objects.all().order_by('-order_date')
    
    for order in orders:
        product_name = 'N/A'
        product_type = 'N/A'
        
        if order.product:
            product_name = str(order.product)[:50]
            if order.content_type:
                product_type = order.content_type.model
        
        writer.writerow([
            order.id,
            order.buyer.username,
            product_type,
            product_name,
            order.quantity,
            order.total_price,
            order.status,
            'Yes' if order.is_paid else 'No',
            order.order_date.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

# Platform Stats API
@login_required
@user_passes_test(is_admin)
def platform_stats_api(request):
    """JSON API for platform statistics"""
    
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    stats = get_platform_stats(start_date, timezone.now().date())
    
    data = {
        'labels': [s['date'] for s in stats],
        'views': [s['views'] for s in stats],
        'unique': [s['unique'] for s in stats],
    }
    
    return JsonResponse(data)

# Reset daily view tracking (optional)
@login_required
@user_passes_test(is_admin)
def reset_platform_stats(request):
    """Reset platform statistics (admin only)"""
    if request.method == 'POST':
        # Clear all platform view cache keys
        from django.core.cache import cache
        # This is a simplified version - in production you'd want to be more selective
        cache.clear()
        return JsonResponse({'status': 'success', 'message': 'Platform stats reset successfully'})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)
# BUS_SYSTEM/context_processors.py
def cart_data(request):
    cart = request.session.get('cart', {})
    cart_count = sum(item['quantity'] for item in cart.values()) if cart else 0
    return {'cart_count': cart_count}
def cart_count(request):
    """
    Makes cart information available across all templates for Blinkit-style UI.
    Provides cart_item_count, cart_total, and a dictionary of cart item quantities.
    """
    if request.user.is_authenticated:
        try:
            cart = getattr(request.user, 'cart', None)
            if cart:
                items = list(cart.items.select_related('product').all())
                count = sum(item.quantity for item in items)
                total = sum(item.get_subtotal() for item in items)
                # Map of product_id -> { 'item_id': item.id, 'quantity': item.quantity }
                cart_map = {item.product_id: {'id': item.id, 'qty': item.quantity} for item in items}
                return {
                    'cart_item_count': count,
                    'cart_total': total,
                    'cart_map': cart_map,
                }
        except Exception:
            pass
    return {
        'cart_item_count': 0,
        'cart_total': 0,
        'cart_map': {},
    }

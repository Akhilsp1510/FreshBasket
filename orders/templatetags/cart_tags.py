from django import template

register = template.Library()

@register.filter
def get_item_id(cart_map, product_id):
    """Returns the CartItem id for a given product_id from cart_map."""
    if isinstance(cart_map, dict) and product_id in cart_map:
        return cart_map[product_id].get('id', 0)
    return 0

@register.filter
def get_item_qty(cart_map, product_id):
    """Returns the quantity for a given product_id from cart_map."""
    if isinstance(cart_map, dict) and product_id in cart_map:
        return cart_map[product_id].get('qty', 0)
    return 0

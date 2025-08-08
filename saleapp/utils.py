from flask import session
from saleapp.models import CartItem
def cart_stats(cart):
    total_quantity, total_amount = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['price']

    return {
        "total_amount": total_amount,
        "total_quantity": total_quantity
    }
def sync_cart_to_session(user_id):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    cart = {
        str(item.book_id): {
            "id": item.book_id,
            "name": item.book.name,
            "price": item.book.price_physical,
            "quantity": item.quantity
        } for item in cart_items
    }
    session['cart'] = cart

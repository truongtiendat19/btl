from saleapp.models import Discount
from datetime import datetime

def cart_stats(cart):
    total_quantity = 0
    total_amount = 0
    cart_with_discounts = {}

    if cart:
        now = datetime.now()

        for item in cart.values():
            quantity = item.get('quantity', 1)
            price = item['price']
            total_quantity += quantity

            discount_value = 0
            final_price = price
            discount_type = None

            # Lấy thông tin giảm giá hợp lệ
            discount = Discount.query.filter_by(book_id=int(item['id']), is_active=True).filter(
                Discount.start_date <= now,
                Discount.end_date >= now
            ).first()

            if discount:
                if discount.discount_type == 'percentage':
                    discount_value = price * discount.value / 100
                    final_price = price - discount_value
                    discount_type = 'percentage'
                elif discount.discount_type == 'fixed':
                    discount_value = discount.value
                    final_price = max(0, price - discount_value)
                    discount_type = 'fixed'

            total_amount += quantity * final_price

            cart_with_discounts[item['id']] = {
                'id': item['id'],
                'name': item['name'],
                'price': price,
                'quantity': quantity,
                'type': item.get('type', 'physical'),
                'digital_pricing_id': item.get('digital_pricing_id'),
                'image_url': item.get('image_url', ''),  # để hiển thị ảnh sản phẩm
                'discount_value': round(discount_value),
                'discount_type': discount_type,
                'final_price': round(final_price)
            }

    return {
        'total_quantity': total_quantity,
        'total_amount': round(total_amount),
        'cart': cart_with_discounts
    }

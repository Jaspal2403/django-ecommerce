from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartItem, Product

@receiver(user_logged_in)
def merge_cart_on_login(request, user, **kwargs):

    session_cart = request.session.get('cart', {})

    if not session_cart:
        return

    cart, _ = Cart.objects.get_or_create(user=user)

    for product_id, qty in session_cart.items():
        product = Product.objects.get(id=product_id)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if created:
            item.quantity = qty
        else:
            item.quantity += qty

        item.save()

    # Clear session cart after merge
    request.session['cart'] = {}
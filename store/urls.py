from django.urls import path
from django.http import HttpResponse
from . import views
from .views import CustomLoginView

app_name = "store"

urlpatterns = [

    # Home
    path("", views.home, name="home"),

    # Search
    path("search/", views.search_products, name="search_products"),
    path("search-suggestions/", views.search_suggestions, name="search_suggestions"),

    # Products
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("category/<int:subcategory_id>/", views.subcategory_products, name="subcategory_products"),

    # Wishlist
    path("toggle-wishlist/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("toggle-wishlist-ajax/<int:product_id>/", views.toggle_wishlist_ajax, name="toggle_wishlist_ajax"),

    # Cart
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart_view, name="cart"),
    path("increase/<int:product_id>/", views.increase_quantity, name="increase_quantity"),
    path("decrease/<int:product_id>/", views.decrease_quantity, name="decrease_quantity"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),    

    # Checkout / Orders
    path("checkout/", views.checkout, name="checkout"),
    path("order-success/", views.order_success, name="order_success"),
    path("orders/", views.order_history, name="order_history"),
    path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),

    # Payments
    path("buy-now/<int:product_id>/", views.buy_now, name="buy_now"),
    path("create-order/", views.create_order, name="create_order"),
    path("pay-now/<int:order_id>/", views.pay_now, name="pay_now"),
    path("payment-success-api/", views.payment_success, name="payment_success"),
    path("payment-success/", views.payment_success_page, name="payment_success_page"),
    path('payment-failed/', views.payment_failed, name='payment_failed'),

    # Auth
    path("signup/", views.signup, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", views.user_logout, name="logout"),

    # AJAX
    path("ajax/load-subcategories/", views.load_subcategories, name="ajax_load_subcategories"),

    # Razorpay webhook
    path("razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
]


def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow:", content_type="text/plain")


urlpatterns += [
    path("robots.txt", robots_txt),
]
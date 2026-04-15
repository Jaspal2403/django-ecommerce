from django.contrib import admin
from django.urls import path, include
from . import views
from django.http import HttpResponse
from store.views import CustomLoginView
app_name = 'store'

urlpatterns = [
    path("ajax/load-subcategories/", views.load_subcategories, name="ajax_load_subcategories"),
    path("", views.home, name="home"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("category/<int:subcategory_id>/", views.subcategory_products, name="subcategory_products"),

    path("buy-now/<int:product_id>/", views.buy_now, name="buy_now"),
    path("create-order/", views.create_order, name="create_order"),

    path('payment-success-api/', views.payment_success, name='payment_success'),
    path('payment-success/', views.payment_success_page, name='payment_success_page'),

    path('pay-now/<int:order_id>/', views.pay_now, name='pay_now'),

    path('signup/', views.signup, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),

    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
]

def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow:", content_type="text/plain")

urlpatterns += [
    path("robots.txt", robots_txt),
]
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from store.forms import CustomLoginForm
from store import views
from store.views import CustomLoginView
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('', include(('store.urls', 'store'), namespace='store')),
    #path('', include('store.urls')),
    #path('login/',auth_views.LoginView.as_view(template_name='store/auth.html',authentication_form=CustomLoginForm),name='login'),
    # path('login/', CustomLoginView.as_view(), name='login'),
    #path('signup/', views.signup, name='signup'),
    path('search/', views.search_products, name='search_products'),
    #path('cart/', views.cart, name='cart'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('logout/', views.user_logout, name='logout'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),
    #path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
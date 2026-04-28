from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.conf import settings

import json
import razorpay

from .forms import SignUpForm
from .models import (
    Product,
    Category,
    ParentCategory,
    Wishlist,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Address,
    Payment,
    HeroBanner,
)

# =====================================================
# RAZORPAY CLIENT
# =====================================================

client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
))


# =====================================================
# AUTH
# =====================================================

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("store:home")

        messages.error(request, "Signup failed")

    else:
        form = SignUpForm()

    return render(request, "store/signup.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "store/auth.html"

    def get_success_url(self):
        return self.request.GET.get("next", "/")


def user_logout(request):
    logout(request)
    return redirect("store:login")


# =====================================================
# HOME / PRODUCTS
# =====================================================

def home(request):
    products = Product.objects.all()

    hero_banners = HeroBanner.objects.filter(
        is_active=True
    ).order_by("display_order")

    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)

    return render(request, "store/home.html", {
        "products": products,
        "hero_banners": hero_banners,
        "parent_categories": ParentCategory.objects.all(),
        "wishlist_ids": wishlist_ids,
    })


def search_products(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "all")
    price_range = request.GET.get("price", "")
    sort_by = request.GET.get("sort", "")

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_id != "all":
        products = products.filter(category_id=category_id)

    if price_range == "under_500":
        products = products.filter(price__lt=500)

    elif price_range == "500_2000":
        products = products.filter(price__gte=500, price__lte=2000)

    elif price_range == "above_2000":
        products = products.filter(price__gt=2000)

    if sort_by == "low":
        products = products.order_by("price")

    elif sort_by == "high":
        products = products.order_by("-price")

    else:
        products = products.order_by("-id")

    return render(request, "store/product_list.html", {
        "products": products,
        "query": query,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, "store/product_detail.html", {
        "product": product
    })


@login_required
def subcategory_products(request, subcategory_id):
    subcategory = get_object_or_404(
        Category,
        id=subcategory_id,
        parent__isnull=False
    )

    products = Product.objects.filter(category=subcategory)

    return render(request, "store/subcategory_products.html", {
        "subcategory": subcategory,
        "products": products
    })


# =====================================================
# AJAX
# =====================================================

def load_subcategories(request):
    parent_id = request.GET.get("parent_id")

    subcategories = Category.objects.filter(parent_id=parent_id)

    data = [
        {
            "id": sub.id,
            "name": sub.name
        }
        for sub in subcategories
    ]

    return JsonResponse(data, safe=False)


def search_suggestions(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(
        name__icontains=query
    )[:8]

    data = []

    for product in products:
        image_url = product.image.url if product.image else ""

        data.append({
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "image": image_url
        })

    return JsonResponse(data, safe=False)


# =====================================================
# WISHLIST
# =====================================================

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    item = Wishlist.objects.filter(
        user=request.user,
        product=product
    )

    if item.exists():
        item.delete()
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def toggle_wishlist_ajax(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    item = Wishlist.objects.filter(
        user=request.user,
        product=product
    )

    if item.exists():
        item.delete()
        status = "removed"
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )
        status = "added"

    return JsonResponse({"status": status})


# =====================================================
# CART
# =====================================================

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    quantity = int(request.POST.get("quantity", 1))

    if created:
        item.quantity = quantity
    else:
        item.quantity += quantity

    item.save()

    return redirect("store:cart")


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    items = cart.items.all()

    total = sum(
        item.product.price * item.quantity
        for item in items
    )

    return render(request, "store/cart.html", {
        "items": items,
        "total": total
    })


@login_required
def increase_quantity(request, product_id):
    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(
        cart=cart,
        product_id=product_id
    )

    item.quantity += 1
    item.save()

    return redirect("store:cart")


@login_required
def decrease_quantity(request, product_id):
    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(
        cart=cart,
        product_id=product_id
    )

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect("store:cart")


@login_required
def remove_from_cart(request, product_id):
    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(
        cart=cart,
        product_id=product_id
    )

    item.delete()

    return redirect("store:cart")


# =====================================================
# ORDERS
# =====================================================

@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    items = cart.items.all()

    total = sum(
        item.product.price * item.quantity
        for item in items
    )

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":

        address_id = request.POST.get("address_id")

        if address_id:
            address = Address.objects.get(
                id=address_id,
                user=request.user
            )

        else:
            address = Address.objects.create(
                user=request.user,
                name=request.POST.get("name"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                pincode=request.POST.get("pincode"),
                phone=request.POST.get("phone"),
            )

        order = Order.objects.create(
            user=request.user,
            address=address,
            status="pending"
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        items.delete()

        return redirect("store:order_success")

    return render(request, "store/checkout.html", {
        "items": items,
        "total": total,
        "addresses": addresses
    })


def order_success(request):
    return render(request, "store/order_success.html")


@login_required
def order_history(request):
    status_filter = request.GET.get("status", "all")

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    valid_status = [
        "pending",
        "processing",
        "shipped",
        "delivered",
        "cancelled"
    ]

    if status_filter in valid_status:
        orders = orders.filter(status=status_filter)

    order_data = []

    for order in orders:
        total = sum(
            item.price * item.quantity
            for item in order.items.all()
        )

        order_data.append({
            "order": order,
            "total": total
        })

    return render(request, "store/order_history.html", {
        "order_data": order_data,
        "status_filter": status_filter
    })


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if request.method == "POST":
        if order.status == "pending":
            order.status = "cancelled"
            order.save()

    return redirect("store:order_history")


# =====================================================
# PAYMENT
# =====================================================

@login_required
def buy_now(request, product_id):
    request.session["buy_product_id"] = product_id
    return redirect("store:create_order")


@login_required
def create_order(request):
    try:
        product_id = request.session.get("buy_product_id")

        if not product_id:
            return redirect("store:home")

        product = Product.objects.get(id=product_id)

        amount = int(product.price * 100)

        if amount < 100:
            amount = 100

        address = Address.objects.filter(user=request.user).first()

        if not address:
            return redirect("store:checkout")

        order = Order.objects.create(
            user=request.user,
            address=address,
            total_amount=float(product.price),
            status="pending"
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )

        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"            
        })

        print("RAZORPAY ORDER:", razorpay_order)

        payment = Payment.objects.create(
            razorpay_order_id=razorpay_order["id"],
            amount=amount,
            status="CREATED",
            # product_id=product.id,
            product=product,
            user=request.user
        )

        order.payment = payment
        order.save()

        # ✅ Clear session after use
        del request.session["buy_product_id"]

        return render(request, "store/payment.html", {
            "order_id": razorpay_order["id"],
            "amount": amount,
            "display_amount": amount / 100,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        })

    except Exception as e:
        return HttpResponseBadRequest(str(e))


@login_required
def pay_now(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    total = sum(
        item.price * item.quantity
        for item in order.items.all()
    )

    amount = int(total * 100)

    if amount < 100:
        amount = 100

    razorpay_order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    order_item = order.items.first()
    product_id = order_item.product.id if order_item else None

    payment = Payment.objects.create(
        razorpay_order_id=razorpay_order["id"],
        amount=amount,
        status="CREATED",
        #product_id=product_id,
        product=order_item.product if order_item else None,
        user=request.user
    )

    order.payment = payment
    order.save()

    return render(request, "store/payment.html", {
        "order_id": razorpay_order["id"],
        "amount": amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


@csrf_exempt
def payment_success(request):

    if request.method != "POST":
        return JsonResponse({"status": "failed"})

    try:
        data = json.loads(request.body)

        params_dict = {
            "razorpay_order_id": data.get("razorpay_order_id"),
            "razorpay_payment_id": data.get("razorpay_payment_id"),
            "razorpay_signature": data.get("razorpay_signature"),
        }

        client.utility.verify_payment_signature(params_dict)

        payment = Payment.objects.get(
            razorpay_order_id=data.get("razorpay_order_id")
        )

        # Prevent duplicate processing
        if payment.status == "SUCCESS":
            return JsonResponse({"status": "success"})

        payment.razorpay_payment_id = data.get("razorpay_payment_id")
        payment.razorpay_signature = data.get("razorpay_signature")
        payment.status = "SUCCESS"
        payment.save()

        order = Order.objects.filter(payment=payment).first()

        if order:
            order.status = "processing"
            order.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        print("PAYMENT ERROR:", repr(e))

    order_id = data.get("razorpay_order_id")

    if order_id:
        try:
            payment = Payment.objects.get(
                razorpay_order_id=order_id
            )
            payment.status = "FAILED"
            payment.save()
        except Payment.DoesNotExist:
            print("Payment record not found for failed update")
        except Exception as update_error:
            print("FAILED status update error:", repr(update_error))

    return JsonResponse({
        "status": "failed",
        "message": str(e)
    })


def payment_success_page(request):
    order_id = request.GET.get("order_id")

    print("SUCCESS PAGE ORDER ID:", order_id)

    payment = Payment.objects.filter(
        razorpay_order_id=order_id
    ).first()

    print("PAYMENT FOUND:", payment)

    if payment:
        payment.amount_in_rupees = payment.amount / 100

    return render(request, "store/payment_success.html", {
        "payment": payment
    })
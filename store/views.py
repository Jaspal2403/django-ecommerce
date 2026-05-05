from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.conf import settings
from decimal import Decimal
from .models import Payment, Order, Coupon, Address

import hmac
import hashlib
import json
import razorpay

import logging
logger=logging.getLogger(__name__)

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
        logger.info("Signup Attempt")       #logs

        form = SignUpForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"Signup success | user_id={user.id}")      #logs
            return redirect("store:home")
        
        logger.warning("Signup failed | invalid form")     #logs

        messages.error(request, "Signup failed")

    else:
        form = SignUpForm()

    return render(request, "store/signup.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "store/login.html"

    def get_success_url(self):
        return self.request.GET.get("next", "/")


def user_logout(request):
    logger.info(f"Logout | user_id={request.user.id}")      #Logs
    logout(request)
    return redirect("store:login")


# =====================================================
# HOME / PRODUCTS
# =====================================================

def home(request):
    logger.debug(f"Home loaded | user={request.user}")      #logs

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

    logger.info(f"Search | query={query} | category={category_id} | price={price_range} | sort={sort_by}")      #logs

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

    logger.debug(f"Product viewed | product_id={product.id} | user={request.user}")     #logs

    return render(request, "store/product_detail.html", {
        "product": product
    })


@login_required
def subcategory_products(request, subcategory_id):
    logger.debug(f"Subcategory view | subcategory_id={subcategory_id} | user={request.user.id}")     #logs

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
    logger.debug(f"Load subcategory | parent_id={parent_id}")        #logs

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
    logger.debug(f"Search suggestions | query={query}")     #logs

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
        logger.info(f"Wishlist removed | user_id={request.user.id} | product_id={product_id}")      #logs
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )
        logger.info(f"Wishlist added | user_id={request.user.id} | product_id={product.id}")        #logs

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

# @login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get("quantity", 1))

    logger.info(f"AddToCart | user_id={request.user.id} | product_id={product.id}")     #logs

    if request.user.is_authenticated:
        # Existing DB logic
        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity

        item.save()

    else:
        # NEW: Session Cart
        cart = request.session.get('cart', {})

        product_id_str = str(product_id)

        if product_id_str in cart:
            cart[product_id_str] += quantity
        else:
            cart[product_id_str] = quantity

        request.session['cart'] = cart

    return redirect("store:cart")


@login_required
def cart_view(request):
    logger.info(f"Cart view | user_if={request.user.id}")       #logs

    items = []

    # ===============================
    # AUTHENTICATED USER (DB CART)
    # ===============================
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        db_items = cart.items.select_related('product')

        for item in db_items:
            product = item.product
            qty = item.quantity

            price = product.price
            mrp = product.mrp if product.mrp else price

            subtotal = price * qty
            mrp_total = mrp * qty
            saving = mrp_total - subtotal

            item.subtotal = subtotal
            item.mrp_total = mrp_total
            item.saving = saving

            items.append(item)

    # ===============================
    # GUEST USER (SESSION CART)
    # ===============================
    else:
        session_cart = request.session.get('cart', {})

        for product_id, qty in session_cart.items():
            product = Product.objects.get(id=product_id)

            price = product.price
            mrp = product.mrp if product.mrp else price

            subtotal = price * qty
            mrp_total = mrp * qty
            saving = mrp_total - subtotal

            # Create lightweight object-like dict
            item = type('obj', (object,), {
                'product': product,
                'quantity': qty,
                'subtotal': subtotal,
                'mrp_total': mrp_total,
                'saving': saving
            })

            items.append(item)

    # ===============================
    # TOTAL CALCULATIONS
    # ===============================
    total_mrp = sum(item.mrp_total for item in items)
    total = sum(item.subtotal for item in items)
    total_savings = total_mrp - total

    # ===============================
    # COUPON LOGIC
    # ===============================
    discount_percent = request.session.get('coupon', 0)

    discount_amount = (total * discount_percent) / 100
    final_total = total - discount_amount

    # ===============================
    # RENDER
    # ===============================
    return render(request, "store/cart.html", {
        "items": items,
        "total": total,
        "total_mrp": total_mrp,
        "total_savings": total_savings,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "discount_percent": discount_percent,
    })

def apply_coupon(request):
    code = request.POST.get("coupon")

    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True)

        logger.info(f"Coupon applied | user_id={request.user.id} | code={code}")        #logs
        
        request.session['coupon'] = coupon.discount_percent
        messages.success(request, "Coupon applied successfully")
    except Coupon.DoesNotExist:

        logger.info(f"Invalid Coupon | user_id={request.user.id} | code={code}")        #logs

        request.session['coupon'] = 0
        messages.error(request, "Invalid coupon")

    return redirect("store:cart")


@login_required
def increase_quantity(request, product_id):
    logger.debug(f"Increase quantity | user_id={request.user.id} | product_id={product_id}")        #logs

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
    logger.info(f"Remove from cart | user_id={request.user.id} | product_id={product_id}")

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
# CHECKOUT PAYMENT
# =====================================================

@login_required
def checkout(request):

    logger.info(f"Checkout started | user_id={request.user.id}")    #logs

    # ===============================
    # CART & ITEMS
    # ===============================
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')

    if not items:
        logger.warning(f"Checkout blocked | empty cart | user_id={request.user.id}")        #logs
        return redirect("store:cart")

    # Add subtotal
    for item in items:
        item.subtotal = item.product.price * item.quantity

    # ===============================
    # PRICE CALCULATION
    # ===============================
    total = sum(item.subtotal for item in items)

    discount_percent = request.session.get('coupon', 0)
    discount_amount = (total * Decimal(discount_percent)) / 100
    final_total = total - discount_amount

    # ===============================
    # USER ADDRESSES
    # ===============================
    addresses = Address.objects.filter(user=request.user)

    # ===============================
    # HANDLE FORM SUBMIT
    # ===============================
    if request.method == "POST":      

        address_id = request.POST.get("address_id")
        
        # ===============================
        # EXISTING ADDRESS (priority)
        # ===============================
        if address_id:
            logger.debug(f"Checkout address selected | address_id={address.id}")        #logs

            address = get_object_or_404(
                Address,
                id=address_id,
                user=request.user
            )
        
        # ===============================
        # NEW ADDRESS (fallback)
        # ===============================
        else:
            name = request.POST.get("name", "").strip()
            address_text = request.POST.get("address", "").strip()
            city = request.POST.get("city", "").strip()
            pincode = request.POST.get("pincode", "").strip()
            phone = request.POST.get("phone", "").strip()

            if not all([name, address_text, city, pincode, phone]):
                messages.error(request, "Please fill all address fields.")
                return redirect("store:checkout")

            address = Address.objects.create(
                user=request.user,
                name=name,
                address=address_text,
                city=city,
                pincode=pincode,
                phone=phone,
            )

        # ===============================
        # CREATE ORDER
        # ===============================
        order = Order.objects.create(
            user=request.user,
            address=address,
            status="pending",
            total_amount=final_total
        )

        logger.info(f"Order created | order_id={order.id} | user_id={request.user.id} | amount={final_total}")      #logs

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
       

        # ===============================
        # CLEAR COUPON
        # ===============================
        request.session['coupon'] = 0

        # ===============================
        # START PAYMENT
        # ===============================
        return start_payment(request, order)

    # ===============================
    # RENDER PAGE
    # ===============================
    return render(request, "store/checkout.html", {
        "items": items,
        "total": total,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "addresses": addresses,
    })


@login_required
def delete_address(request, address_id):
    logger.info(f"Address deleted | user_id={request.user.id} | address_id={address_id}")       #logs

    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        address.delete()
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"})

def order_success(request):
    return render(request, "store/order_success.html")


@login_required
def order_history(request):
    
    status_filter = request.GET.get("status", "all")

    logger.debug(f"Order history viewed | user_id={request.user.id} | filter={status_filter}")      #logs

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

            logger.info(f"Order cancelled | order_id={order.id} | user_id={request.user.id}")       #logs

    return redirect("store:order_history")

# =====================================================
# UNIVERSAL PAYMENT STARTER
# =====================================================

@login_required
def start_payment(request, order):
    logger.info(f"Payment start | order_id={order.id} | user_id={request.user.id}")     #logs

    """
    Reusable Razorpay creator for Buy Now + Checkout
    """

    amount = int(order.total_amount * 100)

    if amount < 100:
        amount = 100

    razorpay_order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    logger.debug(f"Razorpay order created | razorpay_order_id={razorpay_order['id']} | amount={amount}")        #logs

    payment = Payment.objects.create(
        user=request.user,
        product=order.items.first().product if order.items.exists() else None,
        razorpay_order_id=razorpay_order["id"],
        amount=amount,
        status="CREATED"
    )
    
    logger.info(f"Payment record created | payment_id={payment.id}")        #logs

    order.payment = payment
    order.save()

    # return render(request, "store/payment.html", {
    #     "order_id": razorpay_order["id"],
    #     "amount": amount,
    #     "display_amount": amount / 100,
    #     "razorpay_key": settings.RAZORPAY_KEY_ID,
    # })

    return render(request, "store/payment.html", {
    "order_id": razorpay_order["id"],      # Razorpay order id
    "django_order_id": order.id,           # ✅ ADD THIS
    "amount": amount,
    "display_amount": amount / 100,
    "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


# =====================================================
# BUY NOW
# =====================================================

@login_required
def buy_now(request, product_id):
    logger.info(f"BuyNow | user_id={request.user.id} | product_id={product.id}")        #logs

    product = get_object_or_404(Product, id=product_id)

    address = Address.objects.filter(user=request.user).first()

    if not address:
        return redirect("store:checkout")

    order = Order.objects.create(
        user=request.user,
        address=address,
        status="pending",
        total_amount=product.price
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        price=product.price
    )

    return start_payment(request, order)



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

        #print("RAZORPAY ORDER:", razorpay_order)

        logger.debug(f"Razorpay order created | data={razorpay_order}")     #logs
        logger.info(f"Order created (BuyNow flow) | order_id={order.id} | user_id={request.user.id}")       #logs  

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
        logger.error(f"Create order failed | error={str(e)}", exc_info=True)        #logs


@login_required
def pay_now(request, order_id):
    logger.info(f"PayNow triggered | order_id={order.id} | user_id={request.user.id}")      #logs

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

    # return render(request, "store/payment.html", {
    #     "order_id": razorpay_order["id"],
    #     "amount": amount,
    #     "razorpay_key": settings.RAZORPAY_KEY_ID,
    # })

    return render(request, "store/payment.html", {
    "order_id": razorpay_order["id"],
    "django_order_id": order.id,   # ✅ ADD THIS
    "amount": amount,
    "razorpay_key": settings.RAZORPAY_KEY_ID,
    })

@csrf_exempt
def razorpay_webhook(request):
    logger.info("Webhook received")

    # print("🔥 WEBHOOK HIT")

    if request.method != "POST":
        return JsonResponse({"status": "invalid method"})

    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    received_signature = request.headers.get("X-Razorpay-Signature")

    if not received_signature:
        logger.error("Webhook invalid signature")               #logs
        return JsonResponse({"status": "no signature"}, status=400)        

    body = request.body

    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, received_signature):
        print("❌ Invalid signature")
        return JsonResponse({"status": "invalid signature"}, status=400)

    data = json.loads(body)
    event = data.get("event")

    # print("📩 EVENT:", event)
    logger.info(f"Webhook event received | event={event}")          #logs

    # =============================
    # PAYMENT SUCCESS
    # =============================
    if event == "payment.captured":

        payment_entity = data["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        razorpay_payment_id = payment_entity["id"]

        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id
            )

            # 🛑 Idempotency protection
            if payment.status == "SUCCESS":
                return JsonResponse({"status": "already processed"})

            # payment_pending flow
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = "SUCCESS"
            payment.save()

            
            order = Order.objects.filter(payment=payment).first()

            if order:
                order.status = "processing"
                order.save()

                # ✅ Clear cart here (NOT in frontend)
                CartItem.objects.filter(cart__user=order.user).delete()

            # print("✅ Payment confirmed via webhook")
            logger.info(f"Payment success webhook | razorpay_order_id={razorpay_order_id}")     #logs

        except Payment.DoesNotExist:
            # print("❌ Payment not found")
            logger.error(f"Webhook error | payment not found | razorpay_order_id={razorpay_order_id}")      #logs

    # =============================
    # ❌ FAILURE (ADD THIS BLOCK)
    # =============================
    elif event == "payment.failed":

        payment_entity = data["payload"]["payment"]["entity"]

        razorpay_order_id = payment_entity["order_id"]

        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id
            )

            payment.status = "FAILED"
            payment.save()

            order = Order.objects.filter(payment=payment).first()

            if order:
                order.status = "cancelled"
                order.save()

            # print("❌ PAYMENT FAILED UPDATED")
            logger.warning(f"Payment failed webhook | razorpay_order_id={razorpay_order_id}")       #logs

        except Payment.DoesNotExist:
            print("❌ Payment not found for failure")

    return JsonResponse({"status": "ok"})

@csrf_exempt
def payment_success(request):
    logger.info("Payment success API called")       #logs

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
            razorpay_order_id=data["razorpay_order_id"]
        )

        if payment.status == "SUCCESS":
            logger.info(f"Payment verified | razorpay_order_id={data['razorpay_order_id']}")        #logs
            return JsonResponse({"status": "success"})            

        payment.razorpay_payment_id = data["razorpay_payment_id"]
        payment.razorpay_signature = data["razorpay_signature"]
        payment.status = "SUCCESS"
        payment.save()

        order = Order.objects.filter(payment=payment).first()

        if order:
            order.status = "processing"
            order.save()

            # Clear cart after payment success
            CartItem.objects.filter(cart__user=order.user).delete()

        return JsonResponse({"status": "success"})

    except Exception as e:
        logger.error(f"Payment verification failed | error={str(e)}", exc_info=True)        #logs
        return JsonResponse({
            "status": "failed",
            "message": str(e)
        })
        


# def payment_success_page(request):
#     order_id = request.GET.get("order_id")

#     print("SUCCESS PAGE ORDER ID:", order_id)

#     payment = Payment.objects.filter(
#         razorpay_order_id=order_id
#     ).first()

#     print("PAYMENT FOUND:", payment)

#     if payment:
#         payment.amount_in_rupees = payment.amount / 100

#     return render(request, "store/payment_success.html", {
#         "payment": payment
#     })

def payment_success_page(request):
    order_id = request.GET.get("order_id")

    logger.info(f"Payment Success | order_id={order_id}")       #logs

    if not order_id:
        return render(request, "store/payment_failed.html", {
            "message": "Invalid payment request"
        })

    # Try fetching payment
    payment = Payment.objects.filter(
        razorpay_order_id=order_id
    ).first()

    # If payment not found
    if not payment:
        return render(request, "store/payment_failed.html", {
            "message": "Payment record not found"
        })

    # =============================
    # WAIT FOR WEBHOOK (POLLING)
    # =============================
    import time

    max_wait = 5   # seconds
    waited = 0

    while payment.status == "CREATED" and waited < max_wait:
        time.sleep(1)
        waited += 1
        payment.refresh_from_db()

    # =============================
    # FINAL STATE CHECK
    # =============================

    if payment.status == "SUCCESS":
        logger.info(f"Payment confirmed page render | payment_id={payment.id}")     #logs
        payment.amount_in_rupees = payment.amount / 100

        return render(request, "store/payment_success.html", {
            "payment": payment
        })
    
    elif payment.status == "FAILED":

        return render(request, "store/payment_failed.html", {
            "message": "Payment failed. Please try again."
        })

    else:
        # Still not updated → webhook delay
        return render(request, "store/payment_pending.html", {
            "payment": payment
        })
    
def payment_failed(request):
    order_id = request.GET.get('order_id')

    logger.warning(f"Payment failed page | order_id={order_id}")        #logs

    logger.info(f"Payment Failed | order_id={order_id}")    #logs

    return render(request, 'store/payment_failed.html', {
        'order_id': order_id,
        'message': 'Payment failed. Please try again.'
    })
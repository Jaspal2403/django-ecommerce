from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from .forms import SignUpForm
from .models import Product, Category, ParentCategory, Wishlist
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderItem, Address, Payment
from django.http import HttpResponseBadRequest, JsonResponse
import razorpay
from django.conf import settings
from django.contrib import messages

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def signup(request):

    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Signup failed")

    else:
        form = SignUpForm()

    return render(request, 'store/signup.html', {
        'form': form
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def login_redirect(request):

    if request.user.is_staff:
        return redirect('/admin/')
    return redirect('home')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
class CustomLoginView(LoginView):
    template_name = 'store/auth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context['signup_form'] = SignUpForm()
        return context
    
def get_success_url(self):
    return self.request.GET.get('next', '/')


# def get_parent_categories():
#     return ParentCategory.objects.all()

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#@login_required
def home(request):
    #products = Product.objects.all()
    products = Product.objects.all()

    wishlist_ids = []

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)

    return render(request, "store/home.html", {
        "products": products,
        "wishlist_ids": wishlist_ids
    })

# def search_products(request):

#     query = request.GET.get("q")
#     category_id = request.GET.get("category")

#     products = Product.objects.all()

#     if query:
#         products = products.filter(name__icontains=query)

#     if category_id and category_id != "all":
#         products = products.filter(category_id=category_id)

#     return render(request, "store/product_list.html", {
#         "products": products
#     })

from django.db.models import Q

from django.db.models import Q

def search_products(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "all")
    price_range = request.GET.get("price", "")
    sort_by = request.GET.get("sort", "")

    products = Product.objects.all()

    # Search
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Category
    if category_id != "all":
        products = products.filter(category_id=category_id)

    # Price
    if price_range == "under_500":
        products = products.filter(price__lt=500)

    elif price_range == "500_2000":
        products = products.filter(price__gte=500, price__lte=2000)

    elif price_range == "above_2000":
        products = products.filter(price__gt=2000)

    # Sort
    if sort_by == "low":
        products = products.order_by("price")

    elif sort_by == "high":
        products = products.order_by("-price")

    elif sort_by == "new":
        products = products.order_by("-id")

    categories = Category.objects.filter(parent__isnull=False)

    # Suggestions if no results
    suggestions = Product.objects.all()[:6]

    return render(request, "store/product_list.html", {
        "products": products,
        "query": query,
        "categories": categories,
        "suggestions": suggestions,
    })

# def search_products(request):
#     query = request.GET.get("q", "").strip()
#     category_id = request.GET.get("category", "all")

#     products = Product.objects.all()

#     # Search text
#     if query:
#         products = products.filter(
#             Q(name__icontains=query) |
#             Q(description__icontains=query) |
#             Q(category__name__icontains=query)
#         )

#     # Category filter
#     if category_id != "all":

#         # If selected category is parent, include children
#         child_categories = Category.objects.filter(parent_id=category_id)

#         if child_categories.exists():
#             products = products.filter(category__in=child_categories)
#         else:
#             products = products.filter(category_id=category_id)

#     return render(request, "store/product_list.html", {
#         "products": products,
#         "query": query,
#     })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, "store/product_detail.html", {
        "product": product
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def subcategory_products(request, subcategory_id):
    subcategory = get_object_or_404(Category, id=subcategory_id, parent__isnull=False)
    products = Product.objects.filter(category=subcategory)

    return render(request, "store/subcategory_products.html", {
        "subcategory": subcategory,
        "products": products,
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def user_logout(request):
    logout(request)
    return redirect('login')


#AJAX
from django.http import JsonResponse
from .models import Category

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def load_subcategories(request):
    parent_id = request.GET.get('parent_id')
    subcategories = Category.objects.filter(parent_id=parent_id)
    data = [
        {"id": sub.id, "name": sub.name}
        for sub in subcategories
    ]
    return JsonResponse(data, safe=False)

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#Add to cart
@login_required
def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    quantity = int(request.POST.get('quantity', 1))

    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity

    item.save()

    return redirect('cart')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#cart view
@login_required
def cart_view(request):

    cart, created = Cart.objects.get_or_create(user=request.user)

    items = cart.items.all()

    total = sum(item.product.price * item.quantity for item in items)

    return render(request, 'store/cart.html', {
        'items': items,
        'total': total
    })

# ➕ Increase quantity

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def increase_quantity(request, product_id):

    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(cart=cart, product_id=product_id)

    item.quantity += 1
    item.save()

    return redirect('cart')


# ➖ Decrease quantity

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def decrease_quantity(request, product_id):

    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(cart=cart, product_id=product_id)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()   # remove if quantity becomes 0

    return redirect('cart')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
# ❌ Remove item
@login_required
def remove_from_cart(request, product_id):

    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(cart=cart, product_id=product_id)

    item.delete()

    return redirect('cart')


#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def checkout(request):

    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()

    total = sum(item.product.price * item.quantity for item in items)

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":

        address_id = request.POST.get("address_id")

        # 👉 If user selects existing address
        if address_id:
            address = Address.objects.get(id=address_id)

        else:
            # 👉 Create new address
            address = Address.objects.create(
                user=request.user,
                name=request.POST.get("name"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                pincode=request.POST.get("pincode"),
                phone=request.POST.get("phone"),
            )

        # ✅ IMPORTANT: AFTER ADDRESS → GO BACK TO PAYMENT FLOW
        product_id = request.session.get('buy_product_id')

        if product_id:
            #return redirect('pay')   # ⚠️ see note below
            return redirect('create_order')   # ✅ redirect to create_order which will handle both Buy Now and Cart checkout flows
            
        return redirect('home')  
      
        # ✅ After saving address → go back to Buy Now flow
        # return redirect(request.GET.get('next', 'home'))

        order = Order.objects.create(
            user=request.user,
            address=address
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        items.delete()

        return redirect('order_success')

    return render(request, "store/checkout.html", {
        "items": items,
        "total": total,
        "addresses": addresses
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def order_success(request):
    return render(request, "store/order_success.html")

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def order_history(request):

    status_filter = request.GET.get('status', 'all')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    valid_status = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

    if status_filter != 'all' and status_filter in valid_status:
        orders = orders.filter(status=status_filter)

    # ✅ ADD TOTAL CALCULATION
    order_data = []
    for order in orders:
        total = sum(item.price * item.quantity for item in order.items.all())
        order_data.append({
            'order': order,
            'total': total
        })

    return render(request, 'store/order_history.html', {
        'order_data': order_data,
        'status_filter': status_filter
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def cancel_order(request, order_id):

    from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from .forms import SignUpForm
from .models import Product, Category, ParentCategory
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderItem, Address

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def get_parent_categories():
    return ParentCategory.objects.all()

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#@login_required
def home(request):
    #parent_categories = ParentCategory.objects.all()
    #parent_categories = Category.objects.filter(parent__isnull=True)
    #subcategories = Category.objects.filter(parent__isnull=False)
    products = Product.objects.all()

    return render(request, "store/home.html", {
        #"parent_categories": parent_categories,
        "products": products
        #"subcategories": subcategories
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
# def search_products(request):

#     query = request.GET.get("q")
#     category_id = request.GET.get("category")

#     products = Product.objects.all()

#     if query:
#         products = products.filter(name__icontains=query)

#     if category_id and category_id != "all":
#         products = products.filter(category_id=category_id)

#     return render(request, "store/product_list.html", {
#         "products": products
#     })


#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, "store/product_detail.html", {
        "product": product
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def subcategory_products(request, subcategory_id):
    subcategory = get_object_or_404(Category, id=subcategory_id, parent__isnull=False)
    products = Product.objects.filter(category=subcategory)

    return render(request, "store/subcategory_products.html", {
        "subcategory": subcategory,
        "products": products,
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def user_logout(request):
    logout(request)
    return redirect('store:login')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#AJAX
from django.http import JsonResponse
from .models import Category

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def load_subcategories(request):
    parent_id = request.GET.get('parent_id')
    subcategories = Category.objects.filter(parent_id=parent_id)
    data = [
        {"id": sub.id, "name": sub.name}
        for sub in subcategories
    ]
    return JsonResponse(data, safe=False)

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#Add to cart
@login_required
def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    quantity = int(request.POST.get('quantity', 1))

    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity

    item.save()

    return redirect('cart')


#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
#cart view
@login_required
def cart_view(request):

    cart, created = Cart.objects.get_or_create(user=request.user)

    items = cart.items.all()

    total = sum(item.product.price * item.quantity for item in items)

    return render(request, 'store/cart.html', {
        'items': items,
        'total': total
    })

# ➕ Increase quantity

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def increase_quantity(request, product_id):

    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(cart=cart, product_id=product_id)

    item.quantity += 1
    item.save()

    return redirect('cart')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
# ➖ Decrease quantity
@login_required
def decrease_quantity(request, product_id):

    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(cart=cart, product_id=product_id)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()   # remove if quantity becomes 0

    return redirect('cart')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
# ❌ Remove item
@login_required
def remove_from_cart(request, product_id):

    cart = Cart.objects.get(user=request.user)

    item = CartItem.objects.get(cart=cart, product_id=product_id)

    item.delete()

    return redirect('cart')

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def checkout(request):

    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()

    total = sum(item.product.price * item.quantity for item in items)

    addresses = Address.objects.filter(user=request.user)

    if request.method == "POST":

        address_id = request.POST.get("address_id")

        # 👉 If user selects existing address
        if address_id:
            address = Address.objects.get(id=address_id)

        else:
            # 👉 Create new address
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
            address=address
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        items.delete()

        return redirect('order_success')

    return render(request, "store/checkout.html", {
        "items": items,
        "total": total,
        "addresses": addresses
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def order_success(request):
    return render(request, "store/order_success.html")

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def order_history(request):

    status_filter = request.GET.get('status', 'all')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    valid_status = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

    if status_filter != 'all' and status_filter in valid_status:
        orders = orders.filter(status=status_filter)

    # ✅ ADD TOTAL CALCULATION
    order_data = []
    for order in orders:
        total = sum(item.price * item.quantity for item in order.items.all())
        order_data.append({
            'order': order,
            'total': total
        })

    return render(request, 'store/order_history.html', {
        'order_data': order_data,
        'status_filter': status_filter
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def cancel_order(request, order_id):

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()

    return redirect('order_history')


client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID, 
    settings.RAZORPAY_KEY_SECRET
    ))

from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest
from django.conf import settings

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def create_order(request):

    try:
        # ✅ Get product from session
        product_id = request.session.get('buy_product_id')
        print("PRODUCT ID FROM SESSION:", product_id)

        if not product_id:
            return redirect('home')

        # ✅ Get product
        product = Product.objects.get(id=product_id)

        # ✅ Convert amount for Razorpay (₹ → paise)
        amount = int(product.price * 100)

        # ✅ Check address
        address = Address.objects.filter(user=request.user).first()

        if not address:
            # 🔥 Redirect to checkout to add address
            return redirect(f'/checkout/?next=/create-order/')

        # ✅ Create Order
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_amount=float(product.price),
            status="pending"
        )

        # ✅ Create Order Item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )

        # ✅ Create Razorpay Order
        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        # ✅ Create Payment Entry
        payment = Payment.objects.create(
            razorpay_order_id=razorpay_order['id'],
            amount=amount,
            status="CREATED",
            product_id=product.id,
            user=request.user if request.user.is_authenticated else None
        )

        # ✅ Link Payment to Order
        order.payment = payment
        order.save()

        # ✅ Render Payment Page
        return render(request, "store/payment.html", {
            "order_id": razorpay_order['id'],
            "amount": amount,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        })

    except Product.DoesNotExist:
        return HttpResponseBadRequest("Invalid product")

    except Exception as e:
        print("ERROR:", str(e))
        return HttpResponseBadRequest(str(e))
    

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        data = json.loads(request.body)

        print("DATA RECEIVED:", data)
        print("ORDER ID:", data.get('razorpay_order_id'))
        print("PAYMENT ID:", data.get('razorpay_payment_id'))
        print("SIGNATURE:", data.get('razorpay_signature'))

        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            payment = Payment.objects.get(
                razorpay_order_id=data.get('razorpay_order_id')
            )

            payment.razorpay_order_id = data.get('razorpay_order_id')
            payment.razorpay_payment_id = data.get('razorpay_payment_id')
            payment.razorpay_signature = data.get('razorpay_signature')
            payment.status = "SUCCESS"
            payment.save()

            # ✅ UPDATE ORDER
            order = Order.objects.filter(payment=payment).first()
            if order:
                order.status = "processing"
                order.save()

            return JsonResponse({"status": "success"})

        except Exception as e:
            print("SIGNATURE ERROR:", str(e))
            return JsonResponse({"status": "failed"})
        
#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def payment_success_page(request):
    order_id = request.GET.get("order_id")

    payment = Payment.objects.filter(
        razorpay_order_id=order_id
    ).first()

    if payment:
        payment.amount_in_rupees = payment.amount / 100

    return render(request, "store/payment_success.html", {
        "payment": payment
    })

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
@login_required
def pay_now(request, order_id):

    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        # ✅ Calculate from order items (correct way)
        total = sum(item.price * item.quantity for item in order.items.all())
        amount = int(total * 100)

        if amount < 100:
            amount = 100  # Razorpay minimum amount is 100 paise (₹1)

        print("Order Total:", total)
        print("Final Amount:", amount)


        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        # ✅ Get product from order
        order_item = order.items.first()

        product_id = order_item.product.id if order_item else None

        # ✅ Update or create payment
        payment = Payment.objects.create(
            razorpay_order_id=razorpay_order['id'],
            amount=amount,
            status="CREATED",
            product_id=product_id,
            user=request.user
        )

        # ✅ Link to order
        order.payment = payment
        order.save()

        return render(request, "store/payment.html", {
            "order_id": razorpay_order['id'],
            "amount": amount,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        })

    except Exception as e:
        return HttpResponseBadRequest(str(e))

#STABLE MODULE - DO NOT EDIT UNLESS NECESSARY
def buy_now(request, product_id):

    # ✅ If not logged in → redirect to login
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/buy-now/{product_id}/')

    # ✅ Store product in session
    request.session['buy_product_id'] = product_id

    # ✅ Redirect to create_order
    return redirect('store:create_order')

def search_suggestions(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(
        name__icontains=query
    )[:8]

    data = []

    for product in products:

        image_url = ""

        if product.image:
            image_url = product.image.url

        data.append({
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "image": image_url
        })

    return JsonResponse(data, safe=False)

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

    return redirect(request.META.get('HTTP_REFERER', '/'))


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

    return JsonResponse({
        "status": status
    })
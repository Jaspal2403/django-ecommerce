from .models import Category, ParentCategory

def categories_processor(request):
    parent_categories = Category.objects.filter(parent__isnull=True)
    return {
        'parent_categories': parent_categories
    }

def parent_categories(request):    
    return {
        'parent_categories': ParentCategory.objects.all()
        
    }

# Cart count context processor
def cart_count(request):
    count = 0

    if request.user.is_authenticated:
        from .models import CartItem
        count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        cart = request.session.get('cart', {})
        count = sum(cart.values())

    return {'cart_count': count}
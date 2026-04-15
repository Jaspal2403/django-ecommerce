from .models import Category

def categories_processor(request):
    parent_categories = Category.objects.filter(parent__isnull=True)
    return {
        'parent_categories': parent_categories
    }
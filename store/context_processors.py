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
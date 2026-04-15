# Register your models here.

from django.contrib import admin
from .models import (Category, ParentCategory, SubCategory, Product, ProductImage, Order)

# admin.site.register(Category)
# admin.site.register(Product)


@admin.register(ParentCategory)
class ParentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

    # IMPORTANT: hide parent field
    fields = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=True)

    def save_model(self, request, obj, form, change):
        obj.parent = None  # enforce parent = NULL
        super().save_model(request, obj, form, change)

#@admin.register(Category)
#class CategoryAdmin(admin.ModelAdmin):
 #   list_display = ('name', 'parent')
  #  list_filter = ('parent',)
   # search_fields = ('name',)

@admin.register(SubCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)
    fields = ('parent', 'name')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=False)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            # ONLY Parent Categories (parent IS NULL)
            kwargs["queryset"] = Category.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

from .forms import ProductAdminForm

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 10

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'category', 'price', 'image')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [ProductImageInline]

  

    # 🔑 THIS CONTROLS FORM ORDER
    fields = (
        'parent_category',  # custom field FIRST
        'category',
        'name',
        'price',
        'description',
        'image',
    )

    class Media:
        js = ('store/js/product_category_filter.js',)


#@admin.register(SubCategory)
#class CategoryAdmin(admin.ModelAdmin):
 #   list_display = ('name', 'parent')
  #  list_filter = ('parent',)
   # search_fields = ('name',)

    #def get_queryset(self, request):
     #   return super().get_queryset(request).filter(parent__isnull=False)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at')
    list_filter = ('status',)
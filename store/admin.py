from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Address, Cart, CartItem, OrderItem
import csv

from .models import (
    Category,
    ParentCategory,
    SubCategory,
    Product,
    ProductImage,
    Order,
    Payment,
    Wishlist
)


# =========================
# CATEGORY ADMIN
# =========================
@admin.register(ParentCategory)
class ParentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    list_filter = ("parent",)
    search_fields = ("name",)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "city", "pincode", "phone")
    search_fields = ("name", "city", "phone", "user__username")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
    search_fields = ("order__id", "product__name")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__username",)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")
    search_fields = ("product__name", "cart__user__username")

# =========================
# PRODUCT IMAGE INLINE
# =========================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2


# =========================
# PRODUCT ACTIONS
# =========================
@admin.action(description="Mark selected as Featured")
def make_featured(modeladmin, request, queryset):
    queryset.update(is_featured=True)


@admin.action(description="Remove Featured")
def remove_featured(modeladmin, request, queryset):
    queryset.update(is_featured=False)


# =========================
# PRODUCT ADMIN
# =========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "thumbnail",
        "name",
        "category",
        "price",
        "is_featured",
    )

    list_filter = (
        "category",
        "is_featured",
    )

    search_fields = (
        "name",
        "description",
    )

    actions = [
        make_featured,
        remove_featured,
    ]

    inlines = [ProductImageInline]

    fieldsets = (

        ("Basic Details", {
            "fields": (
                "category",
                "name",
                "price",
                "description",
            )
        }),

        ("Images", {
            "fields": (
                "image",
            )
        }),

        ("Hero Banner", {
            "fields": (
                "is_featured",
                "banner_title",
                "banner_subtitle",
            )
        }),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="55" height="55" style="object-fit:cover;border-radius:6px;" />',
                obj.image.url
            )
        return "-"
    thumbnail.short_description = "Image"


# =========================
# ORDER ACTIONS
# =========================
@admin.action(description="Mark selected as Processing")
def mark_processing(modeladmin, request, queryset):
    queryset.update(status="processing")


@admin.action(description="Mark selected as Shipped")
def mark_shipped(modeladmin, request, queryset):
    queryset.update(status="shipped")


@admin.action(description="Mark selected as Delivered")
def mark_delivered(modeladmin, request, queryset):
    queryset.update(status="delivered")


@admin.action(description="Cancel selected orders")
def mark_cancelled(modeladmin, request, queryset):
    queryset.update(status="cancelled")


@admin.action(description="Export selected orders to CSV")
def export_orders_csv(modeladmin, request, queryset):

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=orders.csv"

    writer = csv.writer(response)

    writer.writerow([
        "Order ID",
        "User",
        "Status",
        "Amount",
        "Created"
    ])

    for order in queryset:
        writer.writerow([
            order.id,
            order.user.username,
            order.status,
            order.total_amount,
            order.created_at
        ])

    return response


# =========================
# ORDER ADMIN
# =========================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "status",
        "total_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "id",
        "user__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    actions = [
        mark_processing,
        mark_shipped,
        mark_delivered,
        mark_cancelled,
        export_orders_csv,
    ]


# =========================
# PAYMENT ADMIN
# =========================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "status",
        "amount",
        "created_at",
    )

    list_filter = (
        "status",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# =========================
# WISHLIST ADMIN
# =========================
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "product",
        "created_at",
    )

    search_fields = (
        "user__username",
        "product__name",
    )
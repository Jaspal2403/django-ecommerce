# from django.db import models

# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError
from PIL import Image
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class ParentCategory(Category):
    class Meta:
        proxy = True
        verbose_name = "Parent Category"
        verbose_name_plural = "Parent Categories"

class SubCategory(Category):
   class Meta:
        proxy = True
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Product(models.Model):

    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    image = models.ImageField(upload_to='products/', null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image and hasattr(self.image, 'path'):
            try:
                img = Image.open(self.image.path)

                # 🔧 Resize (recommended size)
                max_size = (500, 500)
                img.thumbnail(max_size)

                # 🔧 Compress & save
                img.save(self.image.path, optimize=True, quality=85)
            except Exception:
                pass  # Handle exceptions (e.g., file not found, invalid image) as needed

    def __str__(self):
        return self.name
    

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return f"Image for {self.product.name}"
    
    
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart - {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product') # Ensure one entry per product in cart

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"    
    
class Address(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)

    def clean(self):
        # ✅ Phone validation
        if not self.phone.isdigit():
            raise ValidationError("Phone number must contain only digits")

        if len(self.phone) != 10:
            raise ValidationError("Phone number must be 10 digits")

        # ✅ Pincode validation (India)
        if not self.pincode.isdigit():
            raise ValidationError("Pincode must contain only digits")

        if len(self.pincode) != 6:
            raise ValidationError("Pincode must be 6 digits")

    def __str__(self):
        return f"{self.name} - {self.city}"

# ---------------- ORDER ---------------- #

class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

    # ✅ FIXED (add related_name to avoid conflicts)
    payment = models.OneToOneField(
        'Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.status})"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) in Order #{self.order.id}"

class Payment(models.Model):

    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    # Payment details
    amount = models.PositiveIntegerField()  # in paise
    currency = models.CharField(max_length=10, default="INR")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')

    # Relations (optional but recommended)
    #product_id = models.IntegerField(null=True, blank=True)
    #user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #def __str__(self):
        #return f"{self.razorpay_order_id} - {self.status}"
    
    def __str__(self):
        return f"Payment {self.id} | {self.status} | ₹{self.amount/100}"
   
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"



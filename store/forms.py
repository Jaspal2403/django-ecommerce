from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Category


# =========================
# 🔐 SIGNUP FORM
# =========================
class SignUpForm(UserCreationForm):

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        })
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    # ✅ Email uniqueness validation
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")
        return email

    # ✅ Save override (important)
    def save(self, commit=True):
        user = super().save(commit=False)

        # 🔥 Recommended: use email as username
        user.username = self.cleaned_data['username']

        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


# =========================
# 🔑 LOGIN FORM
# =========================
class CustomLoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email or username'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )


# =========================
# 🛒 PRODUCT ADMIN FORM
# =========================
class ProductAdminForm(forms.ModelForm):

    parent_category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=True),
        required=True,
        label="Parent Category"
    )

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially empty subcategory
        self.fields['category'].queryset = Category.objects.none()

        # When user selects parent category
        if 'parent_category' in self.data:
            try:
                parent_id = int(self.data.get('parent_category'))
                self.fields['category'].queryset = Category.objects.filter(parent_id=parent_id)
            except (ValueError, TypeError):
                pass

        # When editing existing product
        elif self.instance.pk and self.instance.category:
            self.fields['parent_category'].initial = self.instance.category.parent
            self.fields['category'].queryset = Category.objects.filter(
                parent=self.instance.category.parent
            )
from django import forms
from products.models import Product, Category


class ProductForm(forms.ModelForm):
    initial_stock = forms.IntegerField(
        min_value=0, required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        help_text='Only used when adding a new product. Leave 0 to set stock later via Inventory.'
    )

    class Meta:
        model = Product
        fields = (
            'category', 'name', 'description', 'brand', 'image',
            'price', 'unit', 'unit_quantity', 'low_stock_threshold',
            'is_active', 'is_featured'
        )
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'unit_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'image', 'icon', 'is_active', 'sort_order')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fresh Fruits'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Aisle description...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-apple', 'id': 'categoryIconInput'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '0'}),
        }


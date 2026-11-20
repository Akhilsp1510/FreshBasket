from django.contrib import admin
from .models import Category, Product, SubstituteGroup, SubstituteGroupItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'sort_order', 'get_product_count')
    list_editable = ('is_active', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active', 'is_featured', 'low_stock_threshold')
    list_filter = ('category', 'is_active', 'is_featured')
    list_editable = ('is_active', 'is_featured')
    search_fields = ('name', 'brand', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SubstituteGroup)
class SubstituteGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)

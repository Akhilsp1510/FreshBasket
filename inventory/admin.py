from django.contrib import admin
from .models import Inventory, StockReservation, InventoryLog, StockAlert


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'physical_stock', 'reserved_stock', 'available_stock', 'stock_status', 'updated_at')
    list_filter = ('stock_status',)
    search_fields = ('product__name',)
    readonly_fields = ('available_stock', 'stock_status', 'updated_at')


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'status', 'expires_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'quantity_changed', 'performed_by', 'timestamp')
    list_filter = ('change_type',)
    search_fields = ('product__name', 'performed_by__username')
    readonly_fields = ('timestamp',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('product', 'alert_type', 'stock_level_at_alert', 'is_acknowledged', 'created_at')
    list_filter = ('alert_type', 'is_acknowledged')
    search_fields = ('product__name',)

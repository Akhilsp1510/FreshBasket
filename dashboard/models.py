from django.db import models
from django.conf import settings


# The dashboard app is primarily view-based (no domain models of its own).
# It aggregates data from accounts, products, inventory, and orders apps.
# Any dashboard-specific persistence lives here.


class DashboardWidget(models.Model):
    """
    Persists per-user widget visibility/order preferences for the admin dashboard.
    """
    WIDGET_SALES_SUMMARY = 'sales_summary'
    WIDGET_LOW_STOCK = 'low_stock'
    WIDGET_RECENT_ORDERS = 'recent_orders'
    WIDGET_REVENUE_CHART = 'revenue_chart'
    WIDGET_TOP_PRODUCTS = 'top_products'
    WIDGET_CHOICES = [
        (WIDGET_SALES_SUMMARY, 'Sales Summary'),
        (WIDGET_LOW_STOCK, 'Low Stock Alerts'),
        (WIDGET_RECENT_ORDERS, 'Recent Orders'),
        (WIDGET_REVENUE_CHART, 'Revenue Chart'),
        (WIDGET_TOP_PRODUCTS, 'Top Products'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets'
    )
    widget_type = models.CharField(max_length=50, choices=WIDGET_CHOICES)
    is_visible = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'dashboard_widget'
        unique_together = ('user', 'widget_type')
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.user.username} - {self.widget_type} ({'visible' if self.is_visible else 'hidden'})"

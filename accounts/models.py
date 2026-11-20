from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model with phone and role."""
    ROLE_CUSTOMER = 'customer'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_ADMIN, 'Administrator'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_user_extended'

    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_staff

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"


class Address(models.Model):
    """Delivery addresses for customers."""
    ADDRESS_TYPE_HOME = 'home'
    ADDRESS_TYPE_WORK = 'work'
    ADDRESS_TYPE_OTHER = 'other'
    ADDRESS_TYPE_CHOICES = [
        (ADDRESS_TYPE_HOME, 'Home'),
        (ADDRESS_TYPE_WORK, 'Work'),
        (ADDRESS_TYPE_OTHER, 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, choices=ADDRESS_TYPE_CHOICES, default=ADDRESS_TYPE_HOME)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_address'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.full_name} - {self.address_line1}, {self.city}"

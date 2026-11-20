"""
Management command: create_demo_users
Creates demo accounts for college evaluation:
1. Administrator: admin / AdminPassword123!
2. Customer 1: customer / CustomerPassword123!
3. Customer 2: customer2 / CustomerPassword123! (for concurrent reservation test)

Usage:
  python manage.py create_demo_users
"""
from django.core.management.base import BaseCommand
from accounts.models import User, Address


class Command(BaseCommand):
    help = 'Creates default admin and customer demo accounts for testing and demonstration.'

    def handle(self, *args, **options):
        # 1. Administrator
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@freshbasket.in',
                'first_name': 'FreshBasket',
                'last_name': 'Admin',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('AdminPassword123!')
        admin_user.role = User.ROLE_ADMIN
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        if created:
            self.stdout.write(self.style.SUCCESS('  Created Administrator: admin / AdminPassword123!'))
        else:
            self.stdout.write('  Updated Administrator: admin / AdminPassword123!')

        # 2. Customer 1
        cust1, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@freshbasket.in',
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'role': User.ROLE_CUSTOMER,
                'phone': '9876543210',
            }
        )
        cust1.set_password('CustomerPassword123!')
        cust1.role = User.ROLE_CUSTOMER
        cust1.save()

        # Add default address for Rahul
        Address.objects.get_or_create(
            user=cust1,
            label=Address.ADDRESS_TYPE_HOME,
            defaults={
                'full_name': 'Rahul Sharma',
                'phone': '9876543210',
                'address_line1': 'Flat 402, Green Valley Apartments',
                'address_line2': 'Indiranagar 100ft Road',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560038',
                'is_default': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  Created Customer 1: customer / CustomerPassword123!'))
        else:
            self.stdout.write('  Updated Customer 1: customer / CustomerPassword123!')

        # 3. Customer 2 (for concurrency testing)
        cust2, created = User.objects.get_or_create(
            username='customer2',
            defaults={
                'email': 'customer2@freshbasket.in',
                'first_name': 'Priya',
                'last_name': 'Verma',
                'role': User.ROLE_CUSTOMER,
                'phone': '9123456789',
            }
        )
        cust2.set_password('CustomerPassword123!')
        cust2.role = User.ROLE_CUSTOMER
        cust2.save()

        Address.objects.get_or_create(
            user=cust2,
            label=Address.ADDRESS_TYPE_HOME,
            defaults={
                'full_name': 'Priya Verma',
                'phone': '9123456789',
                'address_line1': 'House 14, 5th Cross, Koramangala',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560034',
                'is_default': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  Created Customer 2: customer2 / CustomerPassword123!'))
        else:
            self.stdout.write('  Updated Customer 2: customer2 / CustomerPassword123!')

        self.stdout.write(self.style.SUCCESS('\nDemo accounts ready!'))


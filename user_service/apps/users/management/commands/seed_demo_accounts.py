from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import Role, User, UserAddress
from apps.users.services import hash_password


ACCOUNTS = [
    {
        'role': 'admin',
        'username': 'admin_demo',
        'email': 'admin.demo@example.com',
        'password': 'Admin@123456',
        'first_name': 'Admin',
        'last_name': 'Demo',
        'phone_number': '0901000001',
        'is_verified': True,
    },
    {
        'role': 'customer',
        'username': 'customer_demo',
        'email': 'customer.demo@example.com',
        'password': 'Customer@123456',
        'first_name': 'Customer',
        'last_name': 'Demo',
        'phone_number': '0901000002',
        'is_verified': True,
    },
    {
        'role': 'customer',
        'username': 'linh_buyer',
        'email': 'linh.buyer@example.com',
        'password': 'Linh@123456',
        'first_name': 'Linh',
        'last_name': 'Nguyen',
        'phone_number': '0901000003',
        'is_verified': True,
    },
]


class Command(BaseCommand):
    help = 'Seed demo roles, accounts, and default shipping addresses.'

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {}
        for name, description in {
            'admin': 'Administrator account for testing admin-only endpoints',
            'customer': 'Customer account for storefront testing',
        }.items():
            role, _ = Role.objects.update_or_create(name=name, defaults={'description': description})
            roles[name] = role

        created = 0
        updated = 0
        for account in ACCOUNTS:
            password = account['password']
            user, was_created = User.objects.update_or_create(
                username=account['username'],
                defaults={
                    'email': account['email'],
                    'password_hash': hash_password(password),
                    'first_name': account['first_name'],
                    'last_name': account['last_name'],
                    'phone_number': account['phone_number'],
                    'role': roles[account['role']],
                    'is_active': True,
                    'is_verified': account['is_verified'],
                },
            )
            created += int(was_created)
            updated += int(not was_created)

            UserAddress.objects.update_or_create(
                user=user,
                recipient_name=f'{user.first_name} {user.last_name}',
                defaults={
                    'phone_number': user.phone_number,
                    'address_line1': '01 Demo Street',
                    'address_line2': 'Test Apartment',
                    'district': 'District 1',
                    'city': 'Ho Chi Minh City',
                    'province': 'Ho Chi Minh',
                    'postal_code': '700000',
                    'is_default': True,
                },
            )

        self.stdout.write(self.style.SUCCESS(f'Seeded demo accounts: {created} created, {updated} updated.'))

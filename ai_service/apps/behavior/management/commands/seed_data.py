"""
Seed realistic e-commerce product + user behaviour data.
Run: python manage.py seed_data
"""
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.behavior.models import Product, UserBehavior
from ml.datasets.base import PRODUCTS as CSV_PRODUCTS

FALLBACK_PRODUCTS = CSV_PRODUCTS

ACTIONS = ['view', 'click', 'add_to_cart', 'purchase']
ACTION_WEIGHT = {'view': 1.0, 'click': 2.0, 'add_to_cart': 3.0, 'purchase': 4.0}


def _action_seq():
    """Generate a realistic funnel sequence: many views, fewer clicks, even fewer carts/purchases."""
    seq = []
    seq += ['view'] * random.randint(2, 5)
    if random.random() > 0.3:
        seq += ['click'] * random.randint(1, 3)
    if random.random() > 0.5:
        seq.append('add_to_cart')
    if random.random() > 0.7:
        seq.append('purchase')
    return seq


class Command(BaseCommand):
    help = 'Seed AI service with product catalogue and user behaviour data.'

    def add_arguments(self, parser):
        parser.add_argument('--users',    type=int, default=50)
        parser.add_argument('--sessions', type=int, default=5,
                            help='Shopping sessions per user')
        parser.add_argument('--clear',    action='store_true',
                            help='Drop existing data before seeding')
        parser.add_argument('--product-url', default=None,
                            help='Product service base URL, default: settings.PRODUCT_SERVICE_URL')

    def handle(self, *args, **options):
        if options['clear']:
            UserBehavior.objects.all().delete()
            Product.objects.all().delete()
            self.stdout.write('Cleared existing data.')

        products = self._load_products(options['product_url'])
        category_products = {}
        for pid, _, cat, _, _ in products:
            category_products.setdefault(cat, []).append(pid)

        # ── 1. Upsert products ───────────────────────────────
        for idx, (pid, name, cat, price, desc) in enumerate(products):
            Product.objects.update_or_create(
                product_id=pid,
                defaults=dict(name=name, category=cat, price=price,
                              description=desc, encoded_id=idx),
            )
        self.stdout.write(f'Upserted {len(products)} products.')

        # ── 2. Generate user behaviour ───────────────────────
        product_map = {p.product_id: p for p in Product.objects.all()}
        behaviours  = []
        now         = timezone.now()
        n_users     = options['users']
        n_sessions  = options['sessions']

        for user_id in range(1, n_users + 1):
            # pick a preferred category
            pref_cat = random.choice(list(category_products.keys()))
            ts = now - timedelta(days=random.randint(7, 90))

            for _ in range(n_sessions):
                # 70 % chance: browse within preferred category
                if random.random() < 0.7 and category_products[pref_cat]:
                    pool = category_products[pref_cat]
                else:
                    pool = [p[0] for p in products]

                product_id = random.choice(pool)
                product    = product_map[product_id]

                for action in _action_seq():
                    ts += timedelta(minutes=random.randint(1, 30))
                    behaviours.append(UserBehavior(
                        user_id=user_id,
                        product=product,
                        action=action,
                        timestamp=ts,
                        weight=ACTION_WEIGHT[action],
                    ))

                # occasionally cross-browse to related product
                if random.random() < 0.4:
                    related_pool = category_products.get(pref_cat, pool)
                    rel_pid = random.choice(related_pool)
                    rel_product = product_map[rel_pid]
                    ts += timedelta(minutes=random.randint(1, 10))
                    behaviours.append(UserBehavior(
                        user_id=user_id,
                        product=rel_product,
                        action='view',
                        timestamp=ts,
                        weight=1.0,
                    ))

        UserBehavior.objects.bulk_create(behaviours, batch_size=500)
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {len(behaviours)} behaviour events for {n_users} users.'
            )
        )

    def _load_products(self, product_url=None):
        url = (product_url or settings.PRODUCT_SERVICE_URL).rstrip('/')
        try:
            import requests

            response = requests.get(f'{url}/api/products/', params={'is_active': 'true'}, timeout=10)
            response.raise_for_status()
            payload = response.json()
            items = payload.get('data', payload) if isinstance(payload, dict) else payload
            products = []
            for item in items:
                products.append((
                    int(item['id']),
                    item['name'],
                    item.get('category_name') or str(item.get('category', '')),
                    float(item.get('base_price') or 0),
                    item.get('description') or '',
                ))
            if products:
                self.stdout.write(f'Loaded {len(products)} products from product_service.')
                return products
        except Exception as exc:
            self.stderr.write(f'Could not load product_service catalog: {exc}')

        self.stderr.write('Falling back to built-in sample AI products.')
        return FALLBACK_PRODUCTS

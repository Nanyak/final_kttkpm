"""
Populate Neo4j Knowledge Graph from DB:
  - Upsert all Products and Users as nodes
  - Create behaviour edges (VIEW / CLICK / ADD_CART / BUY)
  - Compute SIMILAR edges for products in the same category

Run: python manage.py setup_graph [--clear]
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Bootstrap Neo4j graph from UserBehavior data.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Wipe graph before re-building')

    def handle(self, *args, **options):
        from graph.client import get_driver
        from graph.queries import (create_constraints, upsert_product,
                                   upsert_user, record_behavior,
                                   create_similar_edge)
        from apps.behavior.models import Product, UserBehavior

        driver = get_driver()

        # ── optional wipe ─────────────────────────────────────
        if options['clear']:
            with driver.session() as s:
                s.run("MATCH (n) DETACH DELETE n")
            self.stdout.write('Graph cleared.')

        # ── constraints ────────────────────────────────────────
        with driver.session() as s:
            s.execute_write(create_constraints)
        self.stdout.write('Constraints created.')

        # ── upsert products ────────────────────────────────────
        products = list(Product.objects.all())
        with driver.session() as s:
            for p in products:
                s.execute_write(upsert_product,
                                p.product_id, p.name, p.category,
                                p.price, p.description)
        self.stdout.write(f'Upserted {len(products)} product nodes.')

        # ── behaviour edges ────────────────────────────────────
        behaviors = list(
            UserBehavior.objects
            .select_related('product')
            .values_list('user_id', 'product__product_id', 'action')
        )
        with driver.session() as s:
            for uid, pid, action in behaviors:
                s.execute_write(upsert_user, uid)
                s.execute_write(record_behavior, uid, pid, action)
        self.stdout.write(f'Created edges for {len(behaviors)} behaviour events.')

        # ── SIMILAR edges (same category) ──────────────────────
        from collections import defaultdict
        category_map = defaultdict(list)
        for p in products:
            category_map[p.category].append(p.product_id)

        similar_count = 0
        with driver.session() as s:
            for cat, pids in category_map.items():
                for i, pa in enumerate(pids):
                    for pb in pids[i + 1:]:
                        score = 0.8  # same-category baseline
                        s.execute_write(create_similar_edge, pa, pb, score, 'same_category')
                        s.execute_write(create_similar_edge, pb, pa, score, 'same_category')
                        similar_count += 2

        self.stdout.write(
            self.style.SUCCESS(
                f'Graph ready: {len(products)} products, '
                f'{len(set(u for u, _, _ in behaviors))} users, '
                f'{similar_count} SIMILAR edges.'
            )
        )

"""
Build dense FAISS and sparse TF-IDF indexes by fetching live product data
from product_service.

Run: python manage.py build_faiss_index
     python manage.py build_faiss_index --url http://product_service:8001
"""
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fetch products from product_service and build dense/sparse retrieval indexes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url', type=str, default=None,
            help='product_service base URL (default: settings.PRODUCT_SERVICE_URL)',
        )
        parser.add_argument(
            '--embed-model', type=str, default=None,
            help='Sentence-transformers model name (default: settings.EMBED_MODEL)',
        )
        parser.add_argument(
            '--retries', type=int, default=30,
            help='number of times to retry product_service before giving up',
        )
        parser.add_argument(
            '--retry-delay', type=float, default=2.0,
            help='seconds to wait between product_service retries',
        )

    def handle(self, *args, **options):
        import requests
        from rag.embedder import build_index
        from rag.product_api import compact_metadata, next_url, product_text, unwrap_items

        base_url    = options['url'] or settings.PRODUCT_SERVICE_URL
        embed_model = options['embed_model'] or settings.EMBED_MODEL
        retries     = max(1, int(options['retries']))
        retry_delay = max(0.1, float(options['retry_delay']))
        faiss_dir   = Path(settings.FAISS_DIR)

        # ── fetch all products from product_service ───────────────
        self.stdout.write(f'Fetching products from {base_url} …')
        products = []
        metadata = []
        page_url = f'{base_url}/api/products/?limit=200'
        attempt = 1

        while page_url:
            try:
                resp = requests.get(page_url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                if attempt >= retries:
                    self.stderr.write(f'Failed to fetch products after {attempt} attempts: {exc}')
                    return
                self.stderr.write(
                    f'Product service not ready ({exc}); retrying in {retry_delay:g}s '
                    f'[{attempt}/{retries}]'
                )
                attempt += 1
                time.sleep(retry_delay)
                continue

            items = unwrap_items(data)
            for p in items:
                pid   = p.get('id')
                name  = p.get('name', '')
                desc = product_text(p)
                if pid:
                    products.append((pid, name, desc))
                    metadata.append(compact_metadata(p))

            # handle DRF pagination
            page_url = next_url(data)

        if not products:
            self.stderr.write('No products returned from product_service.')
            return

        self.stdout.write(f'Building dense/sparse indexes for {len(products)} products…')
        build_index(products, faiss_dir, embed_model=embed_model, product_metadata=metadata)
        self.stdout.write(self.style.SUCCESS(f'Dense/sparse indexes built ({len(products)} products).'))

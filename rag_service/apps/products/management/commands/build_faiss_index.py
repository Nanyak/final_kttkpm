"""
Build FAISS index by fetching live product data from product_service.

Run: python manage.py build_faiss_index
     python manage.py build_faiss_index --url http://product_service:8001
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fetch products from product_service and build the FAISS index.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url', type=str, default=None,
            help='product_service base URL (default: settings.PRODUCT_SERVICE_URL)',
        )
        parser.add_argument(
            '--embed-model', type=str, default=None,
            help='Sentence-transformers model name (default: settings.EMBED_MODEL)',
        )

    def handle(self, *args, **options):
        import requests
        from rag.embedder import build_index
        from rag.product_api import compact_metadata, next_url, unwrap_items

        base_url    = options['url'] or settings.PRODUCT_SERVICE_URL
        embed_model = options['embed_model'] or settings.EMBED_MODEL
        faiss_dir   = Path(settings.FAISS_DIR)

        # ── fetch all products from product_service ───────────────
        self.stdout.write(f'Fetching products from {base_url} …')
        products = []
        metadata = []
        page_url = f'{base_url}/api/products/?limit=200'

        while page_url:
            try:
                resp = requests.get(page_url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                self.stderr.write(f'Failed to fetch products: {exc}')
                return

            items = unwrap_items(data)
            for p in items:
                pid   = p.get('id')
                name  = p.get('name', '')
                desc  = '. '.join(
                    str(part).strip()
                    for part in (p.get('category_name'), p.get('description'), p.get('product_type'))
                    if part
                )
                if pid:
                    products.append((pid, name, desc))
                    metadata.append(compact_metadata(p))

            # handle DRF pagination
            page_url = next_url(data)

        if not products:
            self.stderr.write('No products returned from product_service.')
            return

        self.stdout.write(f'Building FAISS index for {len(products)} products…')
        build_index(products, faiss_dir, embed_model=embed_model, product_metadata=metadata)
        self.stdout.write(self.style.SUCCESS(f'FAISS index built ({len(products)} products).'))

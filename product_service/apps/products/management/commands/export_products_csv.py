import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.products.models import Product


class Command(BaseCommand):
    help = 'Export active product catalog data to the AI dataset products CSV.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default=str(self._default_output()),
            help=(
                'CSV path to write. Defaults to ai_service/ml/datasets/products.csv '
                'when run from the monorepo, otherwise ./products.csv.'
            ),
        )
        parser.add_argument(
            '--include-inactive',
            action='store_true',
            help='Include inactive products as well as active products.',
        )

    def handle(self, *args, **options):
        output = Path(options['output']).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        qs = Product.objects.select_related('category').order_by('id')
        if not options['include_inactive']:
            qs = qs.filter(is_active=True)

        rows = list(qs.values_list(
            'id',
            'name',
            'category__name',
            'base_price',
            'description',
        ))
        if not rows:
            raise CommandError('No products found to export.')

        with output.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['product_id', 'name', 'category', 'price', 'description'])
            for product_id, name, category, price, description in rows:
                writer.writerow([product_id, name, category, price, description or ''])

        self.stdout.write(self.style.SUCCESS(f'Exported {len(rows)} products to {output}'))

    def _default_output(self):
        for parent in Path(__file__).resolve().parents:
            candidate = parent / 'ai_service' / 'ml' / 'datasets'
            if candidate.exists():
                return candidate / 'products.csv'
        return Path.cwd() / 'products.csv'

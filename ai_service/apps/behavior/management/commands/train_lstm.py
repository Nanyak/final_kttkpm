"""
Train the NextItemLSTM on stored UserBehavior data.
Run: python manage.py train_lstm [--epochs N] [--batch-size N]
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'Train the LSTM next-item prediction model on UserBehavior data.'

    def add_arguments(self, parser):
        parser.add_argument('--epochs',     type=int, default=15)
        parser.add_argument('--batch-size', type=int, default=64)
        parser.add_argument('--lr',         type=float, default=1e-3)
        parser.add_argument('--seq-len',    type=int, default=20)
        parser.add_argument('--embed-dim',  type=int, default=64)
        parser.add_argument('--hidden-dim', type=int, default=128)

    def handle(self, *args, **options):
        from apps.behavior.models import UserBehavior
        from ml.lstm.trainer import train

        self.stdout.write('Loading behaviour data…')
        qs = (UserBehavior.objects
              .order_by('user_id', 'timestamp')
              .values_list('user_id', 'product__product_id'))
        behaviors = list(qs)

        if not behaviors:
            self.stderr.write('No behaviour data found. Run seed_data first.')
            return

        self.stdout.write(f'Training on {len(behaviors)} events…')
        train(
            behaviors=behaviors,
            model_dir=Path(settings.MODEL_DIR),
            epochs=options['epochs'],
            batch_size=options['batch_size'],
            lr=options['lr'],
            seq_len=options['seq_len'],
            embed_dim=options['embed_dim'],
            hidden_dim=options['hidden_dim'],
            verbose=True,
        )
        self.stdout.write(self.style.SUCCESS('LSTM training complete.'))

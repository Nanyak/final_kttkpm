"""
Train any combination of next-item prediction models and generate comparison
metrics/charts.

Available models
----------------
  rnn      — Vanilla RNN (fast baseline, prone to vanishing gradients)
  lstm     — LSTM (standard gated sequence model)
  bilstm   — Bidirectional LSTM (reads sequence in both directions)
  gru      — GRU (lighter LSTM, often comparable accuracy)
  narm     — NARM: GRU encoder + local attention gate (CIKM 2017)
  sasrec   — SASRec: causal self-attention transformer (ICDM 2018)
  bert4rec — BERT4Rec: bidirectional transformer, masked item modelling (CIKM 2019)

Usage examples
--------------
# Train all models
python manage.py train_models

# Train a specific subset
python manage.py train_models --models lstm bilstm sasrec bert4rec

# Custom hyperparameters
python manage.py train_models --epochs 20 --hidden-dim 256 --embed-dim 128
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ml.evaluation import (
    evaluate_model,
    leave_one_out_split,
    render_metric_chart,
    save_metrics,
)


MODEL_REGISTRY = {
    'rnn':      ('ml.rnn.trainer',      Path(settings.MODEL_DIR) / 'rnn'),
    'lstm':     ('ml.lstm.trainer',     Path(settings.MODEL_DIR) / 'lstm'),
    'bilstm':   ('ml.bilstm.trainer',   Path(settings.MODEL_DIR) / 'bilstm'),
    'gru':      ('ml.gru.trainer',      Path(settings.MODEL_DIR) / 'gru'),
    'narm':     ('ml.narm.trainer',     Path(settings.MODEL_DIR) / 'narm'),
    'sasrec':   ('ml.sasrec.trainer',   Path(settings.MODEL_DIR) / 'sasrec'),
    'bert4rec': ('ml.bert4rec.trainer', Path(settings.MODEL_DIR) / 'bert4rec'),
}


class Command(BaseCommand):
    help = (
        'Train one or more next-item models '
        '(rnn / lstm / bilstm / gru / narm / sasrec / bert4rec) '
        'and write side-by-side metric comparisons.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            choices=list(MODEL_REGISTRY.keys()),
            default=list(MODEL_REGISTRY.keys()),
            help='Which models to train (default: all)',
        )
        parser.add_argument('--epochs',     type=int,   default=15)
        parser.add_argument('--batch-size', type=int,   default=64)
        parser.add_argument('--lr',         type=float, default=1e-3)
        parser.add_argument('--seq-len',    type=int,   default=20)
        parser.add_argument('--embed-dim',  type=int,   default=64)
        parser.add_argument('--hidden-dim', type=int,   default=128)
        parser.add_argument('--num-layers', type=int,   default=2)
        parser.add_argument('--dropout',    type=float, default=0.3)
        parser.add_argument('--top-k',      type=int,   default=5)
        parser.add_argument(
            '--report-dir',
            default=str(settings.BASE_DIR / 'data' / 'reports' / 'model_comparison'),
            help='Directory for model_metrics.json/csv and PNG comparison charts.',
        )

    def handle(self, *args, **options):
        import importlib
        from apps.behavior.models import UserBehavior

        self.stdout.write('Loading behaviour data…')
        behaviors = list(
            UserBehavior.objects
            .order_by('user_id', 'timestamp')
            .values_list('user_id', 'product__product_id')
        )

        if not behaviors:
            self.stderr.write('No behaviour data found. Run seed_data first.')
            return

        train_behaviors, tests = leave_one_out_split(behaviors)
        self.stdout.write(
            f'Training on {len(train_behaviors)} events; '
            f'evaluating on {len(tests)} held-out next-item cases.\n'
        )

        results = {}
        metrics = {}
        for name in options['models']:
            module_path, model_dir = MODEL_REGISTRY[name]
            self.stdout.write(f'── Training {name.upper()} ─────────────────')
            try:
                trainer = importlib.import_module(module_path)
                model, proc, meta = trainer.train(
                    behaviors=train_behaviors,
                    model_dir=model_dir,
                    epochs=options['epochs'],
                    batch_size=options['batch_size'],
                    lr=options['lr'],
                    seq_len=options['seq_len'],
                    embed_dim=options['embed_dim'],
                    hidden_dim=options['hidden_dim'],
                    num_layers=options['num_layers'],
                    dropout=options['dropout'],
                    verbose=True,
                )
                results[name] = meta.get('final_loss')
                row = evaluate_model(
                    model=model,
                    proc=proc,
                    tests=tests,
                    seq_len=meta.get('seq_len', options['seq_len']),
                    top_k=options['top_k'],
                )
                row['final_loss'] = meta.get('final_loss')
                metrics[name] = row
            except Exception as exc:
                self.stderr.write(f'  ERROR training {name}: {exc}')
                results[name] = None
                metrics[name] = {
                    'test_cases': 0,
                    'accuracy@1': 0.0,
                    f'accuracy@{options["top_k"]}': 0.0,
                    f'f1@{options["top_k"]}': 0.0,
                    'final_loss': None,
                    'error': str(exc),
                }

        report_dir = Path(options['report_dir'])
        self._write_reports(metrics, report_dir, options['top_k'])
        self._print_comparison(results, metrics, options['top_k'], report_dir)

    def _write_reports(self, metrics: dict, report_dir: Path, top_k: int):
        save_metrics(metrics, report_dir)
        render_metric_chart(
            metrics, 'accuracy@1',
            report_dir / 'accuracy_comparison.png',
            'Model Accuracy@1 Comparison',
        )
        render_metric_chart(
            metrics, f'accuracy@{top_k}',
            report_dir / f'accuracy_at_{top_k}_comparison.png',
            f'Model Accuracy@{top_k} Comparison',
        )
        render_metric_chart(
            metrics, f'f1@{top_k}',
            report_dir / f'f1_at_{top_k}_comparison.png',
            f'Model F1@{top_k} Comparison',
        )

    def _print_comparison(self, results: dict, metrics: dict, top_k: int, report_dir: Path):
        self.stdout.write('\n' + '=' * 78)
        self.stdout.write(
            f'  {"Model":<10}  {"Loss":>10}  {"Acc@1":>10}  '
            f'{"Acc@" + str(top_k):>10}  {"F1@" + str(top_k):>10}'
        )
        self.stdout.write('─' * 78)
        best_name = max(
            (k for k, v in metrics.items() if v.get(f'accuracy@{top_k}') is not None),
            key=lambda k: metrics[k].get(f'accuracy@{top_k}', 0),
            default=None,
        )
        for name in results:
            loss = results[name]
            row = metrics.get(name, {})
            marker = '  <-- best' if name == best_name else ''
            loss_str = f'{loss:.6f}' if loss is not None else 'failed'
            self.stdout.write(
                f'  {name.upper():<10}  {loss_str:>10}  '
                f'{row.get("accuracy@1", 0):>10.4f}  '
                f'{row.get(f"accuracy@{top_k}", 0):>10.4f}  '
                f'{row.get(f"f1@{top_k}", 0):>10.4f}{marker}'
            )
        self.stdout.write('=' * 78)
        self.stdout.write(f'Reports written to: {report_dir}')
        if best_name:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nBest held-out accuracy@{top_k}: {best_name.upper()} '
                    f'({metrics[best_name][f"accuracy@{top_k}"]:.4f})\n'
                    f'Set ACTIVE_MODEL={best_name} in your .env to use it.'
                )
            )

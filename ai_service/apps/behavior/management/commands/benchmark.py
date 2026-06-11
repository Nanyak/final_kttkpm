"""
Benchmark: train any combination of models × datasets and write comparison
tables, metrics, and PNG charts.

Usage examples
--------------
# Full grid: all 7 models × all 5 datasets
python manage.py benchmark

# Specific models × specific datasets
python manage.py benchmark --models lstm sasrec bert4rec --datasets standard power_users

# Single cell
python manage.py benchmark --models bilstm --datasets categorical --epochs 20

Datasets
--------
  tiny        — Cold-start, 20 users, sparse (tests generalisation)
  standard    — Balanced baseline, 100 users (default comparison)
  power_users — Heavy engagement, 50 users, long sequences
  noisy       — 200 users, random exploration, high noise
  categorical — 80 users, 95% category loyalty

Models
------
  rnn / lstm / bilstm / gru / narm / sasrec / bert4rec
"""
import importlib
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ml.datasets import REGISTRY as DATASET_REGISTRY
from ml.evaluation import (
    evaluate_model,
    leave_one_out_split,
    render_metric_chart,
    save_metrics,
)

MODEL_NAMES = ['rnn', 'lstm', 'bilstm', 'gru', 'narm', 'sasrec', 'bert4rec']


class Command(BaseCommand):
    help = 'Train model × dataset combinations and print a loss comparison grid.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models', nargs='+',
            choices=MODEL_NAMES, default=MODEL_NAMES,
            help='Models to benchmark (default: all)',
        )
        parser.add_argument(
            '--datasets', nargs='+',
            choices=list(DATASET_REGISTRY.keys()),
            default=list(DATASET_REGISTRY.keys()),
            help='Datasets to benchmark (default: all)',
        )
        parser.add_argument('--epochs',     type=int,   default=10)
        parser.add_argument('--batch-size', type=int,   default=64)
        parser.add_argument('--lr',         type=float, default=1e-3)
        parser.add_argument('--seq-len',    type=int,   default=20)
        parser.add_argument('--embed-dim',  type=int,   default=64)
        parser.add_argument('--hidden-dim', type=int,   default=128)
        parser.add_argument('--num-layers', type=int,   default=2)
        parser.add_argument('--dropout',    type=float, default=0.3)
        parser.add_argument('--seed',       type=int,   default=42,
                            help='Random seed for dataset generation')
        parser.add_argument('--top-k',      type=int,   default=5)
        parser.add_argument(
            '--report-dir',
            default=str(settings.BASE_DIR / 'data' / 'reports' / 'benchmark'),
            help='Directory for benchmark metrics and PNG comparison charts.',
        )

    def handle(self, *args, **options):
        models_to_run   = options['models']
        datasets_to_run = options['datasets']

        self.stdout.write(
            f'\nBenchmarking {len(models_to_run)} model(s) × '
            f'{len(datasets_to_run)} dataset(s)  '
            f'({options["epochs"]} epochs each)\n'
        )

        # results[dataset_name][model_name] = final_loss | None
        results: dict = {ds: {} for ds in datasets_to_run}
        metrics_by_dataset: dict = {ds: {} for ds in datasets_to_run}

        for ds_name in datasets_to_run:
            dataset = DATASET_REGISTRY[ds_name]()
            summary = dataset.summary()
            self.stdout.write(
                f'\n── Dataset: {ds_name.upper():<15} '
                f'{summary["events"]:>6} events / '
                f'{summary["users"]:>4} users / '
                f'avg {summary["avg_events_per_user"]} events/user'
            )

            behaviors = dataset.to_behaviors(seed=options['seed'])
            train_behaviors, tests = leave_one_out_split(behaviors)

            for model_name in models_to_run:
                self.stdout.write(f'   Training {model_name}…', ending='')
                try:
                    trainer = importlib.import_module(f'ml.{model_name}.trainer')
                    with tempfile.TemporaryDirectory() as tmp:
                        model, proc, meta = trainer.train(
                            behaviors=train_behaviors,
                            model_dir=Path(tmp),
                            epochs=options['epochs'],
                            batch_size=options['batch_size'],
                            lr=options['lr'],
                            seq_len=options['seq_len'],
                            embed_dim=options['embed_dim'],
                            hidden_dim=options['hidden_dim'],
                            num_layers=options['num_layers'],
                            dropout=options['dropout'],
                            verbose=False,
                        )
                    loss = meta.get('final_loss')
                    results[ds_name][model_name] = loss
                    row = evaluate_model(
                        model=model,
                        proc=proc,
                        tests=tests,
                        seq_len=meta.get('seq_len', options['seq_len']),
                        top_k=options['top_k'],
                    )
                    row['final_loss'] = loss
                    metrics_by_dataset[ds_name][model_name] = row
                    top_k = options['top_k']
                    self.stdout.write(
                        f'  loss={loss:.4f}  '
                        f'acc@{top_k}={row[f"accuracy@{top_k}"]:.4f}'
                    )
                except Exception as exc:
                    results[ds_name][model_name] = None
                    metrics_by_dataset[ds_name][model_name] = {
                        'test_cases': 0,
                        'accuracy@1': 0.0,
                        f'accuracy@{options["top_k"]}': 0.0,
                        f'f1@{options["top_k"]}': 0.0,
                        'final_loss': None,
                        'error': str(exc),
                    }
                    self.stdout.write(f'  ERROR: {exc}')

        report_dir = Path(options['report_dir'])
        aggregate_metrics = self._write_reports(
            models_to_run, datasets_to_run, metrics_by_dataset, report_dir, options['top_k'],
        )
        self._print_grid(models_to_run, datasets_to_run, results, metrics_by_dataset, options['top_k'])
        self.stdout.write(f'Reports written to: {report_dir}')
        self._print_aggregate_recommendations(aggregate_metrics, options['top_k'])

    def _write_reports(self, models, datasets, metrics_by_dataset, report_dir: Path, top_k: int):
        flat = {}
        for ds_name in datasets:
            for model_name in models:
                flat[f'{ds_name}:{model_name}'] = metrics_by_dataset[ds_name].get(model_name, {})

        save_metrics(flat, report_dir)

        aggregate = {}
        for model_name in models:
            rows = [
                metrics_by_dataset[ds].get(model_name, {})
                for ds in datasets
                if metrics_by_dataset[ds].get(model_name)
            ]
            denom = max(len(rows), 1)
            aggregate[model_name] = {
                'accuracy@1': round(sum(r.get('accuracy@1', 0.0) for r in rows) / denom, 6),
                f'accuracy@{top_k}': round(sum(r.get(f'accuracy@{top_k}', 0.0) for r in rows) / denom, 6),
                f'f1@{top_k}': round(sum(r.get(f'f1@{top_k}', 0.0) for r in rows) / denom, 6),
                'final_loss': round(sum((r.get('final_loss') or 0.0) for r in rows) / denom, 6),
            }

        save_metrics(aggregate, report_dir / 'aggregate')
        render_metric_chart(
            aggregate, 'accuracy@1',
            report_dir / 'accuracy_comparison.png',
            'Average Model Accuracy@1',
        )
        render_metric_chart(
            aggregate, f'accuracy@{top_k}',
            report_dir / f'accuracy_at_{top_k}_comparison.png',
            f'Average Model Accuracy@{top_k}',
        )
        render_metric_chart(
            aggregate, f'f1@{top_k}',
            report_dir / f'f1_at_{top_k}_comparison.png',
            f'Average Model F1@{top_k}',
        )
        return aggregate

    def _print_grid(self, models, datasets, results, metrics_by_dataset, top_k):
        col_w    = 11
        ds_col_w = 14
        header   = f'  {"":>{ds_col_w}} ' + ''.join(f'{m.upper():>{col_w}}' for m in models)
        divider  = '─' * len(header)

        self.stdout.write('\n' + '=' * len(header))
        self.stdout.write('  BENCHMARK RESULTS  (accuracy@%s, higher = better)' % top_k)
        self.stdout.write(divider)
        self.stdout.write(header)
        self.stdout.write(divider)

        for ds_name in datasets:
            row_values = [
                metrics_by_dataset[ds_name].get(m, {}).get(f'accuracy@{top_k}', 0.0)
                for m in models
            ]
            best_idx = _argmax(row_values)

            row = f'  {ds_name.upper():>{ds_col_w}} '
            for i, val in enumerate(row_values):
                cell = f'{val:.4f}' if val is not None else ' failed'
                mark = '*' if i == best_idx else ' '
                row += f'{(mark + cell):>{col_w}}'
            self.stdout.write(row)

        self.stdout.write(divider)
        self.stdout.write('  * = best model for that dataset')
        self.stdout.write('=' * len(header) + '\n')

        # Overall winner per dataset
        self.stdout.write('Recommendations:')
        for ds_name in datasets:
            row_values = [
                metrics_by_dataset[ds_name].get(m, {}).get(f'accuracy@{top_k}', 0.0)
                for m in models
            ]
            best_idx = _argmax(row_values)
            if best_idx is not None:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  {ds_name:<14} → best model: '
                        f'{models[best_idx].upper()} '
                        f'(accuracy@{top_k}={row_values[best_idx]:.4f})'
                    )
                )
        self.stdout.write(
            '\nSet ACTIVE_MODEL=<model_name> in .env to activate the winner.\n'
        )

    def _print_aggregate_recommendations(self, aggregate_metrics, top_k):
        best = _argmax([v.get(f'accuracy@{top_k}', 0.0) for v in aggregate_metrics.values()])
        if best is None:
            return
        names = list(aggregate_metrics.keys())
        best_name = names[best]
        self.stdout.write(
            self.style.SUCCESS(
                f'Average winner: {best_name.upper()} '
                f'(accuracy@{top_k}={aggregate_metrics[best_name][f"accuracy@{top_k}"]:.4f})'
            )
        )


def _argmin(values):
    """Index of the minimum non-None value, or None if all failed."""
    valid = [(i, v) for i, v in enumerate(values) if v is not None]
    if not valid:
        return None
    return min(valid, key=lambda x: x[1])[0]


def _argmax(values):
    """Index of the maximum non-None value, or None if all failed."""
    valid = [(i, v) for i, v in enumerate(values) if v is not None]
    if not valid:
        return None
    return max(valid, key=lambda x: x[1])[0]

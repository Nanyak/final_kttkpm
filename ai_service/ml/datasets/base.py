"""
Shared product catalogue and base class for all dataset generators.

Every dataset subclass must implement:
    generate(seed: int) -> list of (user_id, product_id, action, timestamp, weight)

And can use the helper `to_behaviors()` to convert to the simple
(user_id, product_id) format expected by model trainers.
"""
import csv
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

# ── Product catalogue ─────────────────────────────────────────────────────────
PRODUCTS_CSV = Path(__file__).with_name('products.csv')


def _load_products_from_csv(path: Path = PRODUCTS_CSV) -> List[Tuple[int, str, str, float, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f'{path} does not exist. Export it from product_service with '
            f'`python manage.py export_products_csv --output {path}`.'
        )

    products = []
    with path.open(newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        required = {'product_id', 'name', 'category', 'price', 'description'}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path} is missing required columns: {sorted(missing)}')

        for row in reader:
            products.append((
                int(row['product_id']),
                row['name'],
                row['category'],
                float(row['price']),
                row.get('description') or '',
            ))

    if not products:
        raise ValueError(f'{path} contains no products')

    return products


PRODUCTS = _load_products_from_csv()

ACTION_WEIGHT = {'view': 1.0, 'click': 2.0, 'add_to_cart': 3.0, 'purchase': 4.0}

CATEGORY_PRODUCTS: dict = {}
for _pid, _name, _cat, _price, _desc in PRODUCTS:
    CATEGORY_PRODUCTS.setdefault(_cat, []).append(_pid)

ALL_PIDS = [p[0] for p in PRODUCTS]


# ── Base class ────────────────────────────────────────────────────────────────
class BaseDataset(ABC):
    """
    Abstract base for all dataset generators.

    Subclasses set class-level metadata and implement `generate()`.
    """
    name: str        = ''
    description: str = ''
    num_users: int   = 0
    num_sessions: int = 0

    @abstractmethod
    def generate(self, seed: int = 42) -> List[Tuple]:
        """
        Returns a list of raw event tuples:
            (user_id, product_id, action, timestamp, weight)
        """

    def to_behaviors(self, seed: int = 42) -> List[Tuple[int, int]]:
        """
        Convenience wrapper: returns [(user_id, product_id)] ordered by
        timestamp — the format expected by every model trainer.
        """
        events = self.generate(seed=seed)
        events.sort(key=lambda e: (e[0], e[3]))   # sort by user_id, then timestamp
        return [(uid, pid) for uid, pid, *_ in events]

    def summary(self) -> dict:
        events = self.generate()
        users  = len({e[0] for e in events})
        pids   = len({e[1] for e in events})
        return {
            'name':        self.name,
            'description': self.description,
            'events':      len(events),
            'users':       users,
            'products':    pids,
            'avg_events_per_user': round(len(events) / max(users, 1), 1),
        }


# ── Shared helpers ────────────────────────────────────────────────────────────
def _funnel(rng: random.Random, purchase_rate: float = 0.3, cart_rate: float = 0.5):
    """Return a realistic action funnel sequence."""
    seq = ['view'] * rng.randint(2, 5)
    if rng.random() > 0.3:
        seq += ['click'] * rng.randint(1, 3)
    if rng.random() < cart_rate:
        seq.append('add_to_cart')
    if rng.random() < purchase_rate:
        seq.append('purchase')
    return seq


def _now_base(seed: int) -> datetime:
    """Deterministic base timestamp for reproducibility."""
    rng = random.Random(seed)
    days_back = rng.randint(30, 120)
    return datetime(2025, 1, 1, tzinfo=timezone.utc) - timedelta(days=days_back)

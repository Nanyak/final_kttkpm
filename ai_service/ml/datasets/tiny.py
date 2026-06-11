"""
Dataset 1 — Tiny (Cold-Start / Sparse)
=======================================
Simulates a brand-new store with very few users and very short interaction
histories.  Models must make good predictions with minimal data.

Characteristics:
  - 20 users, 2 sessions each
  - Short action sequences (mostly views, rare purchases)
  - High product diversity relative to user count
  - Purchase rate: 10%  (very low)

Use to test: cold-start robustness, generalisation from short sequences.
"""
import random
from datetime import timedelta
from typing import List, Tuple

from .base import (
    BaseDataset, PRODUCTS, CATEGORY_PRODUCTS, ALL_PIDS,
    ACTION_WEIGHT, _funnel, _now_base,
)


class TinyDataset(BaseDataset):
    name         = 'tiny'
    description  = 'Cold-start scenario: 20 users, sparse histories, very few purchases.'
    num_users    = 20
    num_sessions = 2

    def generate(self, seed: int = 42) -> List[Tuple]:
        rng    = random.Random(seed)
        events = []
        base_ts = _now_base(seed)

        for user_id in range(1, self.num_users + 1):
            pref_cat = rng.choice(list(CATEGORY_PRODUCTS.keys()))
            ts = base_ts - timedelta(days=rng.randint(1, 14))

            for _ in range(self.num_sessions):
                # Very random product selection (no strong affinity)
                pool = CATEGORY_PRODUCTS[pref_cat] if rng.random() < 0.5 else ALL_PIDS
                pid  = rng.choice(pool)

                for action in _funnel(rng, purchase_rate=0.10, cart_rate=0.25):
                    ts += timedelta(minutes=rng.randint(5, 60))
                    events.append((
                        user_id, pid, action, ts, ACTION_WEIGHT[action]
                    ))

        return events

"""
Dataset 2 — Standard (Balanced Baseline)
=========================================
A realistic mid-sized e-commerce dataset reflecting typical consumer
behaviour: moderate category affinity, occasional cross-browsing, and
a healthy mix of actions.

Characteristics:
  - 100 users, 6 sessions each
  - 70% within-category browsing, 30% cross-category
  - Moderate purchase rate: 30%
  - Occasional "related item" side-browse after each session

Use as: the default training set; baseline for all model comparisons.
"""
import random
from datetime import timedelta
from typing import List, Tuple

from .base import (
    BaseDataset, PRODUCTS, CATEGORY_PRODUCTS, ALL_PIDS,
    ACTION_WEIGHT, _funnel, _now_base,
)


class StandardDataset(BaseDataset):
    name         = 'standard'
    description  = 'Balanced baseline: 100 users, mixed category browsing, 30% purchase rate.'
    num_users    = 100
    num_sessions = 6

    def generate(self, seed: int = 42) -> List[Tuple]:
        rng     = random.Random(seed)
        events  = []
        base_ts = _now_base(seed)

        for user_id in range(1, self.num_users + 1):
            pref_cat = rng.choice(list(CATEGORY_PRODUCTS.keys()))
            ts = base_ts - timedelta(days=rng.randint(7, 90))

            for _ in range(self.num_sessions):
                pool = (
                    CATEGORY_PRODUCTS[pref_cat]
                    if rng.random() < 0.7 else ALL_PIDS
                )
                pid = rng.choice(pool)

                for action in _funnel(rng, purchase_rate=0.30, cart_rate=0.50):
                    ts += timedelta(minutes=rng.randint(1, 30))
                    events.append((user_id, pid, action, ts, ACTION_WEIGHT[action]))

                # cross-browse: 40% chance of viewing a related product
                if rng.random() < 0.4:
                    related = rng.choice(CATEGORY_PRODUCTS.get(pref_cat, ALL_PIDS))
                    ts += timedelta(minutes=rng.randint(1, 10))
                    events.append((user_id, related, 'view', ts, ACTION_WEIGHT['view']))

        return events

"""
Dataset 5 — Categorical (Strong Category Loyalty)
===================================================
Models niche shoppers who are deeply loyal to 1–2 categories and
almost never stray.  Sequences are highly predictable within a
category, making it easier for models to learn item-to-item
transitions but harder to generalise across categories.

Characteristics:
  - 80 users, 10 sessions each
  - 95% within-category browsing (extremely strong affinity)
  - Users cycle through all items in their category repeatedly
  - High purchase rate: 50%
  - Occasional "gift purchase" outside preferred category (5%)

Use to test: category-level pattern learning; whether models can
exploit strong sequential regularity without overfitting.
"""
import random
from datetime import timedelta
from typing import List, Tuple

from .base import (
    BaseDataset, PRODUCTS, CATEGORY_PRODUCTS, ALL_PIDS,
    ACTION_WEIGHT, _funnel, _now_base,
)


class CategoricalDataset(BaseDataset):
    name         = 'categorical'
    description  = 'Niche shoppers: 80 users, 95% category loyalty, 50% purchase rate.'
    num_users    = 80
    num_sessions = 10

    def generate(self, seed: int = 42) -> List[Tuple]:
        rng     = random.Random(seed)
        events  = []
        base_ts = _now_base(seed)
        categories = list(CATEGORY_PRODUCTS.keys())

        for user_id in range(1, self.num_users + 1):
            # Each user is strongly locked into one category
            pref_cat   = rng.choice(categories)
            pref_pool  = CATEGORY_PRODUCTS[pref_cat]
            ts = base_ts - timedelta(days=rng.randint(14, 60))

            # Build a shuffled cycle of all products in the preferred category
            cycle = pref_pool[:]
            rng.shuffle(cycle)
            cycle_idx = 0

            for session_idx in range(self.num_sessions):
                # 95% stay in category; 5% gift/impulse buy from random category
                if rng.random() < 0.95:
                    # Cycle through category products so every item appears
                    pid = cycle[cycle_idx % len(cycle)]
                    cycle_idx += 1
                else:
                    other_cat = rng.choice([c for c in categories if c != pref_cat])
                    pid = rng.choice(CATEGORY_PRODUCTS[other_cat])

                for action in _funnel(rng, purchase_rate=0.50, cart_rate=0.65):
                    ts += timedelta(minutes=rng.randint(5, 45))
                    events.append((user_id, pid, action, ts, ACTION_WEIGHT[action]))

                # Users sometimes re-view the same item before buying
                if rng.random() < 0.3:
                    ts += timedelta(minutes=rng.randint(1, 10))
                    events.append((user_id, pid, 'view', ts, ACTION_WEIGHT['view']))

                ts += timedelta(days=rng.randint(1, 7))

        return events

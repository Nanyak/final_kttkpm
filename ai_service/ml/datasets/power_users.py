"""
Dataset 3 — Power Users (Long Sequences, High Engagement)
===========================================================
Models a segment of highly-active shoppers who browse extensively,
compare many products, and purchase frequently.  Generates long
per-user sequences that reward models with strong long-range memory.

Characteristics:
  - 50 users, 20 sessions each
  - Extensive within-category deep-dives (5+ items per session)
  - High purchase rate: 60%
  - Users also compare across 2 favourite categories
  - Long time horizon: events spread over 6 months

Use to test: long-sequence modelling (SASRec, BERT4Rec, BiLSTM advantage).
"""
import random
from datetime import timedelta
from typing import List, Tuple

from .base import (
    BaseDataset, PRODUCTS, CATEGORY_PRODUCTS, ALL_PIDS,
    ACTION_WEIGHT, _funnel, _now_base,
)


class PowerUsersDataset(BaseDataset):
    name         = 'power_users'
    description  = 'Power shoppers: 50 users, 20 sessions, long sequences, 60% purchase rate.'
    num_users    = 50
    num_sessions = 20

    def generate(self, seed: int = 42) -> List[Tuple]:
        rng     = random.Random(seed)
        events  = []
        base_ts = _now_base(seed)
        categories = list(CATEGORY_PRODUCTS.keys())

        for user_id in range(1, self.num_users + 1):
            # Each power user has 2 favourite categories
            fav_cats = rng.sample(categories, k=2)
            ts = base_ts - timedelta(days=rng.randint(60, 180))

            for session_idx in range(self.num_sessions):
                # Alternate between favourite categories
                cat   = fav_cats[session_idx % 2]
                pool  = CATEGORY_PRODUCTS[cat]

                # Browse multiple items per session (deep-dive)
                items_this_session = rng.randint(3, 6)
                for _ in range(items_this_session):
                    pid = rng.choice(pool)
                    for action in _funnel(rng, purchase_rate=0.60, cart_rate=0.70):
                        ts += timedelta(minutes=rng.randint(1, 20))
                        events.append((user_id, pid, action, ts, ACTION_WEIGHT[action]))

                # Occasional cross-category comparison
                if rng.random() < 0.5:
                    other_cat = rng.choice(categories)
                    compare_pid = rng.choice(CATEGORY_PRODUCTS[other_cat])
                    for action in ['view', 'click']:
                        ts += timedelta(minutes=rng.randint(1, 5))
                        events.append((user_id, compare_pid, action, ts, ACTION_WEIGHT[action]))

                ts += timedelta(days=rng.randint(1, 10))  # gap between sessions

        return events

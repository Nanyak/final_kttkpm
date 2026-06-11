"""
Dataset 4 — Noisy (Random Exploration, Low Affinity)
======================================================
Models casual or first-time visitors who browse randomly across all
categories without any strong preference pattern.  There is significant
noise injected via random product jumps, making it harder for sequence
models to learn reliable transitions.

Characteristics:
  - 200 users, 4 sessions each (large but shallow)
  - Fully random product selection 60% of the time
  - Low purchase rate: 15%
  - 20% of events are pure random "distraction" views (noise)
  - Wide spread of timestamps (users visit sporadically)

Use to test: noise robustness; which models degrade least under weak signals.
"""
import random
from datetime import timedelta
from typing import List, Tuple

from .base import (
    BaseDataset, PRODUCTS, CATEGORY_PRODUCTS, ALL_PIDS,
    ACTION_WEIGHT, _funnel, _now_base,
)


class NoisyDataset(BaseDataset):
    name         = 'noisy'
    description  = 'Casual browsers: 200 users, random exploration, 15% purchase rate, high noise.'
    num_users    = 200
    num_sessions = 4

    # Noise injection ratio: this fraction of extra random views are added
    NOISE_RATIO = 0.20

    def generate(self, seed: int = 42) -> List[Tuple]:
        rng     = random.Random(seed)
        events  = []
        base_ts = _now_base(seed)

        for user_id in range(1, self.num_users + 1):
            pref_cat = rng.choice(list(CATEGORY_PRODUCTS.keys()))
            ts = base_ts - timedelta(days=rng.randint(1, 120))

            for _ in range(self.num_sessions):
                # 60% random, 40% within preferred category
                pool = ALL_PIDS if rng.random() < 0.6 else CATEGORY_PRODUCTS[pref_cat]
                pid  = rng.choice(pool)

                for action in _funnel(rng, purchase_rate=0.15, cart_rate=0.30):
                    ts += timedelta(minutes=rng.randint(1, 120))
                    events.append((user_id, pid, action, ts, ACTION_WEIGHT[action]))

            # Inject random noise views
            n_noise = max(1, int(len(events) * self.NOISE_RATIO // self.num_users))
            for _ in range(n_noise):
                noise_pid = rng.choice(ALL_PIDS)
                noise_ts  = base_ts - timedelta(
                    days=rng.randint(0, 120),
                    hours=rng.randint(0, 23),
                )
                events.append((user_id, noise_pid, 'view', noise_ts, ACTION_WEIGHT['view']))

        return events

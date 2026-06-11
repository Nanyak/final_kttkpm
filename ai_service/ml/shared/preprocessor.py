"""
Converts raw UserBehavior rows into (input_sequence, target) pairs
suitable for training next-item sequence models.
"""
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset


class BehaviorPreprocessor:
    """
    Builds:
      - product_to_idx  : product_id  → 1-based integer
      - idx_to_product  : integer     → product_id
    Then converts per-user behaviour sequences into sliding-window samples.
    """

    def __init__(self, min_seq_len: int = 2, max_seq_len: int = 20):
        self.min_seq_len   = min_seq_len
        self.max_seq_len   = max_seq_len
        self.product_to_idx: Dict[int, int] = {}
        self.idx_to_product: Dict[int, int] = {}
        self.vocab_size = 0

    # ── vocabulary ────────────────────────────────────────────
    def fit(self, product_ids: List[int]):
        unique = sorted(set(product_ids))
        self.product_to_idx = {pid: idx + 1 for idx, pid in enumerate(unique)}
        self.idx_to_product = {v: k for k, v in self.product_to_idx.items()}
        self.vocab_size = len(unique)

    def encode(self, product_id: int) -> int:
        return self.product_to_idx.get(product_id, 0)

    def decode(self, idx: int) -> int:
        return self.idx_to_product.get(idx, -1)

    # ── sequence building ─────────────────────────────────────
    def build_sequences(
        self, behaviors: List[Tuple[int, int]]   # [(user_id, product_id), ...]
    ) -> List[Tuple[List[int], int]]:
        """
        Returns list of (input_seq, target) where input_seq is a list of
        encoded product indices and target is the encoded next-item index.
        """
        user_seqs: Dict[int, List[int]] = defaultdict(list)
        for user_id, product_id in behaviors:
            enc = self.encode(product_id)
            if enc:
                user_seqs[user_id].append(enc)

        samples = []
        for seq in user_seqs.values():
            if len(seq) < self.min_seq_len + 1:
                continue
            # sliding window
            for end in range(self.min_seq_len, len(seq)):
                start = max(0, end - self.max_seq_len)
                inp    = seq[start:end]
                target = seq[end]
                samples.append((inp, target))
        return samples

    def pad_sequence(self, seq: List[int], length: int) -> List[int]:
        if len(seq) >= length:
            return seq[-length:]
        return [0] * (length - len(seq)) + seq


class BehaviorDataset(Dataset):
    def __init__(self, samples: List[Tuple[List[int], int]], seq_len: int = 20):
        self.seq_len = seq_len
        self.X, self.y = [], []
        for inp, target in samples:
            padded = self._pad(inp)
            self.X.append(padded)
            self.y.append(target)
        self.X = np.array(self.X, dtype=np.int64)
        self.y = np.array(self.y, dtype=np.int64)

    def _pad(self, seq):
        if len(seq) >= self.seq_len:
            return seq[-self.seq_len:]
        return [0] * (self.seq_len - len(seq)) + seq

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.X[idx], dtype=torch.long),
            torch.tensor(self.y[idx], dtype=torch.long),
        )

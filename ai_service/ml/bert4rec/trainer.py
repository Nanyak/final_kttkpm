"""
Train NextItemBERT4Rec and persist weights + preprocessor to disk.

BERT4Rec uses a Cloze (masked item modelling) training objective:
  - For each sequence, randomly mask ~20% of items with a [MASK] token.
  - The model predicts the original item at every masked position.
  - Loss is computed only over masked positions (others are ignored).

At inference, the last item in the user's sequence is replaced with
[MASK] and the model's prediction at that position is used as the
next-item score.
"""
import json
import pickle
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .model import NextItemBERT4Rec
from ml.shared.preprocessor import BehaviorPreprocessor, BehaviorDataset


def train(
    behaviors,
    model_dir: Path,
    epochs: int = 10,
    batch_size: int = 64,
    lr: float = 1e-3,
    seq_len: int = 20,
    embed_dim: int = 64,
    hidden_dim: int = 128,
    num_layers: int = 2,
    dropout: float = 0.2,
    n_heads: int = 4,
    mask_prob: float = 0.2,
    verbose: bool = True,
):
    """
    Train on a list of (user_id, product_id) tuples ordered by timestamp.
    Saves bert4rec.pt, preprocessor.pkl, meta.json to model_dir.
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    proc = BehaviorPreprocessor(max_seq_len=seq_len)
    proc.fit([pid for _, pid in behaviors])
    samples = proc.build_sequences(behaviors)
    if not samples:
        raise ValueError('Not enough sequence data to train. Run seed_data first.')

    dataloader = DataLoader(
        BehaviorDataset(samples, seq_len=seq_len),
        batch_size=batch_size, shuffle=True,
    )

    model = NextItemBERT4Rec(
        vocab_size=proc.vocab_size,
        embed_dim=embed_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout,
        n_heads=n_heads,
        max_len=seq_len,
        mask_prob=mask_prob,
    ).to(device)

    optimiser = torch.optim.Adam(model.parameters(), lr=lr, betas=(0.9, 0.999))
    # ignore_index=0 (padding) and -1 (unmasked positions)
    criterion = nn.CrossEntropyLoss(ignore_index=-1)

    model.train()
    history = []
    for epoch in range(1, epochs + 1):
        total = 0.0
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)

            # Apply Cloze mask to input; build per-position labels
            masked_X, mask_pos = model.apply_mask(X)

            # Labels: true item id at masked positions, -1 everywhere else
            labels = torch.full_like(X, fill_value=-1)
            labels[mask_pos] = X[mask_pos]

            optimiser.zero_grad()
            logits = model(masked_X)        # (B, T, vocab+2)
            B, T, V = logits.shape
            loss = criterion(logits.view(B * T, V), labels.view(B * T))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimiser.step()
            total += loss.item()
        avg = total / len(dataloader)
        history.append(avg)
        if verbose:
            print(f'[BERT4Rec] Epoch {epoch:>3}/{epochs}  loss={avg:.4f}')

    torch.save(model.state_dict(), model_dir / 'bert4rec.pt')
    with open(model_dir / 'preprocessor.pkl', 'wb') as f:
        pickle.dump(proc, f)
    meta = {
        'model_type': 'bert4rec', 'vocab_size': proc.vocab_size,
        'embed_dim': embed_dim, 'hidden_dim': hidden_dim,
        'num_layers': num_layers, 'dropout': dropout,
        'n_heads': n_heads, 'seq_len': seq_len, 'mask_prob': mask_prob,
        'final_loss': round(history[-1], 6) if history else None,
    }
    with open(model_dir / 'meta.json', 'w') as f:
        json.dump(meta, f, indent=2)
    if verbose:
        print(f'[BERT4Rec] Saved to {model_dir}')
    return model, proc, meta


def load(model_dir: Path):
    with open(model_dir / 'meta.json') as f:
        meta = json.load(f)
    with open(model_dir / 'preprocessor.pkl', 'rb') as f:
        proc = pickle.load(f)
    model = NextItemBERT4Rec(
        vocab_size=meta['vocab_size'], embed_dim=meta['embed_dim'],
        hidden_dim=meta['hidden_dim'], num_layers=meta['num_layers'],
        dropout=meta['dropout'],
        n_heads=meta.get('n_heads', 4),
        max_len=meta.get('seq_len', 20),
        mask_prob=meta.get('mask_prob', 0.2),
    )
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.load_state_dict(torch.load(model_dir / 'bert4rec.pt', map_location=device))
    model.eval()
    return model.to(device), proc, meta

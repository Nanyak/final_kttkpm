"""
Train NextItemBiLSTM and persist weights + preprocessor to disk.
"""
import json
import pickle
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .model import NextItemBiLSTM
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
    dropout: float = 0.3,
    verbose: bool = True,
):
    """
    Train on a list of (user_id, product_id) tuples ordered by timestamp.
    Saves bilstm.pt, preprocessor.pkl, meta.json to model_dir.
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
        batch_size=batch_size,
        shuffle=True,
    )

    model = NextItemBiLSTM(
        vocab_size=proc.vocab_size,
        embed_dim=embed_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)

    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(ignore_index=0)

    model.train()
    history = []
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimiser.zero_grad()
            loss = criterion(model(X_batch), y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimiser.step()
            total_loss += loss.item()
        avg = total_loss / len(dataloader)
        history.append(avg)
        if verbose:
            print(f'[BiLSTM] Epoch {epoch:>3}/{epochs}  loss={avg:.4f}')

    torch.save(model.state_dict(), model_dir / 'bilstm.pt')
    with open(model_dir / 'preprocessor.pkl', 'wb') as f:
        pickle.dump(proc, f)
    meta = {
        'model_type': 'bilstm',
        'vocab_size': proc.vocab_size,
        'embed_dim': embed_dim,
        'hidden_dim': hidden_dim,
        'num_layers': num_layers,
        'dropout': dropout,
        'seq_len': seq_len,
        'final_loss': round(history[-1], 6) if history else None,
    }
    with open(model_dir / 'meta.json', 'w') as f:
        json.dump(meta, f, indent=2)

    if verbose:
        print(f'[BiLSTM] Saved to {model_dir}')
    return model, proc, meta


def load(model_dir: Path):
    """Load trained BiLSTM + preprocessor from disk."""
    with open(model_dir / 'meta.json') as f:
        meta = json.load(f)
    with open(model_dir / 'preprocessor.pkl', 'rb') as f:
        proc = pickle.load(f)
    model = NextItemBiLSTM(
        vocab_size=meta['vocab_size'],
        embed_dim=meta['embed_dim'],
        hidden_dim=meta['hidden_dim'],
        num_layers=meta['num_layers'],
        dropout=meta['dropout'],
    )
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.load_state_dict(torch.load(model_dir / 'bilstm.pt', map_location=device))
    model.eval()
    return model.to(device), proc, meta

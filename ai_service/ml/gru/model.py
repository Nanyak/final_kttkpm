import torch
import torch.nn as nn


class NextItemGRU(nn.Module):
    """
    GRU next-item sequence model.

    GRU uses two gates (reset + update) instead of LSTM's three, making
    it faster to train with comparable accuracy on shorter sequences.

    Architecture:
        Embedding -> GRU (stacked) -> Dropout -> Linear
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size + 1, embed_dim, padding_idx=0)
        self.gru = nn.GRU(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, vocab_size + 1)

    def forward(self, x):
        # x: (batch, seq_len)
        emb = self.embedding(x)            # (batch, seq_len, embed_dim)
        out, _ = self.gru(emb)             # (batch, seq_len, hidden_dim)
        out = self.dropout(out[:, -1, :])  # last timestep
        return self.fc(out)                # (batch, vocab_size+1)

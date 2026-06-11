import torch
import torch.nn as nn


class NextItemBiLSTM(nn.Module):
    """
    Bidirectional LSTM next-item sequence model.

    Architecture:
        Embedding -> BiLSTM (stacked) -> Dropout -> Linear

    The forward pass reads the sequence left-to-right; the backward pass
    reads right-to-left.  Both directions' final hidden states are
    concatenated, giving the FC layer a richer context representation.

    fc input size = hidden_dim * 2  (forward + backward)
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
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, vocab_size + 1)

    def forward(self, x):
        # x: (batch, seq_len)
        emb = self.embedding(x)            # (batch, seq_len, embed_dim)
        out, _ = self.lstm(emb)            # (batch, seq_len, hidden_dim*2)
        out = self.dropout(out[:, -1, :])  # last timestep  (forward+backward)
        return self.fc(out)                # (batch, vocab_size+1)

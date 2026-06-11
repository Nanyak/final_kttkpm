import torch
import torch.nn as nn


class NextItemRNN(nn.Module):
    """
    Vanilla RNN next-item sequence model.

    Architecture:
        Embedding -> RNN (stacked, tanh) -> Dropout -> Linear

    Note: RNNs are prone to vanishing gradients on long sequences.
    They train faster than LSTM/BiLSTM but typically score lower on
    accuracy for sequences longer than ~10 steps.
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
        self.rnn = nn.RNN(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            nonlinearity='tanh',
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, vocab_size + 1)

    def forward(self, x):
        # x: (batch, seq_len)
        emb = self.embedding(x)            # (batch, seq_len, embed_dim)
        out, _ = self.rnn(emb)             # (batch, seq_len, hidden_dim)
        out = self.dropout(out[:, -1, :])  # last timestep
        return self.fc(out)                # (batch, vocab_size+1)

import torch
import torch.nn as nn
import torch.nn.functional as F


class NextItemNARM(nn.Module):
    """
    NARM — Neural Attentive Recommendation Machine.

    Paper: Li et al., "Neural Attentive Session-based Recommendation" (CIKM 2017).

    Architecture:
        Embedding
          -> GRU encoder  (captures sequential transitions)
          -> Local attention gate  (weights each hidden state by its
             relevance to the final hidden state)
          -> Concat(global_repr, local_repr)
          -> Linear

    The attention mechanism lets the model focus on the subset of items
    most relevant to the current intent, rather than relying solely on
    the last hidden state.
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 1,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.hidden_dim = hidden_dim

        self.embedding  = nn.Embedding(vocab_size + 1, embed_dim, padding_idx=0)
        self.emb_dropout = nn.Dropout(dropout)

        self.gru = nn.GRU(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )

        # Attention: computes a score for each step given the final hidden state
        self.attn_w = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.attn_v = nn.Linear(hidden_dim, 1,          bias=False)

        self.dropout = nn.Dropout(dropout)
        # Concatenation of global (last) + local (attention-weighted) repr
        self.fc = nn.Linear(hidden_dim * 2, vocab_size + 1)

    def forward(self, x):
        # x: (batch, seq_len)
        mask = x.ne(0)                                          # (batch, seq_len)

        emb = self.emb_dropout(self.embedding(x))               # (batch, seq, embed)
        h_all, h_last = self.gru(emb)                           # h_all: (B, T, H)
        h_last = h_last[-1]                                     # (batch, hidden_dim)

        # ── local attention ───────────────────────────────────
        # score_t = v^T * tanh(W * h_t + W * h_last)
        h_last_exp = h_last.unsqueeze(1).expand_as(h_all)      # (B, T, H)
        scores = self.attn_v(
            torch.tanh(self.attn_w(h_all) + self.attn_w(h_last_exp))
        ).squeeze(-1)                                           # (B, T)

        # mask padding positions before softmax
        scores = scores.masked_fill(~mask, float('-inf'))
        alpha  = torch.softmax(scores, dim=1).unsqueeze(-1)    # (B, T, 1)
        local  = (alpha * h_all).sum(dim=1)                    # (B, H)

        # ── combine & project ─────────────────────────────────
        combined = self.dropout(torch.cat([h_last, local], dim=1))  # (B, 2H)
        return self.fc(combined)                                     # (B, vocab+1)

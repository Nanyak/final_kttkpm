import torch
import torch.nn as nn
import math


class PointWiseFeedForward(nn.Module):
    """Position-wise two-layer FFN used inside each SASRec block."""

    def __init__(self, d_model: int, d_ff: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class SASRecBlock(nn.Module):
    """One transformer block: causal self-attention + FFN, each with residual + LayerNorm."""

    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float):
        super().__init__()
        self.attn   = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ffn    = PointWiseFeedForward(d_model, d_ff, dropout)
        self.norm1  = nn.LayerNorm(d_model)
        self.norm2  = nn.LayerNorm(d_model)
        self.drop   = nn.Dropout(dropout)

    def forward(self, x, attn_mask, key_padding_mask):
        # Pre-LN variant for stability
        residual = x
        x, _ = self.attn(
            self.norm1(x), self.norm1(x), self.norm1(x),
            attn_mask=attn_mask,
            key_padding_mask=key_padding_mask,
        )
        x = self.drop(x) + residual

        residual = x
        x = self.ffn(self.norm2(x)) + residual
        return x


class NextItemSASRec(nn.Module):
    """
    SASRec — Self-Attentive Sequential Recommendation.

    Paper: Kang & McAuley, "Self-Attentive Sequential Recommendation" (ICDM 2018).

    Architecture:
        Embedding + positional embedding
          -> N x (Causal Multi-Head Self-Attention + FFN)
          -> LayerNorm -> Dropout -> Linear

    Uses a causal (auto-regressive) attention mask so position t can
    only attend to positions <= t, making it suitable for next-item
    prediction without any label leakage.
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        n_heads: int = 4,
        max_len: int = 200,
    ):
        super().__init__()
        self.embed_dim = embed_dim

        self.item_emb = nn.Embedding(vocab_size + 1, embed_dim, padding_idx=0)
        self.pos_emb  = nn.Embedding(max_len + 1,    embed_dim)
        self.emb_drop = nn.Dropout(dropout)

        d_ff = hidden_dim * 2
        self.blocks = nn.ModuleList([
            SASRecBlock(embed_dim, n_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.norm    = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc      = nn.Linear(embed_dim, vocab_size + 1)

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, std=0.02)
            elif isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, x):
        # x: (batch, seq_len)  — 0 = padding token
        batch, seq_len = x.shape
        device = x.device

        positions = torch.arange(1, seq_len + 1, device=device).unsqueeze(0)  # (1, T)
        positions = positions.clamp(max=self.pos_emb.num_embeddings - 1)

        emb = self.emb_drop(self.item_emb(x) + self.pos_emb(positions))

        # Causal mask: position i cannot attend to j > i
        causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, device=device, dtype=torch.bool), diagonal=1
        )
        # Padding positions are zeroed after attention. Passing them as a
        # key_padding_mask together with a causal mask can leave early
        # left-padded query rows with no valid keys, which yields NaNs.
        key_padding_mask = x.eq(0)

        h = emb
        for block in self.blocks:
            h = block(h, attn_mask=causal_mask, key_padding_mask=None)
            h = h.masked_fill(key_padding_mask.unsqueeze(-1), 0.0)
            h = torch.nan_to_num(h, nan=0.0, posinf=0.0, neginf=0.0)

        h = self.dropout(self.norm(h[:, -1, :]))   # last position
        return self.fc(h)                           # (batch, vocab+1)

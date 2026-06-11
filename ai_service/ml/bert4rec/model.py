import torch
import torch.nn as nn
import math


class BERTEmbeddings(nn.Module):
    """Item + positional embeddings with LayerNorm + Dropout."""

    def __init__(self, vocab_size: int, embed_dim: int, max_len: int, dropout: float):
        super().__init__()
        self.item_emb = nn.Embedding(vocab_size + 2, embed_dim, padding_idx=0)
        # +2: 0=pad, vocab_size+1=[MASK] token
        self.pos_emb  = nn.Embedding(max_len + 1,    embed_dim)
        self.norm     = nn.LayerNorm(embed_dim)
        self.dropout  = nn.Dropout(dropout)

    def forward(self, x):
        batch, seq_len = x.shape
        positions = torch.arange(1, seq_len + 1, device=x.device).unsqueeze(0)
        positions = positions.clamp(max=self.pos_emb.num_embeddings - 1)
        out = self.item_emb(x) + self.pos_emb(positions)
        return self.dropout(self.norm(out))


class BERTBlock(nn.Module):
    """Standard bidirectional transformer block: MHA + FFN with Pre-LN."""

    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float):
        super().__init__()
        self.attn  = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ffn   = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.drop  = nn.Dropout(dropout)

    def forward(self, x, key_padding_mask):
        residual = x
        nx = self.norm1(x)
        x, _ = self.attn(nx, nx, nx, key_padding_mask=key_padding_mask)
        x = self.drop(x) + residual

        residual = x
        x = self.ffn(self.norm2(x)) + residual
        return x


class NextItemBERT4Rec(nn.Module):
    """
    BERT4Rec — Bidirectional Encoder Representations for Sequential Recommendation.

    Paper: Sun et al., "BERT4Rec: Sequential Recommendation with
           Bidirectional Encoder Representations from Transformer" (CIKM 2019).

    Training strategy — Cloze task (masked item modelling):
        A random 20% of input items are replaced with a special [MASK] token.
        The model learns to predict the original item at each masked position.
        This bidirectional context gives richer representations than causal models.

    Inference:
        The last item in the sequence is replaced with [MASK] and the model
        predicts the next item from that position.

    Architecture:
        BERTEmbeddings
          -> N x BERTBlock  (full bidirectional attention)
          -> LayerNorm -> Linear
    """

    MASK_TOKEN_OFFSET = 1   # mask token id = vocab_size + MASK_TOKEN_OFFSET

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        n_heads: int = 4,
        max_len: int = 200,
        mask_prob: float = 0.2,
    ):
        super().__init__()
        self.vocab_size  = vocab_size
        self.mask_token  = vocab_size + self.MASK_TOKEN_OFFSET
        self.mask_prob   = mask_prob

        self.embeddings = BERTEmbeddings(vocab_size, embed_dim, max_len, dropout)
        self.blocks = nn.ModuleList([
            BERTBlock(embed_dim, n_heads, hidden_dim * 2, dropout)
            for _ in range(num_layers)
        ])
        self.norm    = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc      = nn.Linear(embed_dim, vocab_size + 2)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, std=0.02)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def apply_mask(self, x):
        """
        Randomly replace ~mask_prob fraction of non-padding tokens with
        the [MASK] token.  Returns (masked_x, mask_positions).
        Used only during training.
        """
        mask_positions = (
            (torch.rand_like(x, dtype=torch.float) < self.mask_prob) & x.ne(0)
        )
        masked_x = x.clone()
        masked_x[mask_positions] = self.mask_token
        return masked_x, mask_positions

    def forward(self, x):
        # x: (batch, seq_len) — may already contain MASK tokens during training
        key_padding_mask = x.eq(0)   # True = pad, ignore in attention

        h = self.embeddings(x)
        for block in self.blocks:
            h = block(h, key_padding_mask=key_padding_mask)

        h = self.dropout(self.norm(h))
        return self.fc(h)            # (batch, seq_len, vocab+2)

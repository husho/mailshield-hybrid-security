from __future__ import annotations

import torch
import torch.nn as nn


class HybridDeepMailModel(nn.Module):
    """Hybrid deep model: GRU temporal branch + MLP static branch + host embedding."""

    def __init__(
        self,
        seq_input_dim: int,
        static_input_dim: int,
        num_hosts: int,
        num_classes: int = 3,
        gru_hidden: int = 64,
        host_emb_dim: int = 8,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.host_embedding = nn.Embedding(max(num_hosts, 1), host_emb_dim)

        self.gru = nn.GRU(
            input_size=seq_input_dim,
            hidden_size=gru_hidden,
            num_layers=1,
            batch_first=True,
            dropout=0.0,
            bidirectional=False,
        )

        self.static_branch = nn.Sequential(
            nn.Linear(static_input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
        )

        fusion_in = gru_hidden + 32 + host_emb_dim
        self.fusion_head = nn.Sequential(
            nn.Linear(fusion_in, 96),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(96, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, seq_x: torch.Tensor, static_x: torch.Tensor, host_idx: torch.Tensor) -> torch.Tensor:
        _, h_n = self.gru(seq_x)
        temporal_repr = h_n[-1]

        static_repr = self.static_branch(static_x)
        host_repr = self.host_embedding(host_idx)

        fused = torch.cat([temporal_repr, static_repr, host_repr], dim=1)
        return self.fusion_head(fused)

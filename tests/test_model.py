import torch

from hybrid_mailsec.model import HybridDeepMailModel


def test_hybrid_model_forward_shape() -> None:
    model = HybridDeepMailModel(seq_input_dim=9, static_input_dim=16, num_hosts=5, num_classes=3)
    seq_x = torch.randn(4, 8, 9)
    static_x = torch.randn(4, 16)
    host_idx = torch.tensor([0, 1, 2, 3], dtype=torch.int64)

    logits = model(seq_x, static_x, host_idx)
    assert logits.shape == (4, 3)

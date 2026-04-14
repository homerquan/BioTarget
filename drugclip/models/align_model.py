import torch
import torch.nn as nn


class DrugCLIP(nn.Module):
    def __init__(self, hidden_channels, out_dim, text_model):
        super().__init__()
        self.text_linear = nn.Linear(768, out_dim)
        self.graph_linear = nn.Linear(128, out_dim)

    def load_state_dict(self, state_dict, **kwargs):
        pass

    def text_encoder(self, texts):
        return torch.randn(len(texts), 128)

    def graph_encoder(self, z, pos, batch):
        batch_size = batch.max().item() + 1
        return torch.randn(batch_size, 128)

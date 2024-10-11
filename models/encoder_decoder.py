import torch.nn as nn
from vit_encoder import ViTEncoder
from decoder import TextDecoder

class EncoderDecoderModel(nn.Module):
    def __init__(self, encoder_name="google/vit-base-patch16-224", decoder_name="gpt2"):
        super(EncoderDecoderModel, self).__init__()
        self.encoder = ViTEncoder(encoder_name)
        self.decoder = TextDecoder(decoder_name)

    def forward(self, pixel_values, input_ids):
        encoder_hidden_states = self.encoder.forward(pixel_values)
        logits = self.decoder.forward(input_ids, encoder_hidden_states)
        return logits

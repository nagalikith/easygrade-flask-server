from transformers import ViTModel

class ViTEncoder:
    def __init__(self, model_name="google/vit-base-patch16-224"):
        self.model = ViTModel.from_pretrained(model_name)
    
    def forward(self, pixel_values):
        outputs = self.model(pixel_values=pixel_values)
        return outputs.last_hidden_state  # [CLS] token or the full hidden state

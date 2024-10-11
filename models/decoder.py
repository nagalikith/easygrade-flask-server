from transformers import GPT2LMHeadModel

class TextDecoder:
    def __init__(self, model_name="gpt2"):
        self.model = GPT2LMHeadModel.from_pretrained(model_name)

    def forward(self, input_ids, encoder_hidden_states):
        outputs = self.model(input_ids=input_ids, encoder_hidden_states=encoder_hidden_states)
        return outputs.logits

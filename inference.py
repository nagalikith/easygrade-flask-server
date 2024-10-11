import torch
from PIL import Image
from models.encoder_decoder import EncoderDecoderModel
from transformers import TrOCRProcessor
from utils.utils import preprocess_image, decode_text

# Load the model
model = EncoderDecoderModel("google/vit-base-patch16-224", "gpt2")
model.eval()

# Load processor
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")

# Load image
image_path = "path_to_image.jpg"
pixel_values = preprocess_image(image_path, processor)

# Run inference
with torch.no_grad():
    output_ids = model(pixel_values, input_ids=None)

# Decode output text
predicted_text = decode_text(output_ids, processor)
print(predicted_text)

import torch
from torch.utils.data import DataLoader
from models.encoder_decoder import EncoderDecoderModel
from data.dataset import ImageTextDataset
from transformers import TrOCRProcessor

# Load configurations
import yaml
with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Load data
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
train_dataset = ImageTextDataset(image_paths=config['paths']['train_data'], captions=..., processor=processor)
train_loader = DataLoader(train_dataset, batch_size=config['training']['batch_size'], shuffle=True)

# Initialize model
model = EncoderDecoderModel(config['model']['encoder'], config['model']['decoder'])
optimizer = torch.optim.Adam(model.parameters(), lr=config['training']['learning_rate'])

# Training loop
for epoch in range(config['training']['epochs']):
    model.train()
    for batch in train_loader:
        pixel_values, input_ids = batch
        outputs = model(pixel_values, input_ids)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    print(f"Epoch {epoch+1}/{config['training']['epochs']} - Loss: {loss.item()}")

from torch.utils.data import Dataset
from PIL import Image
from transformers import TrOCRProcessor

class ImageTextDataset(Dataset):
    def __init__(self, image_paths, captions, processor):
        self.image_paths = image_paths
        self.captions = captions
        self.processor = processor

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        image = Image.open(self.image_paths[idx]).convert("RGB")
        caption = self.captions[idx]

        # Preprocess the image and text using processor
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
        inputs = self.processor(text=caption, return_tensors="pt", padding=True).input_ids

        return pixel_values.squeeze(), inputs.squeeze()

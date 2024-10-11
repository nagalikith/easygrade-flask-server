from PIL import Image
from .env_manager import get_env_val
from .import_helper import libs, handle_login

# Export commonly used utilities
__all__ = ['get_env_val', 'libs', 'handle_login']
def preprocess_image(image_path, processor):
    image = Image.open(image_path).convert("RGB")
    return processor(images=image, return_tensors="pt").pixel_values

def decode_text(outputs, processor):
    return processor.decode(outputs, skip_special_tokens=True)

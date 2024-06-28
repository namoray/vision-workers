from PIL import Image
import base64
import io


def base64_to_image(base64_str: str) -> Image.Image:
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    return image


def pil_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

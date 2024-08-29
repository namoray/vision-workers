from typing import Optional
from pydantic import BaseModel
import base64
import random
from io import BytesIO

import aiohttp
import diskcache
from PIL import Image
import uuid
from typing import List, Tuple
import io
import numpy as np
import cv2


def pil_to_base64(image: Image, format: str = "JPEG") -> str:
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def model_to_printable_dict(model: Optional[BaseModel], max_length: int = 50) -> dict:
    """
    Convert a model to a dictionary, truncating long string values and string representation of lists.
    Helper function to print synapses & stuff with image b64's in them

    Parameters:
    max_length (int): The maximum length allowed for string fields. Default is 30.

    Returns:
    dict: The model as a dictionary with truncated values.
    """

    if model is None:
        return None

    def truncate_value(value):
        if isinstance(value, str) and len(value) > max_length:
            return value[:max_length] + "..."
        elif isinstance(value, list):
            str_value = str(value)
            if len(str_value) >= max_length:
                return str(value)[:max_length] + "..."
            else:
                return str_value
        elif isinstance(value, dict):
            return {k: truncate_value(v) for k, v in value.items()}
        else:
            return value


async def get_random_picsum_image(x_dim: int, y_dim: int) -> str:
    """
    Generate a random image with the specified dimensions, by calling unsplash api.

    Args:
        x_dim (int): The width of the image.
        y_dim (int): The height of the image.

    Returns:
        str: The base64 encoded representation of the generated image.
    """
    async with aiohttp.ClientSession() as session:
        url = f"https://picsum.photos/{x_dim}/{y_dim}"
        async with session.get(url) as resp:
            data = await resp.read()

    img = Image.open(BytesIO(data))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    return img_b64


async def get_random_image_b64(cache: diskcache.Cache) -> str:
    for key in cache.iterkeys():
        image_b64: str = cache.get(key, None)
        if image_b64 is None:
            cache.delete(key)
            continue

        if random.random() < 0.01:
            cache.delete(key)
        return image_b64

    random_picsum_image = await get_random_picsum_image(1024, 1024)
    cache.add(key=str(uuid.uuid4()), value=random_picsum_image)
    return random_picsum_image


def get_randomly_edited_face_picture_for_avatar() -> str:
    """
    For avatar we need a face image.

    We must satisfy the criteria: image must not be cacheable

    As long as we satisfy that, we're good - since we score organic queries.

    Hence, we can use a single picture and just edit it to generate 2**(1204*1024) unique images
    """
    image = Image.open("app/assets/avatar_image.png")

    # Load the image data
    pixels = image.load()

    width, height = image.size

    for x in range(width):
        for y in range(height):
            if random.random() < 0.9:
                current_value = pixels[x, y]
                if image.mode == "RGB":
                    r, g, b = current_value
                    r = min(r + 1, 255)
                    g = min(g + 1, 255)
                    b = min(b + 1, 255)
                    pixels[x, y] = (r, g, b)
                elif image.mode == "L":
                    new_value = min(current_value + 1, 255)
                    pixels[x, y] = new_value

    return pil_to_base64(image)


def generate_mask_with_circle(image_b64: str) -> np.ndarray:
    imgdata = base64.b64decode(image_b64)
    image = Image.open(BytesIO(imgdata))
    image_np = np.array(image)

    image_shape = image_np.shape[:2]

    center_x = np.random.randint(0, image_shape[1])
    center_y = np.random.randint(0, image_shape[0])
    center = (center_x, center_y)

    mask = np.zeros(image_shape, np.uint8)

    radius = random.randint(20, 100)

    cv2.circle(mask, center, radius, (1), 1)

    mask = cv2.floodFill(mask, None, center, 1)[1]
    mask_img = Image.fromarray(mask, "L")
    buffered = BytesIO()
    mask_img.save(buffered, format="PNG")
    mask_img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return mask_img_str


def resize_image(image_b64: str) -> str:
    image_data = base64.b64decode(image_b64)
    image = Image.open(BytesIO(image_data))

    best_size = find_closest_allowed_size(image)
    resized_image = image.resize(best_size, Image.Resampling.BICUBIC)

    byte_arr = BytesIO()
    resized_image.save(byte_arr, format="PNG")
    encoded_resized_image = base64.b64encode(byte_arr.getvalue()).decode("utf-8")
    return encoded_resized_image


ALLOWED_IMAGE_SIZES: List[Tuple[int, int]] = [
    (1024, 1024),
    (1152, 896),
    (1216, 832),
    (1344, 768),
    (1536, 640),
    (640, 1536),
    (768, 1344),
    (832, 1216),
    (896, 1152),
]


def find_closest_allowed_size(image) -> Tuple[int, int]:
    width, height = image.size
    min_diff: float = float("inf")
    best_size: Tuple[int, int] = None
    for size in ALLOWED_IMAGE_SIZES:
        diff = abs(width - size[0]) + abs(height - size[1])
        if diff < min_diff:
            min_diff = diff
            best_size = size
    return best_size

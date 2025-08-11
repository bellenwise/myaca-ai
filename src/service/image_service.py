import io
from openai import OpenAI
import base64
from fastapi.responses import Response

from src.model.image_model import ImageGenerationRequest

client = OpenAI()


def generate_image(image_request: ImageGenerationRequest) -> Response:
    image_prompt = (f"Generate an image that will be used as a landing page description image."
                    f"The image style is {image_request.style}, "
                    f"The image should not include the prompt text, instead have a visual representation."
                    f"the prompt is: {image_request.title} : {image_request.description}")

    result = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        quality="low",
        size="1024x1024",
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    return Response(image_bytes, media_type="image/png")

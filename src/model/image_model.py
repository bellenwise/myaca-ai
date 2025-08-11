from pydantic import BaseModel

class ImageGenerationRequest(BaseModel):
    title: str
    description: str
    style: str
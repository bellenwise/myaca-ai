from pydantic import BaseModel


class ImageProcessRequest(BaseModel):
    acaId: str
    assignmentUuid: str
    problemId: str
    imageURL: str


class ImageGenerationRequest(BaseModel):
    title: str
    description: str
    style: str
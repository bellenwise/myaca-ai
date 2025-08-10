from pydantic import BaseModel


class LandingPageRequest(BaseModel):
    """
    Model for the landing page request.
    """
    title: str
    description: str
    image_url: str
from pydantic import BaseModel


class LandingPageRequest(BaseModel):
    """
    Model for the landing page request.

    Args :
        - title : str
        - description : str
        - image_url : str
    """
    title: str
    description: str
    image_url: str
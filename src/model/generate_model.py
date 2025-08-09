from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """
    aca_id : project subdomain
    problemID : problem identifier
    """
    acaID : str
    problemID : str



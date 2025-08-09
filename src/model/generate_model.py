from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """
    aca_id : project subdomain
    problemID : problem identifier
    """
    acaId : str
    problemId : str



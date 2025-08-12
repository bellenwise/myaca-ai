from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """
    비슷한 문제 생성

    Args :
        - aca_id : str
        - problemID : str
    """
    acaId : str
    problemId : str



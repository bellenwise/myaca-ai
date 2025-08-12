from dataclasses import dataclass


@dataclass
class TextResponse:
    """
    Args :
        - ok : bool
        - text: str
    """
    ok: bool
    text: str
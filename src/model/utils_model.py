from dataclasses import dataclass


@dataclass
class TextResponse:
    ok: bool
    text: str
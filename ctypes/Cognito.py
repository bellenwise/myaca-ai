import dataclasses
from typing import List, Optional

@dataclasses.dataclass
class CognitoClaims:
    sub: Optional[str] = None
    profile: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    cognito_username: Optional[str] = None
    cognito_groups: Optional[List[str]] = dataclasses.field(default_factory=list)
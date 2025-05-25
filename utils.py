from typing import Optional
from pydantic import BaseModel


class EvaluateContext(BaseModel):
    instruction: Optional[str] = None
    knowledge: list[str] = []
